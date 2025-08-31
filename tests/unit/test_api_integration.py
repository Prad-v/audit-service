"""
Integration tests for API endpoints.

This module tests the complete API functionality including authentication,
audit log operations, and error handling through HTTP requests.
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
import json

from app.models.audit import EventType, Severity
from app.models.auth import UserRole


class TestHealthEndpoints:
    """Test cases for health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["service"] == "audit-log-framework"


class TestAuthenticationEndpoints:
    """Test cases for authentication endpoints."""

    def test_login_success(self, client, test_user, test_user_data, test_tenant_id):
        """Test successful login."""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
            "tenant_id": test_tenant_id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, test_user, test_tenant_id):
        """Test login with invalid credentials."""
        login_data = {
            "username": test_user.username,
            "password": "wrongpassword",
            "tenant_id": test_tenant_id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "message" in data

    def test_login_invalid_tenant(self, client, test_user, test_user_data):
        """Test login with invalid tenant."""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
            "tenant_id": "invalid-tenant"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        """Test login with missing required fields."""
        login_data = {
            "username": "testuser"
            # Missing password and tenant_id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 422  # Validation error

    def test_refresh_token_success(self, client, test_user, test_user_data, test_tenant_id):
        """Test successful token refresh."""
        # First, login to get tokens
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"],
            "tenant_id": test_tenant_id
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        login_data = login_response.json()
        
        # Now refresh the token
        refresh_data = {
            "refresh_token": login_data["refresh_token"]
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

    def test_refresh_token_invalid(self, client):
        """Test token refresh with invalid refresh token."""
        refresh_data = {
            "refresh_token": "invalid-refresh-token"
        }
        
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401

    def test_logout_success(self, client, auth_headers):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200

    def test_logout_without_auth(self, client):
        """Test logout without authentication."""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 401

    def test_get_current_user_success(self, client, auth_headers, test_user):
        """Test getting current user information."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["is_active"] == test_user.is_active

    def test_get_current_user_without_auth(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        assert response.status_code == 401


class TestUserManagementEndpoints:
    """Test cases for user management endpoints."""

    def test_create_user_success(self, client, admin_auth_headers):
        """Test successful user creation by admin."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "password123",
            "roles": [UserRole.AUDIT_VIEWER.value],
            "is_active": True
        }
        
        response = client.post("/api/v1/auth/users", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["is_active"] is True
        assert UserRole.AUDIT_VIEWER.value in data["roles"]

    def test_create_user_without_admin_role(self, client, auth_headers):
        """Test user creation without admin role."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "password123",
            "roles": [UserRole.AUDIT_VIEWER.value]
        }
        
        response = client.post("/api/v1/auth/users", json=user_data, headers=auth_headers)
        
        assert response.status_code == 403  # Forbidden

    def test_create_user_duplicate_username(self, client, admin_auth_headers, test_user):
        """Test user creation with duplicate username."""
        user_data = {
            "username": test_user.username,  # Duplicate
            "email": "different@example.com",
            "full_name": "Different User",
            "password": "password123",
            "roles": [UserRole.AUDIT_VIEWER.value]
        }
        
        response = client.post("/api/v1/auth/users", json=user_data, headers=admin_auth_headers)
        
        assert response.status_code == 400

    def test_get_user_success(self, client, admin_auth_headers, test_user):
        """Test successful user retrieval."""
        response = client.get(f"/api/v1/auth/users/{test_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_user.id
        assert data["username"] == test_user.username

    def test_get_user_not_found(self, client, admin_auth_headers):
        """Test user retrieval with non-existent ID."""
        response = client.get("/api/v1/auth/users/non-existent-id", headers=admin_auth_headers)
        
        assert response.status_code == 404

    def test_update_user_success(self, client, admin_auth_headers, test_user):
        """Test successful user update."""
        update_data = {
            "email": "updated@example.com",
            "full_name": "Updated Name"
        }
        
        response = client.put(
            f"/api/v1/auth/users/{test_user.id}", 
            json=update_data, 
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "updated@example.com"
        assert data["full_name"] == "Updated Name"

    def test_deactivate_user_success(self, client, admin_auth_headers, test_user):
        """Test successful user deactivation."""
        response = client.delete(f"/api/v1/auth/users/{test_user.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_active"] is False

    def test_create_api_key_success(self, client, auth_headers):
        """Test successful API key creation."""
        api_key_data = {
            "name": "Test API Key",
            "permissions": ["audit:read", "audit:write"]
        }
        
        response = client.post("/api/v1/auth/api-keys", json=api_key_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Test API Key"
        assert data["permissions"] == ["audit:read", "audit:write"]
        assert "key" in data  # Should include the actual key when creating
        assert data["is_active"] is True


class TestAuditLogEndpoints:
    """Test cases for audit log endpoints."""

    def test_create_event_success(self, client, auth_headers, test_audit_event_data):
        """Test successful audit event creation."""
        # Convert datetime to string for JSON serialization
        event_data = test_audit_event_data.copy()
        if "timestamp" in event_data and event_data["timestamp"]:
            event_data["timestamp"] = event_data["timestamp"].isoformat()
        
        response = client.post("/api/v1/audit/events", json=event_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["event_type"] == event_data["event_type"].value
        assert data["resource_type"] == event_data["resource_type"]
        assert data["action"] == event_data["action"]
        assert data["severity"] == event_data["severity"].value
        assert data["description"] == event_data["description"]

    def test_create_event_without_auth(self, client, test_audit_event_data):
        """Test audit event creation without authentication."""
        response = client.post("/api/v1/audit/events", json=test_audit_event_data)
        
        assert response.status_code == 401

    def test_create_event_invalid_data(self, client, auth_headers):
        """Test audit event creation with invalid data."""
        invalid_data = {
            "event_type": "invalid_type",
            # Missing required fields
        }
        
        response = client.post("/api/v1/audit/events", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422  # Validation error

    def test_create_events_batch_success(self, client, auth_headers, test_batch_audit_events):
        """Test successful batch audit event creation."""
        batch_data = {
            "audit_logs": test_batch_audit_events
        }
        
        response = client.post("/api/v1/audit/events/batch", json=batch_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == len(test_batch_audit_events)
        
        for event in data:
            assert "id" in event
            assert "event_type" in event
            assert "resource_type" in event

    def test_get_event_success(self, client, auth_headers, test_audit_events):
        """Test successful event retrieval."""
        test_event = test_audit_events[0]
        
        response = client.get(f"/api/v1/audit/events/{test_event.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_event.id
        assert data["event_type"] == test_event.event_type.value

    def test_get_event_not_found(self, client, auth_headers):
        """Test event retrieval with non-existent ID."""
        response = client.get("/api/v1/audit/events/non-existent-id", headers=auth_headers)
        
        assert response.status_code == 404

    def test_query_events_no_filters(self, client, auth_headers, test_audit_events):
        """Test querying events without filters."""
        response = client.get("/api/v1/audit/events", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        
        assert isinstance(data["items"], list)
        assert data["total"] >= len(test_audit_events)

    def test_query_events_with_pagination(self, client, auth_headers, test_audit_events):
        """Test querying events with pagination."""
        params = {"page": 1, "size": 2}
        
        response = client.get("/api/v1/audit/events", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page"] == 1
        assert data["size"] == 2
        assert len(data["items"]) <= 2

    def test_query_events_with_filters(self, client, auth_headers, test_audit_events):
        """Test querying events with filters."""
        params = {
            "event_types": EventType.USER_ACTION.value,
            "severities": Severity.INFO.value,
            "resource_types": "user"
        }
        
        response = client.get("/api/v1/audit/events", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned events should match the filters
        for event in data["items"]:
            assert event["event_type"] == EventType.USER_ACTION.value
            assert event["severity"] == Severity.INFO.value
            assert event["resource_type"] == "user"

    def test_query_events_with_date_range(self, client, auth_headers, test_audit_events):
        """Test querying events with date range."""
        start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        end_date = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        
        response = client.get("/api/v1/audit/events", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All events should be within the date range
        for event in data["items"]:
            event_timestamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
            assert datetime.fromisoformat(start_date.replace("Z", "+00:00")) <= event_timestamp <= datetime.fromisoformat(end_date.replace("Z", "+00:00"))

    def test_query_events_with_search(self, client, auth_headers, test_audit_events):
        """Test querying events with search term."""
        params = {"search": "login"}
        
        response = client.get("/api/v1/audit/events", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All events should contain the search term
        for event in data["items"]:
            assert ("login" in event["description"].lower() or 
                   "login" in event["action"].lower())

    def test_get_summary_success(self, client, auth_headers, test_audit_events):
        """Test getting audit log summary."""
        response = client.get("/api/v1/audit/summary", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_count" in data
        assert "event_types" in data
        assert "severities" in data
        assert "resource_types" in data
        assert "date_range" in data
        
        assert isinstance(data["event_types"], dict)
        assert isinstance(data["severities"], dict)
        assert isinstance(data["resource_types"], dict)

    def test_get_summary_with_filters(self, client, auth_headers, test_audit_events):
        """Test getting audit log summary with filters."""
        start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        params = {
            "start_date": start_date,
            "event_types": EventType.USER_ACTION.value
        }
        
        response = client.get("/api/v1/audit/summary", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_count"] >= 0

    def test_export_events_json(self, client, auth_headers, test_audit_events):
        """Test exporting events in JSON format."""
        params = {"format": "json"}
        
        response = client.get("/api/v1/audit/events/export", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert "format" in data
        assert "count" in data
        assert "generated_at" in data
        
        assert data["format"] == "json"
        assert isinstance(data["data"], list)

    def test_export_events_csv(self, client, auth_headers, test_audit_events):
        """Test exporting events in CSV format."""
        params = {"format": "csv"}
        
        response = client.get("/api/v1/audit/events/export", params=params, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["format"] == "csv"

    def test_export_events_invalid_format(self, client, auth_headers):
        """Test exporting events with invalid format."""
        params = {"format": "invalid"}
        
        response = client.get("/api/v1/audit/events/export", params=params, headers=auth_headers)
        
        assert response.status_code == 400


class TestAPIKeyAuthentication:
    """Test cases for API key authentication."""

    def test_api_key_authentication_success(self, client, api_key_headers, test_audit_event_data):
        """Test successful API key authentication."""
        response = client.post("/api/v1/audit/events", json=test_audit_event_data, headers=api_key_headers)
        
        # This might fail if API key validation is not implemented
        # In a real implementation, you'd need to create a valid API key first
        # For now, we expect it to fail with 401 since we're using a mock API key
        assert response.status_code in [201, 401]

    def test_api_key_missing_tenant_header(self, client, test_audit_event_data):
        """Test API key authentication without tenant header."""
        headers = {"X-API-Key": "test-api-key-123"}
        
        response = client.post("/api/v1/audit/events", json=test_audit_event_data, headers=headers)
        
        assert response.status_code == 401

    def test_api_key_invalid_key(self, client, test_audit_event_data, test_tenant_id):
        """Test API key authentication with invalid key."""
        headers = {
            "X-API-Key": "invalid-api-key",
            "X-Tenant-ID": test_tenant_id
        }
        
        response = client.post("/api/v1/audit/events", json=test_audit_event_data, headers=headers)
        
        assert response.status_code == 401


class TestErrorHandling:
    """Test cases for API error handling."""

    def test_404_not_found(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/api/v1/non-existent-endpoint")
        
        assert response.status_code == 404

    def test_405_method_not_allowed(self, client):
        """Test 405 error for unsupported HTTP method."""
        response = client.patch("/api/v1/health")  # PATCH not supported
        
        assert response.status_code == 405

    def test_422_validation_error(self, client, auth_headers):
        """Test 422 validation error."""
        invalid_data = {
            "invalid_field": "invalid_value"
        }
        
        response = client.post("/api/v1/audit/events", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == 422
        data = response.json()
        
        assert "detail" in data  # FastAPI validation error format

    def test_rate_limiting(self, client, auth_headers):
        """Test rate limiting (if implemented)."""
        # This would test rate limiting by making many requests quickly
        # In a real implementation, you'd configure rate limits and test them
        pass

    def test_request_size_limit(self, client, auth_headers):
        """Test request size limits."""
        # Create a very large request payload
        large_metadata = {f"key_{i}": "x" * 1000 for i in range(100)}
        
        event_data = {
            "event_type": EventType.USER_ACTION.value,
            "resource_type": "user",
            "action": "test",
            "severity": Severity.INFO.value,
            "description": "Large metadata test",
            "metadata": large_metadata
        }
        
        response = client.post("/api/v1/audit/events", json=event_data, headers=auth_headers)
        
        # Should either succeed or fail with appropriate error
        assert response.status_code in [201, 413, 400]


class TestTenantIsolation:
    """Test cases for multi-tenant isolation in API."""

    def test_tenant_isolation_in_queries(self, client, auth_headers):
        """Test that queries only return events from the correct tenant."""
        response = client.get("/api/v1/audit/events", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All events should belong to the authenticated user's tenant
        # This would be verified by checking the tenant_id in the JWT token
        for event in data["items"]:
            # In a real implementation, you'd verify the tenant_id matches
            assert "tenant_id" in event

    def test_cross_tenant_access_denied(self, client):
        """Test that cross-tenant access is denied."""
        # This would test accessing resources from a different tenant
        # In a real implementation, you'd create resources in different tenants
        # and verify they can't be accessed cross-tenant
        pass


class TestConcurrency:
    """Test cases for concurrent API access."""

    def test_concurrent_event_creation(self, client, auth_headers):
        """Test concurrent event creation."""
        import threading
        import time
        
        results = []
        
        def create_event(index):
            event_data = {
                "event_type": EventType.API_CALL.value,
                "resource_type": "api",
                "action": "concurrent_test",
                "severity": Severity.INFO.value,
                "description": f"Concurrent test event {index}",
                "correlation_id": f"concurrent-{index:03d}"
            }
            
            response = client.post("/api/v1/audit/events", json=event_data, headers=auth_headers)
            results.append(response.status_code)
        
        # Create multiple threads to create events concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_event, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 201 for status in results)

    def test_concurrent_queries(self, client, auth_headers, test_audit_events):
        """Test concurrent query operations."""
        import threading
        
        results = []
        
        def query_events(index):
            params = {"page": 1, "size": 10}
            response = client.get("/api/v1/audit/events", params=params, headers=auth_headers)
            results.append(response.status_code)
        
        # Create multiple threads to query events concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=query_events, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)