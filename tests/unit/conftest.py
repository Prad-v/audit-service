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
from app.db.database import get_database, get_database_session, get_database_manager
from app.db.schemas import Base
from app.models.auth import UserCreate, UserRole
from app.models.audit import AuditEventCreate, EventType, Severity
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
        autocommit=False, autoflush=False, bind=test_async_db_engine, class_=AsyncSession
    )
    async with TestingAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture(scope="function")
def client(test_db_session):
    """Create a test client with database session override."""
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_database] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_async_db_session):
    """Create an async test client with database session override."""
    async def override_get_async_db():
        try:
            yield test_async_db_session
        finally:
            pass
    
    app.dependency_overrides[get_database_session] = override_get_async_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis client."""
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    return mock_redis


@pytest.fixture(scope="function")
def mock_nats():
    """Mock NATS client."""
    mock_nats = AsyncMock()
    mock_nats.publish.return_value = None
    mock_nats.subscribe.return_value = None
    return mock_nats


@pytest.fixture(scope="function")
def test_settings():
    """Test settings with overrides."""
    settings = get_settings()
    settings.environment = "test"
    settings.database.url = TEST_DATABASE_URL
    settings.redis.url = "redis://localhost:6379/1"
    settings.nats.url = "nats://localhost:4222"
    settings.security.secret_key = "test-secret-key-for-testing"
    return settings


@pytest.fixture(scope="function")
def test_tenant_id():
    """Test tenant ID."""
    return "test-tenant-123"


@pytest.fixture(scope="function")
def test_user_data():
    """Test user data."""
    return UserCreate(
        username="testuser",
        email="test@example.com",
        password="TestPass123!",
        tenant_id="test-tenant-123",
        roles=[UserRole.AUDIT_READER],
        is_active=True
    )


@pytest.fixture(scope="function")
def test_admin_user_data():
    """Test admin user data."""
    return UserCreate(
        username="admin",
        email="admin@example.com",
        password="AdminPass123!",
        tenant_id="test-tenant-123",
        roles=[UserRole.SYSTEM_ADMIN, UserRole.AUDIT_ADMIN],
        is_active=True
    )


@pytest.fixture(scope="function")
def test_audit_event_data():
    """Test audit event data."""
    return AuditEventCreate(
        event_type=EventType.USER_ACTION,
        resource_type="user",
        action="login",
        severity=Severity.INFO,
        description="User logged in successfully",
        tenant_id="test-tenant-123",
        service_name="test-service",
        user_id="test-user-123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Test Browser)",
        session_id="test-session-123",
        correlation_id="test-correlation-123",
        metadata={"test_key": "test_value"}
    )


@pytest.fixture(scope="function")
def test_batch_audit_events():
    """Test batch audit events data."""
    return [
        AuditEventCreate(
            event_type=EventType.USER_ACTION,
            resource_type="user",
            action="login",
            severity=Severity.INFO,
            description=f"User login event {i}",
            tenant_id="test-tenant-123",
            service_name="test-service",
            user_id=f"user-{i}",
            metadata={"batch_index": i}
        )
        for i in range(1, 4)
    ]


@pytest_asyncio.fixture(scope="function")
async def auth_service(test_async_db_session, test_settings):
    """Create auth service instance for testing."""
    from app.core.security import get_security_manager
    return AuthService(get_security_manager())


@pytest_asyncio.fixture(scope="function")
async def audit_service(test_async_db_session, test_settings, mock_redis, mock_nats):
    """Create audit service instance for testing."""
    return AuditService()


@pytest_asyncio.fixture(scope="function")
async def test_user(auth_service, test_user_data, test_tenant_id):
    """Create a test user."""
    try:
        user = await auth_service.create_user(test_user_data, test_tenant_id)
        return user
    except Exception:
        # User might already exist, try to get existing user
        return None


@pytest_asyncio.fixture(scope="function")
async def test_admin_user(auth_service, test_admin_user_data, test_tenant_id):
    """Create a test admin user."""
    try:
        user = await auth_service.create_user(test_admin_user_data, test_tenant_id)
        return user
    except Exception:
        # User might already exist, try to get existing user
        return None


@pytest.fixture(scope="function")
def test_access_token(test_user, test_tenant_id):
    """Generate test access token."""
    if test_user:
        return create_access_token(
            user_id=str(test_user.id),
            username=test_user.username,
            tenant_id=test_tenant_id,
            roles=test_user.roles
        )
    return None


@pytest.fixture(scope="function")
def test_admin_access_token(test_admin_user, test_tenant_id):
    """Generate test admin access token."""
    if test_admin_user:
        return create_access_token(
            user_id=str(test_admin_user.id),
            username=test_admin_user.username,
            tenant_id=test_tenant_id,
            roles=test_admin_user.roles
        )
    return None


@pytest.fixture(scope="function")
def auth_headers(test_access_token):
    """Auth headers for API requests."""
    if test_access_token:
        return {"Authorization": f"Bearer {test_access_token}"}
    return {}


@pytest.fixture(scope="function")
def admin_auth_headers(test_admin_access_token):
    """Admin auth headers for API requests."""
    if test_admin_access_token:
        return {"Authorization": f"Bearer {test_admin_access_token}"}
    return {}


@pytest.fixture(scope="function")
def api_key_headers(test_tenant_id):
    """API key headers for API requests."""
    return {
        "X-API-Key": "test-api-key-123",
        "X-Tenant-ID": test_tenant_id
    }


@pytest_asyncio.fixture(scope="function")
async def test_audit_events(audit_service, test_audit_event_data, test_tenant_id):
    """Create test audit events."""
    events = []
    for i in range(3):
        event_data = test_audit_event_data.copy()
        event_data.description = f"Test event {i+1}"
        event_data.metadata = {"test_index": i}
        try:
            event = await audit_service.create_audit_log(event_data, test_tenant_id)
            events.append(event)
        except Exception:
            pass  # Event might already exist
    return events


def assert_audit_event_equal(actual, expected, ignore_fields=None):
    """Assert that audit events are equal."""
    if ignore_fields is None:
        ignore_fields = ["id", "timestamp", "created_at", "partition_date"]
    
    for field in ignore_fields:
        if hasattr(actual, field):
            delattr(actual, field)
        if hasattr(expected, field):
            delattr(expected, field)
    
    assert actual == expected


def create_test_query_params(**kwargs):
    """Create test query parameters."""
    default_params = {
        "page": 1,
        "size": 10,
        "sort_by": "timestamp",
        "sort_order": "desc"
    }
    default_params.update(kwargs)
    return default_params


@pytest.fixture(scope="function")
def mock_external_api():
    """Mock external API calls."""
    mock_api = AsyncMock()
    mock_api.get.return_value = {"status": "success"}
    mock_api.post.return_value = {"status": "created"}
    return mock_api


@pytest.fixture(scope="function")
def mock_email_service():
    """Mock email service."""
    mock_email = AsyncMock()
    mock_email.send_email.return_value = True
    mock_email.send_notification.return_value = True
    return mock_email


@pytest.fixture(scope="function")
def mock_metrics_collector():
    """Mock metrics collector."""
    mock_metrics = MagicMock()
    mock_metrics.increment_counter.return_value = None
    mock_metrics.observe_histogram.return_value = None
    mock_metrics.set_gauge.return_value = None
    return mock_metrics


@pytest.fixture(scope="function")
def performance_test_data():
    """Performance test data."""
    return {
        "large_batch_size": 1000,
        "concurrent_requests": 50,
        "test_duration": 30,
        "expected_throughput": 100
    }


@pytest.fixture(scope="function")
def security_test_payloads():
    """Security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ],
        "path_traversal": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd"
        ],
        "command_injection": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& whoami"
        ]
    }


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up test files after each test."""
    yield
    # Clean up test database files
    test_files = ["./test.db", "./test_async.db"]
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass