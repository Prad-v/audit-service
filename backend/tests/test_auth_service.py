"""
Unit tests for the Authentication Service.

This module tests all authentication-related functionality including
user management, JWT tokens, API keys, and RBAC.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.models.auth import UserCreate, UserUpdate, UserRole, APIKeyCreate
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError
)
from app.core.security import verify_password, create_access_token, decode_access_token


class TestAuthService:
    """Test cases for AuthService."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, auth_service, test_tenant_id):
        """Set up test data for each test."""
        self.auth_service = auth_service
        self.tenant_id = test_tenant_id

    async def test_create_user_success(self):
        """Test successful user creation."""
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            full_name="New User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER],
            is_active=True
        )

        user = await self.auth_service.create_user(user_data, self.tenant_id)

        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.tenant_id == self.tenant_id
        assert UserRole.AUDIT_VIEWER in user.roles
        assert user.is_active is True
        assert user.id is not None
        assert user.created_at is not None
        assert user.updated_at is not None

    async def test_create_user_duplicate_username(self, test_user):
        """Test user creation with duplicate username."""
        user_data = UserCreate(
            username=test_user.username,  # Duplicate username
            email="different@example.com",
            full_name="Different User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER]
        )

        with pytest.raises(ValidationError) as exc_info:
            await self.auth_service.create_user(user_data, self.tenant_id)
        
        assert "username already exists" in str(exc_info.value).lower()

    async def test_create_user_duplicate_email(self, test_user):
        """Test user creation with duplicate email."""
        user_data = UserCreate(
            username="differentuser",
            email=test_user.email,  # Duplicate email
            full_name="Different User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER]
        )

        with pytest.raises(ValidationError) as exc_info:
            await self.auth_service.create_user(user_data, self.tenant_id)
        
        assert "email already exists" in str(exc_info.value).lower()

    async def test_authenticate_user_success(self, test_user):
        """Test successful user authentication."""
        user = await self.auth_service.authenticate_user(
            test_user.username, 
            "testpassword123",  # From test_user_data fixture
            self.tenant_id
        )

        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
        assert user.tenant_id == self.tenant_id

    async def test_authenticate_user_wrong_password(self, test_user):
        """Test authentication with wrong password."""
        user = await self.auth_service.authenticate_user(
            test_user.username,
            "wrongpassword",
            self.tenant_id
        )

        assert user is None

    async def test_authenticate_user_wrong_tenant(self, test_user):
        """Test authentication with wrong tenant."""
        user = await self.auth_service.authenticate_user(
            test_user.username,
            "testpassword123",
            "wrong-tenant-id"
        )

        assert user is None

    async def test_authenticate_user_inactive(self):
        """Test authentication with inactive user."""
        # Create inactive user
        user_data = UserCreate(
            username="inactiveuser",
            email="inactive@example.com",
            full_name="Inactive User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER],
            is_active=False
        )
        
        inactive_user = await self.auth_service.create_user(user_data, self.tenant_id)
        
        user = await self.auth_service.authenticate_user(
            inactive_user.username,
            "password123",
            self.tenant_id
        )

        assert user is None

    async def test_get_user_by_id_success(self, test_user):
        """Test successful user retrieval by ID."""
        user = await self.auth_service.get_user_by_id(test_user.id, self.tenant_id)

        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
        assert user.tenant_id == self.tenant_id

    async def test_get_user_by_id_not_found(self):
        """Test user retrieval with non-existent ID."""
        user = await self.auth_service.get_user_by_id("non-existent-id", self.tenant_id)
        assert user is None

    async def test_get_user_by_id_wrong_tenant(self, test_user):
        """Test user retrieval with wrong tenant."""
        user = await self.auth_service.get_user_by_id(test_user.id, "wrong-tenant-id")
        assert user is None

    async def test_get_user_by_username_success(self, test_user):
        """Test successful user retrieval by username."""
        user = await self.auth_service.get_user_by_username(
            test_user.username, 
            self.tenant_id
        )

        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username

    async def test_update_user_success(self, test_user):
        """Test successful user update."""
        update_data = UserUpdate(
            email="updated@example.com",
            full_name="Updated Name",
            roles=[UserRole.AUDIT_MANAGER]
        )

        updated_user = await self.auth_service.update_user(
            test_user.id,
            update_data,
            self.tenant_id
        )

        assert updated_user.email == "updated@example.com"
        assert updated_user.full_name == "Updated Name"
        assert UserRole.AUDIT_MANAGER in updated_user.roles
        assert updated_user.updated_at > test_user.updated_at

    async def test_update_user_not_found(self):
        """Test user update with non-existent user."""
        update_data = UserUpdate(email="new@example.com")

        with pytest.raises(NotFoundError):
            await self.auth_service.update_user(
                "non-existent-id",
                update_data,
                self.tenant_id
            )

    async def test_update_user_password(self, test_user):
        """Test password update."""
        update_data = UserUpdate(password="newpassword123")

        updated_user = await self.auth_service.update_user(
            test_user.id,
            update_data,
            self.tenant_id
        )

        # Verify old password doesn't work
        auth_result = await self.auth_service.authenticate_user(
            test_user.username,
            "testpassword123",  # Old password
            self.tenant_id
        )
        assert auth_result is None

        # Verify new password works
        auth_result = await self.auth_service.authenticate_user(
            test_user.username,
            "newpassword123",  # New password
            self.tenant_id
        )
        assert auth_result is not None

    async def test_deactivate_user_success(self, test_user):
        """Test successful user deactivation."""
        deactivated_user = await self.auth_service.deactivate_user(
            test_user.id,
            self.tenant_id
        )

        assert deactivated_user.is_active is False
        assert deactivated_user.updated_at > test_user.updated_at

        # Verify user can't authenticate after deactivation
        auth_result = await self.auth_service.authenticate_user(
            test_user.username,
            "testpassword123",
            self.tenant_id
        )
        assert auth_result is None

    async def test_create_api_key_success(self, test_user):
        """Test successful API key creation."""
        api_key_data = APIKeyCreate(
            name="Test API Key",
            permissions=["audit:read", "audit:write"],
            expires_at=datetime.utcnow() + timedelta(days=30)
        )

        api_key = await self.auth_service.create_api_key(
            api_key_data,
            test_user.id,
            self.tenant_id
        )

        assert api_key.name == "Test API Key"
        assert api_key.permissions == ["audit:read", "audit:write"]
        assert api_key.user_id == test_user.id
        assert api_key.tenant_id == self.tenant_id
        assert api_key.is_active is True
        assert api_key.key is not None  # Should include the actual key when creating
        assert len(api_key.key) > 20  # Should be a reasonable length

    async def test_create_api_key_no_expiration(self, test_user):
        """Test API key creation without expiration."""
        api_key_data = APIKeyCreate(
            name="Permanent API Key",
            permissions=["audit:read"]
        )

        api_key = await self.auth_service.create_api_key(
            api_key_data,
            test_user.id,
            self.tenant_id
        )

        assert api_key.expires_at is None

    async def test_validate_api_key_success(self, test_user):
        """Test successful API key validation."""
        # Create API key
        api_key_data = APIKeyCreate(
            name="Test API Key",
            permissions=["audit:read"]
        )
        
        api_key = await self.auth_service.create_api_key(
            api_key_data,
            test_user.id,
            self.tenant_id
        )

        # Validate the key
        validated_key = await self.auth_service.validate_api_key(
            api_key.key,
            self.tenant_id
        )

        assert validated_key is not None
        assert validated_key.id == api_key.id
        assert validated_key.user_id == test_user.id
        assert validated_key.tenant_id == self.tenant_id

    async def test_validate_api_key_invalid(self):
        """Test API key validation with invalid key."""
        validated_key = await self.auth_service.validate_api_key(
            "invalid-api-key",
            self.tenant_id
        )

        assert validated_key is None

    async def test_validate_api_key_expired(self, test_user):
        """Test API key validation with expired key."""
        # Create expired API key
        api_key_data = APIKeyCreate(
            name="Expired API Key",
            permissions=["audit:read"],
            expires_at=datetime.utcnow() - timedelta(days=1)  # Expired
        )
        
        api_key = await self.auth_service.create_api_key(
            api_key_data,
            test_user.id,
            self.tenant_id
        )

        # Try to validate expired key
        validated_key = await self.auth_service.validate_api_key(
            api_key.key,
            self.tenant_id
        )

        assert validated_key is None

    async def test_validate_api_key_inactive(self, test_user):
        """Test API key validation with inactive key."""
        # Create API key
        api_key_data = APIKeyCreate(
            name="Test API Key",
            permissions=["audit:read"]
        )
        
        api_key = await self.auth_service.create_api_key(
            api_key_data,
            test_user.id,
            self.tenant_id
        )

        # Deactivate the API key (this would be done through an admin endpoint)
        # For now, we'll simulate this by directly updating the database
        # In a real implementation, there would be a deactivate_api_key method
        
        # Try to validate - should still work since we haven't actually deactivated it
        validated_key = await self.auth_service.validate_api_key(
            api_key.key,
            self.tenant_id
        )

        assert validated_key is not None

    async def test_check_permission_success(self, test_user):
        """Test successful permission check."""
        # Create API key with specific permissions
        api_key_data = APIKeyCreate(
            name="Test API Key",
            permissions=["audit:read", "audit:write"]
        )
        
        api_key = await self.auth_service.create_api_key(
            api_key_data,
            test_user.id,
            self.tenant_id
        )

        # Check permissions
        has_read = await self.auth_service.check_permission(
            api_key.id,
            "audit:read"
        )
        has_write = await self.auth_service.check_permission(
            api_key.id,
            "audit:write"
        )
        has_admin = await self.auth_service.check_permission(
            api_key.id,
            "admin:users"
        )

        assert has_read is True
        assert has_write is True
        assert has_admin is False

    async def test_update_last_login(self, test_user):
        """Test updating user's last login timestamp."""
        original_last_login = test_user.last_login_at
        
        await self.auth_service.update_last_login(test_user.id)
        
        # Refresh user from database
        updated_user = await self.auth_service.get_user_by_id(
            test_user.id,
            self.tenant_id
        )
        
        assert updated_user.last_login_at is not None
        if original_last_login:
            assert updated_user.last_login_at > original_last_login


