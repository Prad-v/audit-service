"""
Authentication API endpoints for the audit log framework.

This module provides endpoints for user authentication, token management,
and user-related operations with multi-tenant support.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
import structlog

from app.api.middleware import (
    get_current_user,
    require_permission,
    require_role,
    require_tenant_admin,
)
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.models.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserCreate,
    UserUpdate,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse,
    Permission,
    UserRole,
)
from app.services.auth_service import get_auth_service

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate a user and return access and refresh tokens.
    
    This endpoint authenticates a user with username/password and returns
    JWT tokens for subsequent API access.
    """
    try:
        auth_service = get_auth_service()
        user, tokens = await auth_service.authenticate_user(login_data)
        
        logger.info(
            "User login successful",
            user_id=user.id,
            username=user.username,
            tenant_id=user.tenant_id,
        )
        
        return tokens
        
    except AuthenticationError as e:
        logger.warning("Login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Login error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """
    Refresh an access token using a refresh token.
    
    This endpoint allows clients to obtain a new access token
    using a valid refresh token.
    """
    try:
        auth_service = get_auth_service()
        tokens = await auth_service.refresh_access_token(refresh_data)
        
        logger.info("Token refresh successful")
        return tokens
        
    except AuthenticationError as e:
        logger.warning("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Token refresh error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(request: Request):
    """
    Get information about the currently authenticated user.
    
    This endpoint returns the profile information of the
    currently authenticated user.
    """
    try:
        user_id, tenant_id, roles, permissions = get_current_user(request)
        
        auth_service = get_auth_service()
        user = await auth_service.get_user(user_id, tenant_id)
        
        return user
        
    except (AuthenticationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Get current user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information",
        )


@router.post("/users", response_model=UserResponse)
@require_tenant_admin()
async def create_user(request: Request, user_data: UserCreate):
    """
    Create a new user in the tenant.
    
    This endpoint allows tenant administrators to create new users
    within their tenant with specified roles and permissions.
    """
    try:
        creator_id, tenant_id, _, _ = get_current_user(request)
        
        auth_service = get_auth_service()
        user = await auth_service.create_user(
            user_data=user_data,
            tenant_id=tenant_id,
            created_by=creator_id,
        )
        
        logger.info(
            "User created",
            user_id=user.id,
            username=user.username,
            tenant_id=tenant_id,
            created_by=creator_id,
        )
        
        return user
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Create user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.get("/users/{user_id}", response_model=UserResponse)
@require_permission(Permission.MANAGE_USERS)
async def get_user(request: Request, user_id: str):
    """
    Get a user by ID within the current tenant.
    
    This endpoint allows authorized users to retrieve information
    about other users within their tenant.
    """
    try:
        _, tenant_id, _, _ = get_current_user(request)
        
        auth_service = get_auth_service()
        user = await auth_service.get_user(user_id, tenant_id)
        
        return user
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Get user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )


@router.put("/users/{user_id}", response_model=UserResponse)
@require_permission(Permission.MANAGE_USERS)
async def update_user(request: Request, user_id: str, user_data: UserUpdate):
    """
    Update a user's information.
    
    This endpoint allows authorized users to update user information
    within their tenant.
    """
    try:
        updater_id, tenant_id, _, _ = get_current_user(request)
        
        auth_service = get_auth_service()
        user = await auth_service.update_user(
            user_id=user_id,
            tenant_id=tenant_id,
            user_data=user_data,
            updated_by=updater_id,
        )
        
        logger.info(
            "User updated",
            user_id=user_id,
            tenant_id=tenant_id,
            updated_by=updater_id,
        )
        
        return user
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Update user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete("/users/{user_id}", response_model=UserResponse)
@require_tenant_admin()
async def deactivate_user(request: Request, user_id: str):
    """
    Deactivate a user account.
    
    This endpoint allows tenant administrators to deactivate user accounts
    within their tenant. Users are not deleted but marked as inactive.
    """
    try:
        deactivator_id, tenant_id, _, _ = get_current_user(request)
        
        auth_service = get_auth_service()
        user = await auth_service.deactivate_user(
            user_id=user_id,
            tenant_id=tenant_id,
            deactivated_by=deactivator_id,
        )
        
        logger.info(
            "User deactivated",
            user_id=user_id,
            tenant_id=tenant_id,
            deactivated_by=deactivator_id,
        )
        
        return user
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Deactivate user error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user",
        )


@router.post("/api-keys", response_model=APIKeyResponse)
@require_permission(Permission.MANAGE_USERS)
async def create_api_key(request: Request, api_key_data: APIKeyCreate):
    """
    Create a new API key for the current user.
    
    This endpoint allows users to create API keys for programmatic access
    to the audit log system.
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        auth_service = get_auth_service()
        api_key = await auth_service.create_api_key(
            api_key_data=api_key_data,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        
        logger.info(
            "API key created",
            api_key_id=api_key.id,
            user_id=user_id,
            tenant_id=tenant_id,
            name=api_key.name,
        )
        
        return api_key
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Create API key error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key",
        )


@router.post("/logout")
async def logout(request: Request):
    """
    Logout the current user.
    
    This endpoint provides a logout mechanism. In a stateless JWT system,
    this mainly serves as a client-side indication to discard tokens.
    For enhanced security, token blacklisting could be implemented.
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        logger.info(
            "User logout",
            user_id=user_id,
            tenant_id=tenant_id,
        )
        
        return {"message": "Logout successful"}
        
    except Exception as e:
        logger.error("Logout error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )