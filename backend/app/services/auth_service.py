"""
Authentication service for the audit log framework.

This service handles user authentication, token management,
and user-related operations with multi-tenant support.
"""

from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import uuid4

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    SecurityManager,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)
from app.db.database import get_database_manager
from app.db.schemas import User, Tenant, APIKey
from app.models.auth import (
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    APIKeyCreate,
    APIKeyResponse,
    UserRole,
)

logger = structlog.get_logger(__name__)


class AuthService:
    """Authentication service for user management and token operations."""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.db_manager = get_database_manager()
    
    async def create_user(
        self,
        user_data: UserCreate,
        tenant_id: str,
        created_by: Optional[str] = None,
    ) -> UserResponse:
        """Create a new user in the specified tenant."""
        async with self.db_manager.get_session() as session:
            # Check if username already exists in tenant
            existing_user = await self._get_user_by_username(
                session, user_data.username, tenant_id
            )
            if existing_user:
                raise ValidationError("Username already exists in this tenant")
            
            # Check if email already exists in tenant
            existing_email = await self._get_user_by_email(
                session, user_data.email, tenant_id
            )
            if existing_email:
                raise ValidationError("Email already exists in this tenant")
            
            # Create user
            user_id = str(uuid4())
            hashed_password = hash_password(user_data.password)
            
            user = User(
                id=user_id,
                tenant_id=tenant_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                password_hash=hashed_password,
                roles=user_data.roles,
                is_active=user_data.is_active,
                created_by=created_by,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            logger.info(
                "User created",
                user_id=user_id,
                username=user_data.username,
                tenant_id=tenant_id,
                created_by=created_by,
            )
            
            return UserResponse.from_orm(user)
    
    async def authenticate_user(
        self, login_data: LoginRequest
    ) -> Tuple[UserResponse, TokenResponse]:
        """Authenticate a user and return user info with tokens."""
        async with self.db_manager.get_session() as session:
            # Get user by username and tenant
            user = await self._get_user_by_username(
                session, login_data.username, login_data.tenant_id
            )
            
            if not user:
                logger.warning(
                    "Authentication failed - user not found",
                    username=login_data.username,
                    tenant_id=login_data.tenant_id,
                )
                raise AuthenticationError("Invalid credentials")
            
            if not user.is_active:
                logger.warning(
                    "Authentication failed - user inactive",
                    user_id=user.id,
                    username=login_data.username,
                )
                raise AuthenticationError("User account is inactive")
            
            # Verify password
            if not verify_password(login_data.password, user.password_hash):
                logger.warning(
                    "Authentication failed - invalid password",
                    user_id=user.id,
                    username=login_data.username,
                )
                raise AuthenticationError("Invalid credentials")
            
            # Update last login
            user.last_login_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            
            # Create tokens
            access_token = create_access_token(
                user_id=user.id,
                username=user.username,
                tenant_id=user.tenant_id,
                roles=user.roles,
            )
            
            refresh_token = create_refresh_token(
                user_id=user.id,
                tenant_id=user.tenant_id,
            )
            
            tokens = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )
            
            logger.info(
                "User authenticated successfully",
                user_id=user.id,
                username=user.username,
                tenant_id=user.tenant_id,
            )
            
            return UserResponse.from_orm(user), tokens
    
    async def refresh_access_token(
        self, refresh_data: RefreshTokenRequest
    ) -> TokenResponse:
        """Refresh an access token using a refresh token."""
        # Verify refresh token
        payload = verify_refresh_token(refresh_data.refresh_token)
        user_id = payload["sub"]
        tenant_id = payload["tenant_id"]
        
        async with self.db_manager.get_session() as session:
            # Get user to ensure they still exist and are active
            user = await self._get_user_by_id(session, user_id)
            
            if not user:
                logger.warning("Refresh failed - user not found", user_id=user_id)
                raise AuthenticationError("Invalid refresh token")
            
            if not user.is_active:
                logger.warning("Refresh failed - user inactive", user_id=user_id)
                raise AuthenticationError("User account is inactive")
            
            if user.tenant_id != tenant_id:
                logger.warning(
                    "Refresh failed - tenant mismatch",
                    user_id=user_id,
                    token_tenant=tenant_id,
                    user_tenant=user.tenant_id,
                )
                raise AuthenticationError("Invalid refresh token")
            
            # Create new access token
            access_token = create_access_token(
                user_id=user.id,
                username=user.username,
                tenant_id=user.tenant_id,
                roles=user.roles,
            )
            
            logger.info(
                "Access token refreshed",
                user_id=user_id,
                tenant_id=tenant_id,
            )
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_data.refresh_token,
                token_type="bearer",
            )
    
    async def get_user(self, user_id: str, tenant_id: str) -> UserResponse:
        """Get a user by ID within a tenant."""
        async with self.db_manager.get_session() as session:
            user = await self._get_user_by_id(session, user_id)
            
            if not user:
                raise NotFoundError("User not found")
            
            if user.tenant_id != tenant_id:
                raise AuthorizationError("Access denied")
            
            return UserResponse.from_orm(user)
    
    async def update_user(
        self,
        user_id: str,
        tenant_id: str,
        user_data: UserUpdate,
        updated_by: Optional[str] = None,
    ) -> UserResponse:
        """Update a user's information."""
        async with self.db_manager.get_session() as session:
            user = await self._get_user_by_id(session, user_id)
            
            if not user:
                raise NotFoundError("User not found")
            
            if user.tenant_id != tenant_id:
                raise AuthorizationError("Access denied")
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            
            if "password" in update_data:
                update_data["password_hash"] = hash_password(update_data.pop("password"))
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_by = updated_by
            user.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(
                "User updated",
                user_id=user_id,
                tenant_id=tenant_id,
                updated_by=updated_by,
            )
            
            return UserResponse.from_orm(user)
    
    async def deactivate_user(
        self,
        user_id: str,
        tenant_id: str,
        deactivated_by: Optional[str] = None,
    ) -> UserResponse:
        """Deactivate a user account."""
        async with self.db_manager.get_session() as session:
            user = await self._get_user_by_id(session, user_id)
            
            if not user:
                raise NotFoundError("User not found")
            
            if user.tenant_id != tenant_id:
                raise AuthorizationError("Access denied")
            
            user.is_active = False
            user.updated_by = deactivated_by
            user.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(
                "User deactivated",
                user_id=user_id,
                tenant_id=tenant_id,
                deactivated_by=deactivated_by,
            )
            
            return UserResponse.from_orm(user)
    
    async def create_api_key(
        self,
        api_key_data: APIKeyCreate,
        user_id: str,
        tenant_id: str,
    ) -> APIKeyResponse:
        """Create a new API key for a user."""
        async with self.db_manager.get_session() as session:
            # Generate API key
            plain_key = generate_api_key()
            hashed_key = hash_api_key(plain_key)
            
            api_key_id = str(uuid4())
            api_key = APIKey(
                id=api_key_id,
                tenant_id=tenant_id,
                user_id=user_id,
                name=api_key_data.name,
                key_hash=hashed_key,
                permissions=api_key_data.permissions,
                expires_at=api_key_data.expires_at,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            
            session.add(api_key)
            await session.commit()
            await session.refresh(api_key)
            
            logger.info(
                "API key created",
                api_key_id=api_key_id,
                user_id=user_id,
                tenant_id=tenant_id,
                name=api_key_data.name,
            )
            
            # Return response with plain key (only time it's visible)
            response = APIKeyResponse.from_orm(api_key)
            response.key = plain_key  # Include plain key in response
            return response
    
    async def authenticate_api_key(
        self, api_key: str, tenant_id: str
    ) -> Tuple[str, list[str]]:  # Returns (user_id, permissions)
        """Authenticate an API key and return user ID and permissions."""
        async with self.db_manager.get_session() as session:
            # Get all active API keys for the tenant
            stmt = select(APIKey).where(
                APIKey.tenant_id == tenant_id,
                APIKey.is_active == True,
                (APIKey.expires_at.is_(None) | (APIKey.expires_at > datetime.now(timezone.utc))),
            )
            result = await session.execute(stmt)
            api_keys = result.scalars().all()
            
            # Check each API key
            for key_record in api_keys:
                if verify_api_key(api_key, key_record.key_hash):
                    logger.info(
                        "API key authenticated",
                        api_key_id=key_record.id,
                        user_id=key_record.user_id,
                        tenant_id=tenant_id,
                    )
                    return key_record.user_id, key_record.permissions
            
            logger.warning("API key authentication failed", tenant_id=tenant_id)
            raise AuthenticationError("Invalid API key")
    
    async def _get_user_by_username(
        self, session: AsyncSession, username: str, tenant_id: str
    ) -> Optional[User]:
        """Get a user by username within a tenant."""
        stmt = select(User).where(
            User.username == username,
            User.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_by_email(
        self, session: AsyncSession, email: str, tenant_id: str
    ) -> Optional[User]:
        """Get a user by email within a tenant."""
        stmt = select(User).where(
            User.email == email,
            User.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_by_id(
        self, session: AsyncSession, user_id: str
    ) -> Optional[User]:
        """Get a user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


# Global auth service instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get the global auth service instance."""
    global _auth_service
    if _auth_service is None:
        from app.core.security import get_security_manager
        _auth_service = AuthService(get_security_manager())
    return _auth_service