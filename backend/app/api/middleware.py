"""
API middleware for the audit log framework.

This module provides middleware for authentication, authorization,
tenant isolation, and request/response processing.
"""

import time
from typing import Optional, Tuple
from uuid import uuid4

import structlog
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
)
from app.core.security import verify_access_token
from app.models.auth import JWTPayload, UserRole, Permission
from app.services.auth_service import get_auth_service

logger = structlog.get_logger(__name__)

# Security scheme for OpenAPI documentation
security_scheme = HTTPBearer(auto_error=False)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for handling authentication and tenant isolation."""
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/health",
    }
    
    # Paths that require authentication but have custom handling
    AUTH_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process the request through authentication middleware."""
        # Add correlation ID for request tracking
        correlation_id = str(uuid4())
        request.state.correlation_id = correlation_id
        
        # Add structured logging context
        logger.bind(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )
        
        start_time = time.time()
        
        try:
            # Skip authentication for public paths
            if request.url.path in self.PUBLIC_PATHS:
                response = await call_next(request)
                return self._add_response_headers(response, correlation_id, start_time)
            
            # Skip authentication middleware for auth endpoints (they handle it internally)
            if request.url.path in self.AUTH_PATHS:
                response = await call_next(request)
                return self._add_response_headers(response, correlation_id, start_time)
            
            # Authenticate the request
            await self._authenticate_request(request)
            
            # Process the request
            response = await call_next(request)
            
            return self._add_response_headers(response, correlation_id, start_time)
            
        except AuthenticationError as e:
            logger.warning("Authentication failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except AuthorizationError as e:
            logger.warning("Authorization failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )
        except ValidationError as e:
            logger.warning("Validation failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            logger.error("Unexpected error in authentication middleware", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
    
    async def _authenticate_request(self, request: Request) -> None:
        """Authenticate the request using JWT token or API key."""
        # Try JWT token authentication first
        token = self._extract_bearer_token(request)
        if token:
            await self._authenticate_jwt_token(request, token)
            return
        
        # Try API key authentication
        api_key = self._extract_api_key(request)
        if api_key:
            await self._authenticate_api_key(request, api_key)
            return
        
        # No authentication provided
        raise AuthenticationError("Authentication required")
    
    def _extract_bearer_token(self, request: Request) -> Optional[str]:
        """Extract Bearer token from Authorization header."""
        authorization = request.headers.get("Authorization")
        if not authorization:
            return None
        
        if not authorization.startswith("Bearer "):
            return None
        
        return authorization[7:]  # Remove "Bearer " prefix
    
    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from X-API-Key header."""
        return request.headers.get("X-API-Key")
    
    async def _authenticate_jwt_token(self, request: Request, token: str) -> None:
        """Authenticate using JWT token."""
        try:
            # Verify and decode the token
            payload = verify_access_token(token)
            
            # Store authentication info in request state
            request.state.auth_type = "jwt"
            request.state.user_id = payload.sub
            request.state.username = payload.username
            request.state.tenant_id = payload.tenant_id
            request.state.roles = payload.roles
            request.state.permissions = payload.permissions
            
            logger.info(
                "JWT authentication successful",
                user_id=payload.sub,
                username=payload.username,
                tenant_id=payload.tenant_id,
                roles=[role.value for role in payload.roles],
            )
            
        except Exception as e:
            logger.warning("JWT authentication failed", error=str(e))
            raise AuthenticationError("Invalid or expired token")
    
    async def _authenticate_api_key(self, request: Request, api_key: str) -> None:
        """Authenticate using API key."""
        try:
            # Extract tenant ID from request (could be in header, query param, or path)
            tenant_id = self._extract_tenant_id(request)
            if not tenant_id:
                raise AuthenticationError("Tenant ID required for API key authentication")
            
            # Authenticate API key
            auth_service = get_auth_service()
            user_id, permissions = await auth_service.authenticate_api_key(api_key, tenant_id)
            
            # Store authentication info in request state
            request.state.auth_type = "api_key"
            request.state.user_id = user_id
            request.state.username = None  # API keys don't have usernames
            request.state.tenant_id = tenant_id
            request.state.roles = []  # API keys use permissions directly
            request.state.permissions = [Permission(p) for p in permissions]
            
            logger.info(
                "API key authentication successful",
                user_id=user_id,
                tenant_id=tenant_id,
                permissions=permissions,
            )
            
        except Exception as e:
            logger.warning("API key authentication failed", error=str(e))
            raise AuthenticationError("Invalid API key")
    
    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request headers, query params, or path."""
        # Try X-Tenant-ID header first
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # Try query parameter
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id
        
        # Try to extract from path (e.g., /api/v1/tenants/{tenant_id}/...)
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 5 and path_parts[3] == "tenants":
            return path_parts[4]
        
        return None
    
    def _add_response_headers(
        self, response: Response, correlation_id: str, start_time: float
    ) -> Response:
        """Add common response headers."""
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"
        return response


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing tenant isolation."""
    
    async def dispatch(self, request: Request, call_next):
        """Enforce tenant isolation for authenticated requests."""
        # Skip for public paths
        if request.url.path in AuthenticationMiddleware.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip for auth paths
        if request.url.path in AuthenticationMiddleware.AUTH_PATHS:
            return await call_next(request)
        
        # Check if request is authenticated
        if not hasattr(request.state, "tenant_id"):
            # Not authenticated, let authentication middleware handle it
            return await call_next(request)
        
        # Validate tenant access for the requested resource
        await self._validate_tenant_access(request)
        
        return await call_next(request)
    
    async def _validate_tenant_access(self, request: Request) -> None:
        """Validate that the user can access the requested tenant resources."""
        user_tenant_id = request.state.tenant_id
        user_roles = getattr(request.state, "roles", [])
        
        # Extract target tenant ID from the request
        target_tenant_id = self._extract_target_tenant_id(request)
        
        # If no target tenant specified, use user's tenant
        if not target_tenant_id:
            return
        
        # System admins can access all tenants
        if UserRole.SYSTEM_ADMIN in user_roles:
            return
        
        # Users can only access their own tenant
        if user_tenant_id != target_tenant_id:
            logger.warning(
                "Tenant access denied",
                user_tenant_id=user_tenant_id,
                target_tenant_id=target_tenant_id,
                user_roles=[role.value for role in user_roles],
            )
            raise AuthorizationError("Access to tenant resources denied")
    
    def _extract_target_tenant_id(self, request: Request) -> Optional[str]:
        """Extract the target tenant ID from the request."""
        # Check path parameters (e.g., /api/v1/tenants/{tenant_id}/...)
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 5 and path_parts[3] == "tenants":
            return path_parts[4]
        
        # Check query parameters
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id
        
        # For other endpoints, assume they operate on the user's tenant
        return request.state.tenant_id


def get_current_user(request: Request) -> Tuple[str, str, list[UserRole], list[Permission]]:
    """Get current user information from request state."""
    if not hasattr(request.state, "user_id"):
        raise AuthenticationError("Authentication required")
    
    return (
        request.state.user_id,
        request.state.tenant_id,
        getattr(request.state, "roles", []),
        getattr(request.state, "permissions", []),
    )


def require_permission(permission: Permission):
    """Decorator to require a specific permission."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            _, _, _, permissions = get_current_user(request)
            
            if permission not in permissions:
                logger.warning(
                    "Permission denied",
                    required_permission=permission.value,
                    user_permissions=[p.value for p in permissions],
                )
                raise AuthorizationError(f"Permission '{permission.value}' required")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: UserRole):
    """Decorator to require a specific role."""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            _, _, roles, _ = get_current_user(request)
            
            if role not in roles:
                logger.warning(
                    "Role access denied",
                    required_role=role.value,
                    user_roles=[r.value for r in roles],
                )
                raise AuthorizationError(f"Role '{role.value}' required")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_system_admin():
    """Decorator to require system admin role."""
    return require_role(UserRole.SYSTEM_ADMIN)


def require_tenant_admin():
    """Decorator to require tenant admin role."""
    return require_role(UserRole.TENANT_ADMIN)