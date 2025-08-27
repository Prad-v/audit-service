"""
Security utilities for the audit log framework.

This module provides JWT token handling, password hashing,
and other security-related utilities.
"""

import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union

import jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import structlog

from app.config import get_settings
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.auth import JWTPayload, UserRole, Permission, get_permissions_for_roles

logger = structlog.get_logger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Security manager for authentication and authorization."""
    
    def __init__(self):
        self.settings = settings.security
        self.algorithm = self.settings.jwt_algorithm
        self.secret_key = self.settings.secret_key
        self.access_token_expire_minutes = self.settings.access_token_expire_minutes
        self.refresh_token_expire_days = self.settings.refresh_token_expire_days
    
    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, plain_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash."""
        return hashlib.sha256(plain_key.encode()).hexdigest() == hashed_key
    
    def create_access_token(
        self,
        user_id: str,
        username: str,
        tenant_id: str,
        roles: list[UserRole],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        # Get permissions for roles
        permissions = get_permissions_for_roles(roles)
        
        payload = JWTPayload(
            sub=user_id,
            tenant_id=tenant_id,
            username=username,
            roles=roles,
            permissions=permissions,
            exp=int(expire.timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti=secrets.token_urlsafe(16),
        )
        
        try:
            token = jwt.encode(
                payload.dict(),
                self.secret_key,
                algorithm=self.algorithm
            )
            logger.info("Access token created", user_id=user_id, tenant_id=tenant_id)
            return token
        except Exception as e:
            logger.error("Failed to create access token", error=str(e))
            raise AuthenticationError("Failed to create access token")
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT refresh token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.refresh_token_expire_days
            )
        
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "type": "refresh",
            "exp": int(expire.timestamp()),
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": secrets.token_urlsafe(16),
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info("Refresh token created", user_id=user_id, tenant_id=tenant_id)
            return token
        except Exception as e:
            logger.error("Failed to create refresh token", error=str(e))
            raise AuthenticationError("Failed to create refresh token")
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token", error=str(e))
            raise AuthenticationError("Invalid token")
    
    def verify_access_token(self, token: str) -> JWTPayload:
        """Verify an access token and return the payload."""
        payload = self.verify_token(token)
        
        # Ensure it's not a refresh token
        if payload.get("type") == "refresh":
            raise AuthenticationError("Invalid token type")
        
        try:
            return JWTPayload(**payload)
        except Exception as e:
            logger.error("Invalid token payload", error=str(e))
            raise AuthenticationError("Invalid token payload")
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify a refresh token and return the payload."""
        payload = self.verify_token(token)
        
        # Ensure it's a refresh token
        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")
        
        return payload
    
    def check_permission(
        self,
        user_permissions: list[Permission],
        required_permission: Permission,
    ) -> bool:
        """Check if user has the required permission."""
        return required_permission in user_permissions
    
    def check_role(
        self,
        user_roles: list[UserRole],
        required_role: UserRole,
    ) -> bool:
        """Check if user has the required role."""
        return required_role in user_roles
    
    def check_tenant_access(
        self,
        user_tenant_id: str,
        resource_tenant_id: str,
        user_roles: list[UserRole],
    ) -> bool:
        """Check if user can access resources from the specified tenant."""
        # System admins can access all tenants
        if UserRole.SYSTEM_ADMIN in user_roles:
            return True
        
        # Users can only access their own tenant
        return user_tenant_id == resource_tenant_id
    
    def require_permission(
        self,
        user_permissions: list[Permission],
        required_permission: Permission,
    ) -> None:
        """Require a specific permission, raise exception if not present."""
        if not self.check_permission(user_permissions, required_permission):
            logger.warning(
                "Permission denied",
                required_permission=required_permission,
                user_permissions=user_permissions,
            )
            raise AuthorizationError(f"Permission '{required_permission}' required")
    
    def require_role(
        self,
        user_roles: list[UserRole],
        required_role: UserRole,
    ) -> None:
        """Require a specific role, raise exception if not present."""
        if not self.check_role(user_roles, required_role):
            logger.warning(
                "Role access denied",
                required_role=required_role,
                user_roles=user_roles,
            )
            raise AuthorizationError(f"Role '{required_role}' required")
    
    def require_tenant_access(
        self,
        user_tenant_id: str,
        resource_tenant_id: str,
        user_roles: list[UserRole],
    ) -> None:
        """Require tenant access, raise exception if not allowed."""
        if not self.check_tenant_access(user_tenant_id, resource_tenant_id, user_roles):
            logger.warning(
                "Tenant access denied",
                user_tenant_id=user_tenant_id,
                resource_tenant_id=resource_tenant_id,
            )
            raise AuthorizationError("Access to tenant resources denied")


# Global security manager instance
security_manager = SecurityManager()


def get_security_manager() -> SecurityManager:
    """Get the global security manager instance."""
    return security_manager


def hash_password(password: str) -> str:
    """Hash a password."""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password."""
    return security_manager.verify_password(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    username: str,
    tenant_id: str,
    roles: list[UserRole],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create an access token."""
    return security_manager.create_access_token(
        user_id, username, tenant_id, roles, expires_delta
    )


def create_refresh_token(
    user_id: str,
    tenant_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a refresh token."""
    return security_manager.create_refresh_token(user_id, tenant_id, expires_delta)


def verify_access_token(token: str) -> JWTPayload:
    """Verify an access token."""
    return security_manager.verify_access_token(token)


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """Verify a refresh token."""
    return security_manager.verify_refresh_token(token)


def generate_api_key() -> str:
    """Generate a new API key."""
    return security_manager.generate_api_key()


def hash_api_key(api_key: str) -> str:
    """Hash an API key."""
    return security_manager.hash_api_key(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """Verify an API key."""
    return security_manager.verify_api_key(plain_key, hashed_key)