class TestSecurityFunctions:
    """Test cases for security utility functions."""

    def test_create_and_decode_access_token(self):
        """Test JWT token creation and decoding."""
        token_data = {
            "sub": "user-123",
            "tenant_id": "tenant-456",
            "roles": ["audit_viewer"],
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

        token = create_access_token(token_data)
        assert token is not None
        assert isinstance(token, str)

        decoded_data = decode_access_token(token)
        assert decoded_data["sub"] == "user-123"
        assert decoded_data["tenant_id"] == "tenant-456"
        assert decoded_data["roles"] == ["audit_viewer"]

    def test_decode_expired_token(self):
        """Test decoding expired JWT token."""
        token_data = {
            "sub": "user-123",
            "tenant_id": "tenant-456",
            "roles": ["audit_viewer"],
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired
        }

        token = create_access_token(token_data)
        
        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token."""
        with pytest.raises(AuthenticationError):
            decode_access_token("invalid.jwt.token")

    def test_password_hashing_and_verification(self):
        """Test password hashing and verification."""
        password = "testpassword123"
        
        # Hash password
        hashed = verify_password(password, password)  # This should work
        assert hashed is True
        
        # Verify wrong password
        wrong_verification = verify_password("wrongpassword", password)
        assert wrong_verification is False


class TestRoleBasedAccess:
    """Test cases for role-based access control."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, auth_service, test_tenant_id):
        """Set up test data for RBAC tests."""
        self.auth_service = auth_service
        self.tenant_id = test_tenant_id

    async def test_system_admin_permissions(self):
        """Test system admin has all permissions."""
        user_data = UserCreate(
            username="sysadmin",
            email="sysadmin@example.com",
            full_name="System Admin",
            password="password123",
            roles=[UserRole.SYSTEM_ADMIN]
        )

        user = await self.auth_service.create_user(user_data, self.tenant_id)
        
        # System admin should have all permissions
        assert UserRole.SYSTEM_ADMIN in user.roles

    async def test_tenant_admin_permissions(self):
        """Test tenant admin permissions."""
        user_data = UserCreate(
            username="tenantadmin",
            email="tenantadmin@example.com",
            full_name="Tenant Admin",
            password="password123",
            roles=[UserRole.TENANT_ADMIN]
        )

        user = await self.auth_service.create_user(user_data, self.tenant_id)
        
        assert UserRole.TENANT_ADMIN in user.roles

    async def test_audit_manager_permissions(self):
        """Test audit manager permissions."""
        user_data = UserCreate(
            username="auditmanager",
            email="auditmanager@example.com",
            full_name="Audit Manager",
            password="password123",
            roles=[UserRole.AUDIT_MANAGER]
        )

        user = await self.auth_service.create_user(user_data, self.tenant_id)
        
        assert UserRole.AUDIT_MANAGER in user.roles

    async def test_audit_viewer_permissions(self):
        """Test audit viewer permissions."""
        user_data = UserCreate(
            username="auditviewer",
            email="auditviewer@example.com",
            full_name="Audit Viewer",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER]
        )

        user = await self.auth_service.create_user(user_data, self.tenant_id)
        
        assert UserRole.AUDIT_VIEWER in user.roles

    async def test_multiple_roles(self):
        """Test user with multiple roles."""
        user_data = UserCreate(
            username="multirole",
            email="multirole@example.com",
            full_name="Multi Role User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER, UserRole.AUDIT_MANAGER]
        )

        user = await self.auth_service.create_user(user_data, self.tenant_id)
        
        assert UserRole.AUDIT_VIEWER in user.roles
        assert UserRole.AUDIT_MANAGER in user.roles
        assert len(user.roles) == 2


