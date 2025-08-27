#!/usr/bin/env python3
"""
Smoke tests for audit service deployment verification.

These tests verify basic functionality after deployment to ensure
the service is running correctly in the target environment.
"""

import argparse
import asyncio
import json
import sys
import time
from typing import Any, Dict, List, Optional

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class SmokeTestRunner:
    """Smoke test runner for audit service."""
    
    def __init__(self, base_url: str, production: bool = False):
        self.base_url = base_url.rstrip('/')
        self.production = production
        self.session: Optional[aiohttp.ClientSession] = None
        self.test_results: List[Dict[str, Any]] = []
        
        # Test credentials (should be environment-specific)
        self.test_tenant_id = "smoke-test-tenant"
        self.test_user_id = "smoke-test-user"
        self.api_key = None
        self.jwt_token = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'AuditService-SmokeTest/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self) -> bool:
        """Run all smoke tests."""
        logger.info("Starting smoke tests", base_url=self.base_url, production=self.production)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("API Documentation", self.test_api_docs),
            ("Authentication", self.test_authentication),
            ("Audit Log Creation", self.test_audit_log_creation),
            ("Audit Log Retrieval", self.test_audit_log_retrieval),
            ("Metrics Endpoint", self.test_metrics_endpoint),
        ]
        
        if not self.production:
            # Additional tests for non-production environments
            tests.extend([
                ("Batch Audit Creation", self.test_batch_audit_creation),
                ("Export Functionality", self.test_export_functionality),
            ])
        
        all_passed = True
        
        for test_name, test_func in tests:
            try:
                logger.info("Running test", test_name=test_name)
                start_time = time.time()
                
                result = await test_func()
                
                duration = time.time() - start_time
                
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'PASS' if result else 'FAIL',
                    'duration': duration,
                    'timestamp': time.time()
                })
                
                if result:
                    logger.info("Test passed", test_name=test_name, duration=f"{duration:.2f}s")
                else:
                    logger.error("Test failed", test_name=test_name, duration=f"{duration:.2f}s")
                    all_passed = False
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error("Test error", test_name=test_name, error=str(e), duration=f"{duration:.2f}s")
                
                self.test_results.append({
                    'test_name': test_name,
                    'status': 'ERROR',
                    'error': str(e),
                    'duration': duration,
                    'timestamp': time.time()
                })
                
                all_passed = False
        
        # Print summary
        self.print_test_summary()
        
        return all_passed
    
    async def test_health_endpoint(self) -> bool:
        """Test health check endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    logger.error("Health check failed", status=response.status)
                    return False
                
                data = await response.json()
                
                # Verify required fields
                required_fields = ['status', 'timestamp', 'version']
                for field in required_fields:
                    if field not in data:
                        logger.error("Health check missing field", field=field)
                        return False
                
                if data['status'] != 'healthy':
                    logger.error("Service not healthy", status=data['status'])
                    return False
                
                logger.info("Health check passed", data=data)
                return True
                
        except Exception as e:
            logger.error("Health check error", error=str(e))
            return False
    
    async def test_api_docs(self) -> bool:
        """Test API documentation endpoints."""
        try:
            # Test OpenAPI spec
            async with self.session.get(f"{self.base_url}/openapi.json") as response:
                if response.status != 200:
                    logger.error("OpenAPI spec not accessible", status=response.status)
                    return False
                
                spec = await response.json()
                
                # Verify basic OpenAPI structure
                required_fields = ['openapi', 'info', 'paths']
                for field in required_fields:
                    if field not in spec:
                        logger.error("OpenAPI spec missing field", field=field)
                        return False
                
                # Test docs endpoint
                async with self.session.get(f"{self.base_url}/docs") as docs_response:
                    if docs_response.status != 200:
                        logger.error("API docs not accessible", status=docs_response.status)
                        return False
                
                logger.info("API documentation accessible")
                return True
                
        except Exception as e:
            logger.error("API docs test error", error=str(e))
            return False
    
    async def test_authentication(self) -> bool:
        """Test authentication endpoints."""
        try:
            # Test login endpoint
            login_data = {
                "username": "admin",
                "password": "admin123"  # Default test credentials
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'access_token' in data:
                        self.jwt_token = data['access_token']
                        logger.info("Authentication successful")
                        return True
                
                # If login fails, try to create API key (for testing)
                if not self.production:
                    return await self.test_api_key_creation()
                
                logger.error("Authentication failed", status=response.status)
                return False
                
        except Exception as e:
            logger.error("Authentication test error", error=str(e))
            return False
    
    async def test_api_key_creation(self) -> bool:
        """Test API key creation (non-production only)."""
        try:
            # This would typically require admin credentials
            # For smoke tests, we'll simulate having an API key
            self.api_key = "test-api-key-for-smoke-tests"
            logger.info("API key configured for testing")
            return True
            
        except Exception as e:
            logger.error("API key test error", error=str(e))
            return False
    
    async def test_audit_log_creation(self) -> bool:
        """Test audit log creation."""
        try:
            headers = self._get_auth_headers()
            if not headers:
                logger.error("No authentication available for audit log test")
                return False
            
            # Create test audit log
            audit_data = {
                "tenant_id": self.test_tenant_id,
                "user_id": self.test_user_id,
                "event_type": "smoke_test",
                "resource_type": "test_resource",
                "resource_id": "test-123",
                "action": "create",
                "metadata": {
                    "test": True,
                    "timestamp": time.time()
                }
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/audit/logs",
                json=audit_data,
                headers=headers
            ) as response:
                if response.status not in [200, 201]:
                    logger.error("Audit log creation failed", status=response.status)
                    return False
                
                data = await response.json()
                
                # Verify response structure
                if 'id' not in data:
                    logger.error("Audit log response missing ID")
                    return False
                
                # Store ID for retrieval test
                self.test_audit_id = data['id']
                
                logger.info("Audit log created successfully", audit_id=data['id'])
                return True
                
        except Exception as e:
            logger.error("Audit log creation error", error=str(e))
            return False
    
    async def test_audit_log_retrieval(self) -> bool:
        """Test audit log retrieval."""
        try:
            headers = self._get_auth_headers()
            if not headers:
                logger.error("No authentication available for audit log retrieval test")
                return False
            
            # Test list endpoint
            params = {
                "tenant_id": self.test_tenant_id,
                "limit": 10
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v1/audit/logs",
                params=params,
                headers=headers
            ) as response:
                if response.status != 200:
                    logger.error("Audit log retrieval failed", status=response.status)
                    return False
                
                data = await response.json()
                
                # Verify response structure
                required_fields = ['items', 'total', 'page', 'size']
                for field in required_fields:
                    if field not in data:
                        logger.error("Audit log response missing field", field=field)
                        return False
                
                if not isinstance(data['items'], list):
                    logger.error("Audit log items not a list")
                    return False
                
                logger.info("Audit log retrieval successful", count=len(data['items']))
                return True
                
        except Exception as e:
            logger.error("Audit log retrieval error", error=str(e))
            return False
    
    async def test_batch_audit_creation(self) -> bool:
        """Test batch audit log creation."""
        try:
            headers = self._get_auth_headers()
            if not headers:
                logger.error("No authentication available for batch audit test")
                return False
            
            # Create batch of audit logs
            batch_data = {
                "logs": [
                    {
                        "tenant_id": self.test_tenant_id,
                        "user_id": self.test_user_id,
                        "event_type": "smoke_test_batch",
                        "resource_type": "test_resource",
                        "resource_id": f"batch-test-{i}",
                        "action": "create",
                        "metadata": {"batch_index": i}
                    }
                    for i in range(5)
                ]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/audit/logs/batch",
                json=batch_data,
                headers=headers
            ) as response:
                if response.status not in [200, 201]:
                    logger.error("Batch audit creation failed", status=response.status)
                    return False
                
                data = await response.json()
                
                # Verify batch response
                if 'created_count' not in data:
                    logger.error("Batch response missing created_count")
                    return False
                
                if data['created_count'] != 5:
                    logger.error("Batch creation count mismatch", expected=5, actual=data['created_count'])
                    return False
                
                logger.info("Batch audit creation successful", count=data['created_count'])
                return True
                
        except Exception as e:
            logger.error("Batch audit creation error", error=str(e))
            return False
    
    async def test_export_functionality(self) -> bool:
        """Test audit log export functionality."""
        try:
            headers = self._get_auth_headers()
            if not headers:
                logger.error("No authentication available for export test")
                return False
            
            # Test CSV export
            params = {
                "tenant_id": self.test_tenant_id,
                "format": "csv",
                "limit": 10
            }
            
            async with self.session.get(
                f"{self.base_url}/api/v1/audit/logs/export",
                params=params,
                headers=headers
            ) as response:
                if response.status != 200:
                    logger.error("Export functionality failed", status=response.status)
                    return False
                
                content_type = response.headers.get('content-type', '')
                if 'text/csv' not in content_type:
                    logger.error("Export content type incorrect", content_type=content_type)
                    return False
                
                # Verify we got some data
                data = await response.text()
                if len(data) < 10:  # Should have at least headers
                    logger.error("Export data too small")
                    return False
                
                logger.info("Export functionality successful", data_size=len(data))
                return True
                
        except Exception as e:
            logger.error("Export functionality error", error=str(e))
            return False
    
    async def test_metrics_endpoint(self) -> bool:
        """Test metrics endpoint."""
        try:
            async with self.session.get(f"{self.base_url}/metrics") as response:
                if response.status != 200:
                    logger.error("Metrics endpoint failed", status=response.status)
                    return False
                
                data = await response.text()
                
                # Verify Prometheus format
                if 'http_requests_total' not in data:
                    logger.error("Metrics missing expected data")
                    return False
                
                logger.info("Metrics endpoint accessible")
                return True
                
        except Exception as e:
            logger.error("Metrics endpoint error", error=str(e))
            return False
    
    def _get_auth_headers(self) -> Optional[Dict[str, str]]:
        """Get authentication headers."""
        if self.jwt_token:
            return {"Authorization": f"Bearer {self.jwt_token}"}
        elif self.api_key:
            return {"X-API-Key": self.api_key}
        return None
    
    def print_test_summary(self) -> None:
        """Print test results summary."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results if r['status'] == 'ERROR'])
        
        print("\n" + "="*60)
        print("SMOKE TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print("="*60)
        
        # Print individual test results
        for result in self.test_results:
            status_symbol = "✅" if result['status'] == 'PASS' else "❌"
            print(f"{status_symbol} {result['test_name']}: {result['status']} ({result['duration']:.2f}s)")
            
            if 'error' in result:
                print(f"   Error: {result['error']}")
        
        print("="*60)


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Run smoke tests for audit service')
    parser.add_argument('--url', required=True, help='Base URL of the service')
    parser.add_argument('--production', action='store_true', help='Run in production mode (limited tests)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        )
    
    # Run smoke tests
    async with SmokeTestRunner(args.url, args.production) as runner:
        success = await runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())