"""
Authentication and authorization Pydantic models for the audit log framework.

This module contains models for user authentication, JWT tokens,
and role-based access control.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, validator
from pydantic.types import UUID4


class UserRole(str, Enum):
    """User roles enumeration."""
    AUDIT_READER = "audit_reader"
    AUDIT_WRITER = "audit_writer"
    AUDIT_ADMIN = "audit_admin"
    AUDIT_EXPORT = "audit_export"
    SYSTEM_ADMIN = "system_admin"


class Permission(str, Enum):
    """Permission enumeration."""
    READ_AUDIT = "read:audit"
    WRITE_AUDIT = "write:audit"
    DELETE_AUDIT = "delete:audit"
    EXPORT_AUDIT = "export:audit"
    MANAGE_USERS = "manage:users"
    MANAGE_TENANTS = "manage:tenants"
    MANAGE_SYSTEM = "manage:system"


class BaseAuthModel(BaseModel):
    """Base model for authentication-related data."""
    
    class Config:
        use_enum_values = True
        validate_assignment = True


class UserCreate(BaseAuthModel):
    """Model for creating users."""
    
    username: str = Field(..., description="Username", min_length=3, max_length=255)
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password", min_length=8)
    tenant_id: str = Field(..., description="Tenant ID", max_length=255)
    roles: List[UserRole] = Field(default_factory=list, description="User roles")
    is_active: bool = Field(True, description="Whether user is active")
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format."""
        if not v.replace('_', '').replace('-', '').replace('.', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, hyphens, underscores, and dots")
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
        
        return v


class UserUpdate(BaseAuthModel):
    """Model for updating users."""
    
    email: Optional[EmailStr] = Field(None, description="Email address")
    roles: Optional[List[UserRole]] = Field(None, description="User roles")
    is_active: Optional[bool] = Field(None, description="Whether user is active")


class UserResponse(BaseAuthModel):
    """Model for user responses."""
    
    id: UUID4 = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    tenant_id: str = Field(..., description="Tenant ID")
    roles: List[UserRole] = Field(..., description="User roles")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class LoginRequest(BaseAuthModel):
    """Model for login requests."""
    
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (optional)")


class LoginResponse(BaseAuthModel):
    """Model for login responses."""
    
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")


class RefreshTokenRequest(BaseAuthModel):
    """Model for refresh token requests."""
    
    refresh_token: str = Field(..., description="Refresh token")


class RefreshTokenResponse(BaseAuthModel):
    """Model for refresh token responses."""
    
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class PasswordChangeRequest(BaseAuthModel):
    """Model for password change requests."""
    
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password", min_length=8)
    
    @validator('new_password')
    def validate_new_password(cls, v):
        """Validate new password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit and has_special):
            raise ValueError(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one digit, and one special character"
            )
        
        return v


class TenantCreate(BaseAuthModel):
    """Model for creating tenants."""
    
    id: str = Field(..., description="Tenant ID", max_length=255)
    name: str = Field(..., description="Tenant name", max_length=255)
    description: Optional[str] = Field(None, description="Tenant description")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant settings")
    is_active: bool = Field(True, description="Whether tenant is active")
    
    @validator('id')
    def validate_tenant_id(cls, v):
        """Validate tenant ID format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Tenant ID can only contain letters, numbers, hyphens, and underscores")
        return v.lower()


class TenantUpdate(BaseAuthModel):
    """Model for updating tenants."""
    
    name: Optional[str] = Field(None, description="Tenant name", max_length=255)
    description: Optional[str] = Field(None, description="Tenant description")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")
    is_active: Optional[bool] = Field(None, description="Whether tenant is active")


class TenantResponse(BaseAuthModel):
    """Model for tenant responses."""
    
    id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    description: Optional[str] = Field(None, description="Tenant description")
    settings: Dict[str, Any] = Field(..., description="Tenant settings")
    is_active: bool = Field(..., description="Whether tenant is active")
    created_at: datetime = Field(..., description="Tenant creation timestamp")
    updated_at: datetime = Field(..., description="Tenant last update timestamp")


class APIKeyCreate(BaseAuthModel):
    """Model for creating API keys."""
    
    name: str = Field(..., description="API key name", max_length=255)
    permissions: List[Permission] = Field(..., description="API key permissions")
    expires_at: Optional[datetime] = Field(None, description="API key expiration time")


class APIKeyResponse(BaseAuthModel):
    """Model for API key responses."""
    
    id: UUID4 = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key: Optional[str] = Field(None, description="API key (only shown on creation)")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: UUID4 = Field(..., description="User ID")
    permissions: List[Permission] = Field(..., description="API key permissions")
    is_active: bool = Field(..., description="Whether API key is active")
    expires_at: Optional[datetime] = Field(None, description="API key expiration time")
    last_used: Optional[datetime] = Field(None, description="Last used timestamp")
    created_at: datetime = Field(..., description="API key creation timestamp")
    updated_at: datetime = Field(..., description="API key last update timestamp")


class JWTPayload(BaseAuthModel):
    """Model for JWT token payload."""
    
    sub: str = Field(..., description="Subject (user ID)")
    tenant_id: str = Field(..., description="Tenant ID")
    username: str = Field(..., description="Username")
    roles: List[UserRole] = Field(..., description="User roles")
    permissions: List[Permission] = Field(..., description="User permissions")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    jti: str = Field(..., description="JWT ID")


class CurrentUser(BaseAuthModel):
    """Model for current authenticated user."""
    
    id: UUID4 = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    tenant_id: str = Field(..., description="Tenant ID")
    roles: List[UserRole] = Field(..., description="User roles")
    permissions: List[Permission] = Field(..., description="User permissions")
    is_active: bool = Field(..., description="Whether user is active")


class RolePermissionMapping(BaseAuthModel):
    """Model for role-permission mappings."""
    
    role: UserRole = Field(..., description="User role")
    permissions: List[Permission] = Field(..., description="Permissions for the role")


# Role-permission mappings
ROLE_PERMISSIONS = {
    UserRole.AUDIT_READER: [
        Permission.READ_AUDIT,
    ],
    UserRole.AUDIT_WRITER: [
        Permission.READ_AUDIT,
        Permission.WRITE_AUDIT,
    ],
    UserRole.AUDIT_ADMIN: [
        Permission.READ_AUDIT,
        Permission.WRITE_AUDIT,
        Permission.DELETE_AUDIT,
        Permission.EXPORT_AUDIT,
        Permission.MANAGE_USERS,
    ],
    UserRole.AUDIT_EXPORT: [
        Permission.READ_AUDIT,
        Permission.EXPORT_AUDIT,
    ],
    UserRole.SYSTEM_ADMIN: [
        Permission.READ_AUDIT,
        Permission.WRITE_AUDIT,
        Permission.DELETE_AUDIT,
        Permission.EXPORT_AUDIT,
        Permission.MANAGE_USERS,
        Permission.MANAGE_TENANTS,
        Permission.MANAGE_SYSTEM,
    ],
}


def get_permissions_for_roles(roles: List[UserRole]) -> List[Permission]:
    """Get all permissions for a list of roles."""
    permissions = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, []))
    return list(permissions)