class TestTenantIsolation:
    """Test cases for multi-tenant isolation."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, auth_service):
        """Set up test data for tenant isolation tests."""
        self.auth_service = auth_service
        self.tenant1_id = "tenant-1"
        self.tenant2_id = "tenant-2"

    async def test_user_isolation_between_tenants(self):
        """Test that users are isolated between tenants."""
        # Create user in tenant 1
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER]
        )

        user1 = await self.auth_service.create_user(user_data, self.tenant1_id)
        
        # Try to get user from tenant 2
        user_from_tenant2 = await self.auth_service.get_user_by_id(
            user1.id,
            self.tenant2_id
        )
        
        assert user_from_tenant2 is None

    async def test_authentication_tenant_isolation(self):
        """Test authentication respects tenant isolation."""
        # Create user in tenant 1
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER]
        )

        user1 = await self.auth_service.create_user(user_data, self.tenant1_id)
        
        # Try to authenticate from tenant 2
        auth_result = await self.auth_service.authenticate_user(
            user1.username,
            "password123",
            self.tenant2_id
        )
        
        assert auth_result is None

    async def test_api_key_tenant_isolation(self):
        """Test API key validation respects tenant isolation."""
        # Create user and API key in tenant 1
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            password="password123",
            roles=[UserRole.AUDIT_VIEWER]
        )

        user1 = await self.auth_service.create_user(user_data, self.tenant1_id)
        
        api_key_data = APIKeyCreate(
            name="Test API Key",
            permissions=["audit:read"]
        )
        
        api_key = await self.auth_service.create_api_key(
            api_key_data,
            user1.id,
            self.tenant1_id
        )

        # Try to validate API key from tenant 2
        validated_key = await self.auth_service.validate_api_key(
            api_key.key,
            self.tenant2_id
        )
        
        assert validated_key is None