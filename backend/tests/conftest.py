"""
Test configuration and fixtures for the Audit Log Framework.

This module provides pytest fixtures and configuration for testing
all components of the audit log system.
"""

import asyncio
import os
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import get_settings
from app.db.database import get_db, get_async_db
from app.db.schemas import Base
from app.models.auth import UserCreate, UserRole
from app.models.audit import AuditLogEventCreate, EventType, Severity
from app.services.auth_service import AuthService
from app.services.audit_service import AuditService
from app.core.security import create_access_token


# Test database configuration
TEST_DATABASE_URL = "sqlite:///./test.db"
TEST_ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./test_async.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    # Clean up the test database file
    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest_asyncio.fixture(scope="function")
async def test_async_db_engine():
    """Create a test async database engine."""
    engine = create_async_engine(
        TEST_ASYNC_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    
    # Clean up the test database file
    if os.path.exists("./test_async.db"):
        os.remove("./test_async.db")


@pytest.fixture(scope="function")
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest_asyncio.fixture(scope="function")
async def test_async_db_session(test_async_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test async database session."""
    TestingAsyncSessionLocal = sessionmaker(
        test_async_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client(test_db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_async_db_session):
    """Create a test async client with database dependency override."""
    def override_get_async_db():
        return test_async_db_session

    app.dependency_overrides[get_async_db] = override_get_async_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_redis():
    """Create a mock Redis client."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.exists.return_value = False
    return mock_redis


@pytest.fixture(scope="function")
def mock_nats():
    """Create a mock NATS client."""
    mock_nats = AsyncMock()
    mock_nats.publish.return_value = None
    mock_nats.subscribe.return_value = AsyncMock()
    return mock_nats


@pytest.fixture(scope="function")
def test_settings():
    """Create test settings."""
    settings = get_settings()
    settings.database_url = TEST_DATABASE_URL
    settings.redis_url = "redis://localhost:6379/1"  # Use test database
    settings.nats_url = "nats://localhost:4222"
    settings.secret_key = "test-secret-key-for-testing-only"
    settings.environment = "test"
    return settings


@pytest.fixture(scope="function")
def test_tenant_id():
    """Provide a test tenant ID."""
    return "test-tenant-123"


@pytest.fixture(scope="function")
def test_user_data():
    """Provide test user data."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "roles": [UserRole.AUDIT_VIEWER],
        "is_active": True,
    }


@pytest.fixture(scope="function")
def test_admin_user_data():
    """Provide test admin user data."""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "adminpassword123",
        "roles": [UserRole.SYSTEM_ADMIN],
        "is_active": True,
    }


@pytest.fixture(scope="function")
def test_audit_event_data():
    """Provide test audit event data."""
    return {
        "event_type": EventType.USER_ACTION,
        "resource_type": "user",
        "action": "login",
        "severity": Severity.INFO,
        "description": "User login test event",
        "user_id": "test-user-123",
        "resource_id": "resource-456",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 Test Browser",
        "session_id": "session-789",
        "correlation_id": "correlation-abc",
        "metadata": {
            "test_key": "test_value",
            "login_method": "password"
        }
    }


@pytest.fixture(scope="function")
def test_batch_audit_events():
    """Provide test batch audit events."""
    return [
        {
            "event_type": EventType.API_CALL,
            "resource_type": "api",
            "action": "create_user",
            "severity": Severity.INFO,
            "description": f"API call test event {i}",
            "correlation_id": f"batch-req-{i:03d}",
            "metadata": {"batch_id": "test-batch-001", "sequence": i}
        }
        for i in range(1, 6)
    ]


@pytest_asyncio.fixture(scope="function")
async def auth_service(test_async_db_session, test_settings):
    """Create an AuthService instance for testing."""
    return AuthService(test_async_db_session, test_settings)


@pytest_asyncio.fixture(scope="function")
async def audit_service(test_async_db_session, test_settings, mock_redis, mock_nats):
    """Create an AuditService instance for testing."""
    service = AuditService(test_async_db_session, test_settings)
    service.redis_client = mock_redis
    service.nats_client = mock_nats
    return service


@pytest_asyncio.fixture(scope="function")
async def test_user(auth_service, test_user_data, test_tenant_id):
    """Create a test user in the database."""
    user_create = UserCreate(**test_user_data)
    user = await auth_service.create_user(user_create, test_tenant_id)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_admin_user(auth_service, test_admin_user_data, test_tenant_id):
    """Create a test admin user in the database."""
    user_create = UserCreate(**test_admin_user_data)
    user = await auth_service.create_user(user_create, test_tenant_id)
    return user


@pytest.fixture(scope="function")
def test_access_token(test_user, test_tenant_id):
    """Create a test access token."""
    token_data = {
        "sub": test_user.id,
        "tenant_id": test_tenant_id,
        "roles": [role.value for role in test_user.roles],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def test_admin_access_token(test_admin_user, test_tenant_id):
    """Create a test admin access token."""
    token_data = {
        "sub": test_admin_user.id,
        "tenant_id": test_tenant_id,
        "roles": [role.value for role in test_admin_user.roles],
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return create_access_token(token_data)


@pytest.fixture(scope="function")
def auth_headers(test_access_token):
    """Create authorization headers for API requests."""
    return {"Authorization": f"Bearer {test_access_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(test_admin_access_token):
    """Create admin authorization headers for API requests."""
    return {"Authorization": f"Bearer {test_admin_access_token}"}


@pytest.fixture(scope="function")
def api_key_headers(test_tenant_id):
    """Create API key headers for API requests."""
    return {
        "X-API-Key": "test-api-key-123",
        "X-Tenant-ID": test_tenant_id
    }


@pytest_asyncio.fixture(scope="function")
async def test_audit_events(audit_service, test_audit_event_data, test_tenant_id):
    """Create test audit events in the database."""
    events = []
    for i in range(5):
        event_data = test_audit_event_data.copy()
        event_data["description"] = f"Test event {i + 1}"
        event_data["correlation_id"] = f"test-correlation-{i + 1:03d}"
        
        event_create = AuditLogEventCreate(**event_data)
        event = await audit_service.create_event(event_create, test_tenant_id, "test-user-123")
        events.append(event)
    
    return events


# Utility functions for tests

def assert_audit_event_equal(actual, expected, ignore_fields=None):
    """Assert that two audit events are equal, ignoring specified fields."""
    if ignore_fields is None:
        ignore_fields = ["id", "created_at", "timestamp"]
    
    for field in ignore_fields:
        if hasattr(actual, field):
            delattr(actual, field)
        if hasattr(expected, field):
            delattr(expected, field)
    
    assert actual == expected


def create_test_query_params(**kwargs):
    """Create test query parameters for API requests."""
    params = {}
    for key, value in kwargs.items():
        if value is not None:
            if isinstance(value, list):
                params[key] = ",".join(str(v) for v in value)
            elif isinstance(value, datetime):
                params[key] = value.isoformat()
            else:
                params[key] = str(value)
    return params


# Mock external services

@pytest.fixture(scope="function")
def mock_external_api():
    """Mock external API calls."""
    mock = MagicMock()
    mock.post.return_value.status_code = 200
    mock.post.return_value.json.return_value = {"success": True}
    mock.get.return_value.status_code = 200
    mock.get.return_value.json.return_value = {"data": "test"}
    return mock


@pytest.fixture(scope="function")
def mock_email_service():
    """Mock email service."""
    mock = AsyncMock()
    mock.send_email.return_value = True
    return mock


@pytest.fixture(scope="function")
def mock_metrics_collector():
    """Mock metrics collector."""
    mock = MagicMock()
    mock.increment.return_value = None
    mock.histogram.return_value = None
    mock.gauge.return_value = None
    return mock


# Performance testing fixtures

@pytest.fixture(scope="function")
def performance_test_data():
    """Generate data for performance testing."""
    return {
        "small_batch": 10,
        "medium_batch": 100,
        "large_batch": 1000,
        "concurrent_users": 50,
        "test_duration": 30,  # seconds
    }


# Security testing fixtures

@pytest.fixture(scope="function")
def security_test_payloads():
    """Provide security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ],
        "xss_payloads": [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//"
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`"
        ]
    }


# Test data cleanup

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    # Clean up any test files that might have been created
    test_files = ["./test.db", "./test_async.db", "./test_export.json", "./test_export.csv"]
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass  # File might be in use, ignore