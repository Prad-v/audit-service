"""
Load testing for the Audit Log Framework using Locust.

This module provides comprehensive load testing scenarios to validate
the system's performance under various load conditions.
"""

import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class AuditLogUser(HttpUser):
    """
    Simulates a user interacting with the Audit Log Framework API.
    
    This user performs various operations including authentication,
    event creation, querying, and export operations.
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Initialize user session and authenticate."""
        self.tenant_id = f"tenant-{random.randint(1, 10)}"
        self.user_id = f"user-{random.randint(1, 100)}"
        self.access_token = None
        self.api_key = None
        
        # Try to authenticate (50% JWT, 50% API key)
        if random.choice([True, False]):
            self.authenticate_jwt()
        else:
            self.authenticate_api_key()
    
    def authenticate_jwt(self):
        """Authenticate using JWT tokens."""
        login_data = {
            "username": f"testuser{random.randint(1, 100)}",
            "password": "testpassword123",
            "tenant_id": self.tenant_id
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=login_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                response.success()
            else:
                # If authentication fails, use API key as fallback
                self.authenticate_api_key()
                response.failure(f"JWT authentication failed: {response.status_code}")
    
    def authenticate_api_key(self):
        """Set up API key authentication."""
        self.api_key = f"api-key-{random.randint(1, 50)}"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        elif self.api_key:
            return {
                "X-API-Key": self.api_key,
                "X-Tenant-ID": self.tenant_id
            }
        else:
            return {}
    
    @task(10)
    def create_single_event(self):
        """Create a single audit log event (most common operation)."""
        event_data = self.generate_audit_event()
        
        with self.client.post(
            "/api/v1/audit/events",
            json=event_data,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create event: {response.status_code}")
    
    @task(3)
    def create_batch_events(self):
        """Create multiple audit log events in batch."""
        batch_size = random.randint(5, 20)
        events = [self.generate_audit_event() for _ in range(batch_size)]
        
        batch_data = {"audit_logs": events}
        
        with self.client.post(
            "/api/v1/audit/events/batch",
            json=batch_data,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create batch events: {response.status_code}")
    
    @task(5)
    def query_events_simple(self):
        """Query audit events with simple parameters."""
        params = {
            "page": random.randint(1, 5),
            "size": random.choice([10, 25, 50, 100])
        }
        
        with self.client.get(
            "/api/v1/audit/events",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to query events: {response.status_code}")
    
    @task(3)
    def query_events_filtered(self):
        """Query audit events with filters."""
        params = {
            "page": 1,
            "size": 50,
            "event_types": random.choice([
                "user_action",
                "api_call",
                "data_access",
                "system_event"
            ]),
            "severities": random.choice([
                "info",
                "warning",
                "error",
                "critical"
            ]),
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        with self.client.get(
            "/api/v1/audit/events",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to query filtered events: {response.status_code}")
    
    @task(2)
    def query_events_search(self):
        """Query audit events with search term."""
        search_terms = ["login", "create", "update", "delete", "error", "success"]
        
        params = {
            "page": 1,
            "size": 25,
            "search": random.choice(search_terms)
        }
        
        with self.client.get(
            "/api/v1/audit/events",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to search events: {response.status_code}")
    
    @task(2)
    def get_summary(self):
        """Get audit log summary statistics."""
        params = {
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        with self.client.get(
            "/api/v1/audit/summary",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get summary: {response.status_code}")
    
    @task(1)
    def export_events(self):
        """Export audit events (less frequent operation)."""
        params = {
            "format": random.choice(["json", "csv"]),
            "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        with self.client.get(
            "/api/v1/audit/events/export",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to export events: {response.status_code}")
    
    @task(1)
    def get_current_user(self):
        """Get current user information."""
        if not self.access_token:
            # Skip this task if using API key authentication
            raise RescheduleTask()
        
        with self.client.get(
            "/api/v1/auth/me",
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get current user: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Perform health check."""
        with self.client.get(
            "/api/v1/health",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    def generate_audit_event(self) -> Dict[str, Any]:
        """Generate a realistic audit event for testing."""
        event_types = [
            "user_action",
            "api_call", 
            "data_access",
            "data_modification",
            "system_event",
            "authentication",
            "authorization",
            "error"
        ]
        
        severities = ["debug", "info", "warning", "error", "critical"]
        
        actions = [
            "login", "logout", "create", "update", "delete", "read",
            "upload", "download", "export", "import", "backup", "restore"
        ]
        
        resource_types = [
            "user", "api", "database", "file", "system", "application",
            "service", "configuration", "report", "dashboard"
        ]
        
        event_type = random.choice(event_types)
        resource_type = random.choice(resource_types)
        action = random.choice(actions)
        severity = random.choice(severities)
        
        # Generate realistic metadata based on event type
        metadata = self.generate_metadata(event_type, action)
        
        return {
            "event_type": event_type,
            "resource_type": resource_type,
            "action": action,
            "severity": severity,
            "description": f"{action.title()} {resource_type} - Load test event",
            "user_id": self.user_id,
            "resource_id": f"{resource_type}-{random.randint(1, 1000)}",
            "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "user_agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            ]),
            "session_id": f"session-{random.randint(1, 10000)}",
            "correlation_id": f"load-test-{int(time.time())}-{random.randint(1, 9999)}",
            "metadata": metadata
        }
    
    def generate_metadata(self, event_type: str, action: str) -> Dict[str, Any]:
        """Generate realistic metadata based on event type and action."""
        base_metadata = {
            "load_test": True,
            "timestamp": datetime.utcnow().isoformat(),
            "test_run_id": getattr(self, 'test_run_id', 'unknown')
        }
        
        if event_type == "user_action":
            base_metadata.update({
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "device_type": random.choice(["desktop", "mobile", "tablet"]),
                "success": random.choice([True, False])
            })
        
        elif event_type == "api_call":
            base_metadata.update({
                "endpoint": f"/api/v1/{random.choice(['users', 'events', 'reports'])}",
                "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
                "response_time_ms": random.randint(10, 500),
                "status_code": random.choice([200, 201, 400, 401, 403, 404, 500])
            })
        
        elif event_type == "data_access":
            base_metadata.update({
                "table_name": random.choice(["users", "audit_logs", "api_keys"]),
                "query_type": random.choice(["SELECT", "INSERT", "UPDATE", "DELETE"]),
                "rows_affected": random.randint(1, 100),
                "execution_time_ms": random.randint(1, 50)
            })
        
        elif event_type == "system_event":
            base_metadata.update({
                "component": random.choice(["database", "cache", "queue", "worker"]),
                "memory_usage_mb": random.randint(100, 2000),
                "cpu_usage_percent": random.randint(10, 90)
            })
        
        return base_metadata


class AdminUser(HttpUser):
    """
    Simulates an admin user performing administrative operations.
    
    This user performs less frequent but more resource-intensive operations
    like user management and system administration.
    """
    
    wait_time = between(5, 15)  # Longer wait time for admin operations
    weight = 1  # Lower weight (fewer admin users)
    
    def on_start(self):
        """Initialize admin session."""
        self.tenant_id = "admin-tenant"
        self.access_token = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate as admin user."""
        login_data = {
            "username": "admin",
            "password": "adminpassword123",
            "tenant_id": self.tenant_id
        }
        
        with self.client.post(
            "/api/v1/auth/login",
            json=login_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                response.success()
            else:
                response.failure(f"Admin authentication failed: {response.status_code}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get admin authentication headers."""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    @task(3)
    def create_user(self):
        """Create a new user (admin operation)."""
        user_data = {
            "username": f"loadtest_user_{random.randint(1, 10000)}",
            "email": f"loadtest{random.randint(1, 10000)}@example.com",
            "full_name": f"Load Test User {random.randint(1, 10000)}",
            "password": "testpassword123",
            "roles": [random.choice(["audit_viewer", "audit_manager", "api_user"])],
            "is_active": True
        }
        
        with self.client.post(
            "/api/v1/auth/users",
            json=user_data,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create user: {response.status_code}")
    
    @task(2)
    def create_api_key(self):
        """Create a new API key."""
        api_key_data = {
            "name": f"Load Test API Key {random.randint(1, 1000)}",
            "permissions": random.choice([
                ["audit:read"],
                ["audit:read", "audit:write"],
                ["audit:read", "audit:write", "audit:export"]
            ])
        }
        
        with self.client.post(
            "/api/v1/auth/api-keys",
            json=api_key_data,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Failed to create API key: {response.status_code}")
    
    @task(1)
    def export_large_dataset(self):
        """Export a large dataset (resource-intensive operation)."""
        params = {
            "format": "json",
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        
        with self.client.get(
            "/api/v1/audit/events/export",
            params=params,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to export large dataset: {response.status_code}")


class HighVolumeUser(HttpUser):
    """
    Simulates high-volume event creation for stress testing.
    
    This user focuses on creating many events quickly to test
    the system's ability to handle high throughput.
    """
    
    wait_time = between(0.1, 0.5)  # Very short wait time
    weight = 2  # Higher weight for stress testing
    
    def on_start(self):
        """Initialize high-volume session."""
        self.tenant_id = f"hv-tenant-{random.randint(1, 5)}"
        self.api_key = f"hv-api-key-{random.randint(1, 10)}"
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "X-API-Key": self.api_key,
            "X-Tenant-ID": self.tenant_id
        }
    
    @task(15)
    def rapid_event_creation(self):
        """Create events rapidly for stress testing."""
        event_data = {
            "event_type": "api_call",
            "resource_type": "api",
            "action": "stress_test",
            "severity": "info",
            "description": "High volume stress test event",
            "correlation_id": f"stress-{int(time.time())}-{random.randint(1, 9999)}",
            "metadata": {
                "stress_test": True,
                "batch_id": f"batch-{random.randint(1, 100)}"
            }
        }
        
        with self.client.post(
            "/api/v1/audit/events",
            json=event_data,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Rapid event creation failed: {response.status_code}")
    
    @task(5)
    def rapid_batch_creation(self):
        """Create batch events rapidly."""
        batch_size = random.randint(10, 50)
        events = []
        
        for i in range(batch_size):
            events.append({
                "event_type": "system_event",
                "resource_type": "system",
                "action": "batch_stress_test",
                "severity": "debug",
                "description": f"Batch stress test event {i}",
                "correlation_id": f"batch-stress-{int(time.time())}-{i}",
                "metadata": {"batch_index": i, "stress_test": True}
            })
        
        batch_data = {"audit_logs": events}
        
        with self.client.post(
            "/api/v1/audit/events/batch",
            json=batch_data,
            headers=self.get_auth_headers(),
            catch_response=True
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Rapid batch creation failed: {response.status_code}")


# Event handlers for custom metrics and reporting

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test run."""
    print("Starting Audit Log Framework load test...")
    
    # Set test run ID for correlation
    test_run_id = f"load-test-{int(time.time())}"
    for user_class in [AuditLogUser, AdminUser, HighVolumeUser]:
        user_class.test_run_id = test_run_id


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Clean up after test run."""
    print("Audit Log Framework load test completed.")
    
    # Print summary statistics
    stats = environment.stats
    print(f"\nTest Summary:")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")


# Custom task sets for specific scenarios

class AuthenticationLoadTest(HttpUser):
    """Focused load test for authentication endpoints."""
    
    wait_time = between(1, 2)
    
    @task
    def login_logout_cycle(self):
        """Test login/logout cycle."""
        # Login
        login_data = {
            "username": f"testuser{random.randint(1, 100)}",
            "password": "testpassword123",
            "tenant_id": f"tenant-{random.randint(1, 10)}"
        }
        
        with self.client.post("/api/v1/auth/login", json=login_data) as response:
            if response.status_code == 200:
                token = response.json().get("access_token")
                
                # Use the token for a request
                headers = {"Authorization": f"Bearer {token}"}
                self.client.get("/api/v1/auth/me", headers=headers)
                
                # Logout
                self.client.post("/api/v1/auth/logout", headers=headers)


class QueryPerformanceTest(HttpUser):
    """Focused load test for query performance."""
    
    wait_time = between(0.5, 1.5)
    
    def on_start(self):
        """Set up authentication."""
        self.headers = {
            "X-API-Key": "test-api-key",
            "X-Tenant-ID": "test-tenant"
        }
    
    @task(5)
    def simple_query(self):
        """Test simple queries."""
        params = {"page": 1, "size": 50}
        self.client.get("/api/v1/audit/events", params=params, headers=self.headers)
    
    @task(3)
    def complex_query(self):
        """Test complex queries with multiple filters."""
        params = {
            "page": 1,
            "size": 100,
            "event_types": "user_action,api_call",
            "severities": "info,warning,error",
            "start_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "end_date": datetime.utcnow().isoformat(),
            "search": "test"
        }
        self.client.get("/api/v1/audit/events", params=params, headers=self.headers)
    
    @task(1)
    def summary_query(self):
        """Test summary queries."""
        params = {
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
        self.client.get("/api/v1/audit/summary", params=params, headers=self.headers)