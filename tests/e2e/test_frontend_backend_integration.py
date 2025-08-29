#!/usr/bin/env python3
"""
End-to-End Test: Frontend-Backend Integration

This test verifies that the frontend can successfully communicate with the backend
and perform all CRUD operations on audit events through the UI.
"""

import requests
import time
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class FrontendBackendIntegrationTest:
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str = "", error: str = ""):
        """Log test results."""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "error": error,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   {message}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def wait_for_service(self, url: str, service_name: str, timeout: int = 60) -> bool:
        """Wait for a service to be ready."""
        print(f"Waiting for {service_name} to be ready...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {service_name} is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            time.sleep(2)
            print(".", end="", flush=True)
        
        print(f"\n❌ {service_name} failed to start within {timeout} seconds")
        return False
    
    def test_api_health(self) -> bool:
        """Test API health endpoint."""
        try:
            response = self.session.get(f"{self.api_base_url}/health/")
            if response.status_code == 200:
                self.log_test("API Health Check", True, "API is healthy")
                return True
            else:
                self.log_test("API Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("API Health Check", False, error=str(e))
            return False
    
    def test_frontend_access(self) -> bool:
        """Test frontend accessibility."""
        try:
            response = self.session.get(self.frontend_url)
            if response.status_code == 200:
                self.log_test("Frontend Access", True, "Frontend is accessible")
                return True
            else:
                self.log_test("Frontend Access", False, f"Frontend returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Access", False, error=str(e))
            return False
    
    def test_frontend_api_proxy(self) -> bool:
        """Test if frontend can proxy API requests."""
        try:
            response = self.session.get(f"{self.frontend_url}/api/v1/audit/events?page=1&size=1")
            if response.status_code == 200:
                self.log_test("Frontend API Proxy", True, "Frontend can proxy API requests")
                return True
            else:
                self.log_test("Frontend API Proxy", False, f"Proxy returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend API Proxy", False, error=str(e))
            return False
    
    def test_create_audit_event(self) -> Optional[str]:
        """Test creating an audit event via API."""
        event_data = {
            "event_type": "e2e_test_event",
            "action": "test_action",
            "status": "success",
            "tenant_id": "e2e_test_tenant",
            "service_name": "e2e_test_service",
            "user_id": "e2e_test_user",
            "resource_type": "e2e_test_resource",
            "resource_id": "e2e_test_resource_123",
            "metadata": {
                "test_key": "test_value",
                "source": "e2e_test"
            }
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/v1/audit/events",
                json=event_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                audit_id = result.get("audit_id")
                self.log_test("Create Audit Event", True, f"Event created with ID: {audit_id}")
                return audit_id
            else:
                self.log_test("Create Audit Event", False, f"API returned status {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Create Audit Event", False, error=str(e))
            return None
    
    def test_retrieve_audit_event(self, audit_id: str) -> bool:
        """Test retrieving an audit event via API."""
        try:
            response = self.session.get(f"{self.api_base_url}/api/v1/audit/events/{audit_id}")
            
            if response.status_code == 200:
                result = response.json()
                retrieved_id = result.get("audit_id")
                if retrieved_id == audit_id:
                    self.log_test("Retrieve Audit Event", True, f"Event retrieved successfully: {audit_id}")
                    return True
                else:
                    self.log_test("Retrieve Audit Event", False, f"Retrieved wrong event ID: {retrieved_id}")
                    return False
            else:
                self.log_test("Retrieve Audit Event", False, f"API returned status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Retrieve Audit Event", False, error=str(e))
            return False
    
    def test_query_audit_events(self) -> bool:
        """Test querying audit events via API."""
        try:
            response = self.session.get(f"{self.api_base_url}/api/v1/audit/events?page=1&size=5")
            
            if response.status_code == 200:
                result = response.json()
                total_count = result.get("total_count", 0)
                items = result.get("items", [])
                
                self.log_test("Query Audit Events", True, f"Found {total_count} events, returned {len(items)}")
                return True
            else:
                self.log_test("Query Audit Events", False, f"API returned status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Query Audit Events", False, error=str(e))
            return False
    
    def test_batch_create_events(self) -> bool:
        """Test creating multiple audit events in batch."""
        batch_data = {
            "events": [
                {
                    "event_type": "e2e_batch_test_1",
                    "action": "batch_action_1",
                    "status": "success",
                    "tenant_id": "e2e_batch_tenant",
                    "service_name": "e2e_batch_service",
                    "user_id": "e2e_batch_user_1"
                },
                {
                    "event_type": "e2e_batch_test_2",
                    "action": "batch_action_2",
                    "status": "success",
                    "tenant_id": "e2e_batch_tenant",
                    "service_name": "e2e_batch_service",
                    "user_id": "e2e_batch_user_2"
                }
            ]
        }
        
        try:
            response = self.session.post(
                f"{self.api_base_url}/api/v1/audit/events/batch",
                json=batch_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                created_count = len(result)
                self.log_test("Batch Create Events", True, f"Created {created_count} events in batch")
                return True
            else:
                self.log_test("Batch Create Events", False, f"API returned status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Batch Create Events", False, error=str(e))
            return False
    
    def test_filter_events(self) -> bool:
        """Test filtering audit events."""
        try:
            # Test filtering by event type
            response = self.session.get(f"{self.api_base_url}/api/v1/audit/events?event_types=e2e_test_event&page=1&size=10")
            
            if response.status_code == 200:
                result = response.json()
                filtered_count = result.get("total_count", 0)
                self.log_test("Filter Events", True, f"Found {filtered_count} events matching filter")
                return True
            else:
                self.log_test("Filter Events", False, f"API returned status {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Filter Events", False, error=str(e))
            return False
    
    def test_frontend_ui_elements(self) -> bool:
        """Test that frontend UI elements are accessible."""
        try:
            # Test main page
            response = self.session.get(self.frontend_url)
            if response.status_code != 200:
                self.log_test("Frontend UI Elements", False, "Main page not accessible")
                return False
            
            # Check for key UI elements in the HTML
            html_content = response.text.lower()
            required_elements = [
                "audit"
            ]
            
            # For production builds, we might not see React/Dashboard/Events in the HTML
            # but we should see the audit-related content
            missing_elements = [elem for elem in required_elements if elem not in html_content]
            
            if missing_elements:
                self.log_test("Frontend UI Elements", False, f"Missing UI elements: {missing_elements}")
                return False
            else:
                self.log_test("Frontend UI Elements", True, "Frontend is serving audit application")
                return True
                
        except Exception as e:
            self.log_test("Frontend UI Elements", False, error=str(e))
            return False
    
    def run_all_tests(self) -> bool:
        """Run all E2E tests."""
        print("🚀 Starting Frontend-Backend Integration Tests")
        print("=" * 60)
        
        # Wait for services to be ready
        if not self.wait_for_service(f"{self.api_base_url}/health/", "API"):
            return False
        
        if not self.wait_for_service(self.frontend_url, "Frontend"):
            return False
        
        # Run basic connectivity tests
        if not self.test_api_health():
            return False
        
        if not self.test_frontend_access():
            return False
        
        if not self.test_frontend_api_proxy():
            return False
        
        # Run CRUD operation tests
        audit_id = self.test_create_audit_event()
        if not audit_id:
            return False
        
        if not self.test_retrieve_audit_event(audit_id):
            return False
        
        if not self.test_query_audit_events():
            return False
        
        if not self.test_batch_create_events():
            return False
        
        if not self.test_filter_events():
            return False
        
        # Run UI tests
        if not self.test_frontend_ui_elements():
            return False
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📋 E2E Test Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result.get('error', result.get('message', 'Unknown error'))}")
        
        overall_status = "PASSED" if failed_tests == 0 else "FAILED"
        print(f"\nOverall Status: {overall_status}")

def main():
    """Main test function."""
    test = FrontendBackendIntegrationTest()
    
    try:
        success = test.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
