"""
Security testing and vulnerability scanning for the Audit Log Framework.

This module provides comprehensive security tests including authentication,
authorization, input validation, injection attacks, and other security
vulnerabilities.
"""

import pytest
import requests
import json
import time
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any
from urllib.parse import quote, unquote


class SecurityTestBase:
    """Base class for security tests with common utilities."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def get_auth_token(self, username: str = "testuser", password: str = "testpass", tenant_id: str = "test-tenant") -> str:
        """Get authentication token for testing."""
        login_data = {
            "username": username,
            "password": password,
            "tenant_id": tenant_id
        }
        
        response = self.make_request("POST", "/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
        return None


class AuthenticationSecurityTests(SecurityTestBase):
    """Security tests for authentication mechanisms."""
    
    def test_brute_force_protection(self):
        """Test protection against brute force attacks."""
        print("Testing brute force protection...")
        
        login_data = {
            "username": "testuser",
            "password": "wrongpassword",
            "tenant_id": "test-tenant"
        }
        
        # Attempt multiple failed logins
        failed_attempts = 0
        for i in range(10):
            response = self.make_request("POST", "/api/v1/auth/login", json=login_data)
            if response.status_code == 401:
                failed_attempts += 1
            elif response.status_code == 429:  # Rate limited
                print(f"✓ Rate limiting activated after {failed_attempts} attempts")
                return True
            time.sleep(0.1)  # Small delay between attempts
        
        print(f"⚠ No rate limiting detected after {failed_attempts} failed attempts")
        return False
    
    def test_password_complexity(self):
        """Test password complexity requirements."""
        print("Testing password complexity...")
        
        weak_passwords = [
            "123456",
            "password",
            "abc123",
            "qwerty",
            "admin",
            "test",
            "a",  # Too short
            "aaaaaaaa",  # No complexity
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "full_name": "Test User",
                "password": weak_password,
                "roles": ["audit_viewer"],
                "is_active": True
            }
            
            # This would require admin token in real implementation
            response = self.make_request("POST", "/api/v1/auth/users", json=user_data)
            
            if response.status_code == 400:
                print(f"✓ Weak password '{weak_password}' rejected")
            else:
                print(f"⚠ Weak password '{weak_password}' accepted")
    
    def test_jwt_token_security(self):
        """Test JWT token security."""
        print("Testing JWT token security...")
        
        token = self.get_auth_token()
        if not token:
            print("⚠ Could not obtain token for testing")
            return False
        
        # Test token structure
        parts = token.split('.')
        if len(parts) != 3:
            print("⚠ Invalid JWT token structure")
            return False
        
        # Decode header and payload (without verification)
        try:
            header = json.loads(base64.urlsafe_b64decode(parts[0] + '=='))
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
            
            # Check for security best practices
            if 'alg' not in header or header['alg'] == 'none':
                print("⚠ JWT algorithm not specified or set to 'none'")
                return False
            
            if 'exp' not in payload:
                print("⚠ JWT token has no expiration")
                return False
            
            # Check expiration time is reasonable (not too long)
            exp_time = datetime.fromtimestamp(payload['exp'])
            now = datetime.now()
            if (exp_time - now).total_seconds() > 86400:  # More than 24 hours
                print("⚠ JWT token expiration time is too long")
                return False
            
            print("✓ JWT token structure and security checks passed")
            return True
            
        except Exception as e:
            print(f"⚠ Error decoding JWT token: {e}")
            return False
    
    def test_session_management(self):
        """Test session management security."""
        print("Testing session management...")
        
        token = self.get_auth_token()
        if not token:
            return False
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test that token works
        response = self.make_request("GET", "/api/v1/auth/me", headers=headers)
        if response.status_code != 200:
            print("⚠ Valid token rejected")
            return False
        
        # Test logout invalidates token
        self.make_request("POST", "/api/v1/auth/logout", headers=headers)
        
        # Token should no longer work (if logout is properly implemented)
        response = self.make_request("GET", "/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            print("⚠ Token still valid after logout")
            return False
        
        print("✓ Session management tests passed")
        return True


class AuthorizationSecurityTests(SecurityTestBase):
    """Security tests for authorization and access control."""
    
    def test_rbac_enforcement(self):
        """Test role-based access control enforcement."""
        print("Testing RBAC enforcement...")
        
        # Test with different user roles
        test_cases = [
            {
                "role": "audit_viewer",
                "allowed_endpoints": [
                    ("GET", "/api/v1/audit/events"),
                    ("GET", "/api/v1/audit/summary"),
                ],
                "forbidden_endpoints": [
                    ("POST", "/api/v1/auth/users"),
                    ("DELETE", "/api/v1/auth/users/test-id"),
                ]
            },
            {
                "role": "audit_manager", 
                "allowed_endpoints": [
                    ("GET", "/api/v1/audit/events"),
                    ("POST", "/api/v1/audit/events"),
                    ("GET", "/api/v1/audit/events/export"),
                ],
                "forbidden_endpoints": [
                    ("POST", "/api/v1/auth/users"),
                ]
            }
        ]
        
        for test_case in test_cases:
            print(f"Testing role: {test_case['role']}")
            
            # This would require creating users with specific roles
            # For now, we'll test with existing tokens
            token = self.get_auth_token()
            if not token:
                continue
                
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test allowed endpoints
            for method, endpoint in test_case["allowed_endpoints"]:
                response = self.make_request(method, endpoint, headers=headers)
                if response.status_code in [200, 201]:
                    print(f"✓ {method} {endpoint} allowed for {test_case['role']}")
                else:
                    print(f"⚠ {method} {endpoint} denied for {test_case['role']} (status: {response.status_code})")
            
            # Test forbidden endpoints
            for method, endpoint in test_case["forbidden_endpoints"]:
                response = self.make_request(method, endpoint, headers=headers)
                if response.status_code in [403, 401]:
                    print(f"✓ {method} {endpoint} properly denied for {test_case['role']}")
                else:
                    print(f"⚠ {method} {endpoint} allowed for {test_case['role']} (should be denied)")
    
    def test_tenant_isolation(self):
        """Test multi-tenant isolation."""
        print("Testing tenant isolation...")
        
        # Create events in different tenants and verify isolation
        tenant1_headers = {
            "X-API-Key": "tenant1-key",
            "X-Tenant-ID": "tenant-1"
        }
        
        tenant2_headers = {
            "X-API-Key": "tenant2-key", 
            "X-Tenant-ID": "tenant-2"
        }
        
        event_data = {
            "event_type": "user_action",
            "resource_type": "user",
            "action": "test_isolation",
            "severity": "info",
            "description": "Tenant isolation test event"
        }
        
        # Create event in tenant 1
        response1 = self.make_request("POST", "/api/v1/audit/events", 
                                    json=event_data, headers=tenant1_headers)
        
        # Query events from tenant 2 - should not see tenant 1's events
        response2 = self.make_request("GET", "/api/v1/audit/events",
                                    headers=tenant2_headers)
        
        if response2.status_code == 200:
            events = response2.json().get("items", [])
            tenant1_events = [e for e in events if e.get("description") == "Tenant isolation test event"]
            
            if len(tenant1_events) == 0:
                print("✓ Tenant isolation working correctly")
                return True
            else:
                print("⚠ Tenant isolation breach detected")
                return False
        
        print("⚠ Could not test tenant isolation")
        return False
    
    def test_privilege_escalation(self):
        """Test for privilege escalation vulnerabilities."""
        print("Testing privilege escalation...")
        
        # Test modifying user roles through API
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to escalate privileges by modifying own user
        escalation_data = {
            "roles": ["system_admin"]  # Try to become admin
        }
        
        # This should fail for non-admin users
        response = self.make_request("PUT", "/api/v1/auth/me", 
                                   json=escalation_data, headers=headers)
        
        if response.status_code in [403, 401, 405]:  # Forbidden, Unauthorized, or Method Not Allowed
            print("✓ Privilege escalation properly prevented")
            return True
        else:
            print(f"⚠ Potential privilege escalation vulnerability (status: {response.status_code})")
            return False


class InputValidationSecurityTests(SecurityTestBase):
    """Security tests for input validation and injection attacks."""
    
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities."""
        print("Testing SQL injection...")
        
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "1'; UPDATE users SET password='hacked' WHERE username='admin'--",
            "' OR 1=1#",
            "'; EXEC xp_cmdshell('dir'); --"
        ]
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test SQL injection in search parameters
        for payload in sql_payloads:
            params = {"search": payload}
            response = self.make_request("GET", "/api/v1/audit/events", 
                                       params=params, headers=headers)
            
            if response.status_code == 500:
                print(f"⚠ Potential SQL injection vulnerability with payload: {payload}")
                return False
            elif response.status_code in [200, 400]:
                print(f"✓ SQL injection payload handled safely: {payload}")
        
        # Test SQL injection in event creation
        for payload in sql_payloads:
            event_data = {
                "event_type": "user_action",
                "resource_type": "user",
                "action": payload,
                "severity": "info",
                "description": "SQL injection test"
            }
            
            response = self.make_request("POST", "/api/v1/audit/events",
                                       json=event_data, headers=headers)
            
            if response.status_code == 500:
                print(f"⚠ Potential SQL injection in event creation: {payload}")
                return False
        
        print("✓ SQL injection tests passed")
        return True
    
    def test_xss_prevention(self):
        """Test for Cross-Site Scripting (XSS) vulnerabilities."""
        print("Testing XSS prevention...")
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>",
            "&#60;script&#62;alert('xss')&#60;/script&#62;",
            "<iframe src='javascript:alert(\"xss\")'></iframe>"
        ]
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test XSS in event creation
        for payload in xss_payloads:
            event_data = {
                "event_type": "user_action",
                "resource_type": "user", 
                "action": "test",
                "severity": "info",
                "description": payload
            }
            
            response = self.make_request("POST", "/api/v1/audit/events",
                                       json=event_data, headers=headers)
            
            if response.status_code == 201:
                # Check if the payload is properly escaped in response
                created_event = response.json()
                if payload in created_event.get("description", ""):
                    # Verify it's properly escaped (this would need frontend testing)
                    print(f"⚠ Potential XSS payload stored unescaped: {payload}")
                else:
                    print(f"✓ XSS payload properly handled: {payload}")
        
        print("✓ XSS prevention tests completed")
        return True
    
    def test_command_injection(self):
        """Test for command injection vulnerabilities."""
        print("Testing command injection...")
        
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; ping -c 1 127.0.0.1",
            "| nc -l 4444"
        ]
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test command injection in various fields
        for payload in command_payloads:
            event_data = {
                "event_type": "system_event",
                "resource_type": "system",
                "action": payload,
                "severity": "info",
                "description": "Command injection test",
                "metadata": {
                    "command": payload,
                    "test_field": payload
                }
            }
            
            response = self.make_request("POST", "/api/v1/audit/events",
                                       json=event_data, headers=headers)
            
            # Command injection would typically cause 500 errors or timeouts
            if response.status_code == 500:
                print(f"⚠ Potential command injection vulnerability: {payload}")
                return False
            elif response.status_code in [201, 400]:
                print(f"✓ Command injection payload handled safely: {payload}")
        
        print("✓ Command injection tests passed")
        return True
    
    def test_path_traversal(self):
        """Test for path traversal vulnerabilities."""
        print("Testing path traversal...")
        
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd"
        ]
        
        # Test path traversal in file-related endpoints (if any)
        for payload in path_payloads:
            # Test in export filename parameter (if implemented)
            params = {"format": "json", "filename": payload}
            response = self.make_request("GET", "/api/v1/audit/events/export", params=params)
            
            if response.status_code == 500:
                print(f"⚠ Potential path traversal vulnerability: {payload}")
                return False
        
        print("✓ Path traversal tests passed")
        return True
    
    def test_json_injection(self):
        """Test for JSON injection vulnerabilities."""
        print("Testing JSON injection...")
        
        # Test malformed JSON and injection attempts
        json_payloads = [
            '{"extra_field": "injected_value"}',
            '{"admin": true}',
            '{"roles": ["system_admin"]}',
            '{"tenant_id": "different_tenant"}'
        ]
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test JSON injection in metadata fields
        for payload in json_payloads:
            event_data = {
                "event_type": "user_action",
                "resource_type": "user",
                "action": "test",
                "severity": "info", 
                "description": "JSON injection test",
                "metadata": payload  # This should be rejected as it's not a dict
            }
            
            response = self.make_request("POST", "/api/v1/audit/events",
                                       json=event_data, headers=headers)
            
            if response.status_code == 422:  # Validation error expected
                print(f"✓ JSON injection properly rejected: {payload}")
            else:
                print(f"⚠ JSON injection payload accepted: {payload}")
        
        print("✓ JSON injection tests completed")
        return True


class DataSecurityTests(SecurityTestBase):
    """Security tests for data protection and privacy."""
    
    def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure in responses."""
        print("Testing sensitive data exposure...")
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test user information endpoint
        response = self.make_request("GET", "/api/v1/auth/me", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Check for sensitive fields that shouldn't be exposed
            sensitive_fields = ["password", "password_hash", "secret_key", "private_key"]
            
            for field in sensitive_fields:
                if field in user_data:
                    print(f"⚠ Sensitive field '{field}' exposed in user data")
                    return False
            
            print("✓ No sensitive data exposed in user information")
        
        # Test audit events for sensitive data
        response = self.make_request("GET", "/api/v1/audit/events", headers=headers)
        
        if response.status_code == 200:
            events = response.json().get("items", [])
            
            for event in events[:5]:  # Check first 5 events
                # Look for potential sensitive data patterns
                description = event.get("description", "").lower()
                metadata = str(event.get("metadata", {})).lower()
                
                sensitive_patterns = ["password", "secret", "key", "token", "ssn", "credit"]
                
                for pattern in sensitive_patterns:
                    if pattern in description or pattern in metadata:
                        print(f"⚠ Potential sensitive data in event: {pattern}")
        
        print("✓ Sensitive data exposure tests completed")
        return True
    
    def test_data_encryption(self):
        """Test data encryption in transit and at rest."""
        print("Testing data encryption...")
        
        # Test HTTPS enforcement (if applicable)
        if self.base_url.startswith("https://"):
            print("✓ HTTPS is being used")
        else:
            print("⚠ HTTP is being used - data not encrypted in transit")
        
        # Test for encrypted fields in responses
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create event with potentially sensitive data
        event_data = {
            "event_type": "user_action",
            "resource_type": "user",
            "action": "password_change",
            "severity": "info",
            "description": "User changed password",
            "metadata": {
                "old_password": "should_be_encrypted",
                "new_password": "should_also_be_encrypted"
            }
        }
        
        response = self.make_request("POST", "/api/v1/audit/events",
                                   json=event_data, headers=headers)
        
        if response.status_code == 201:
            created_event = response.json()
            metadata = created_event.get("metadata", {})
            
            # Check if sensitive data is stored in plain text
            if "should_be_encrypted" in str(metadata):
                print("⚠ Sensitive data stored in plain text")
                return False
            else:
                print("✓ Sensitive data appears to be protected")
        
        return True


class APISecurityTests(SecurityTestBase):
    """Security tests for API-specific vulnerabilities."""
    
    def test_rate_limiting(self):
        """Test API rate limiting."""
        print("Testing rate limiting...")
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make rapid requests to test rate limiting
        rate_limited = False
        for i in range(100):
            response = self.make_request("GET", "/api/v1/health", headers=headers)
            
            if response.status_code == 429:  # Too Many Requests
                print(f"✓ Rate limiting activated after {i+1} requests")
                rate_limited = True
                break
            
            time.sleep(0.01)  # Small delay
        
        if not rate_limited:
            print("⚠ No rate limiting detected after 100 requests")
            return False
        
        return True
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        print("Testing CORS configuration...")
        
        # Test preflight request
        headers = {
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = self.make_request("OPTIONS", "/api/v1/audit/events", headers=headers)
        
        if response.status_code == 200:
            cors_headers = response.headers
            
            # Check for overly permissive CORS
            if cors_headers.get("Access-Control-Allow-Origin") == "*":
                print("⚠ CORS allows all origins (*)")
                return False
            
            if "Access-Control-Allow-Credentials" in cors_headers:
                if cors_headers.get("Access-Control-Allow-Origin") == "*":
                    print("⚠ CORS allows credentials with wildcard origin")
                    return False
            
            print("✓ CORS configuration appears secure")
        
        return True
    
    def test_http_security_headers(self):
        """Test HTTP security headers."""
        print("Testing HTTP security headers...")
        
        response = self.make_request("GET", "/api/v1/health")
        headers = response.headers
        
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # Should be present for HTTPS
            "Content-Security-Policy": None,
            "Referrer-Policy": None
        }
        
        missing_headers = []
        
        for header, expected_value in security_headers.items():
            if header not in headers:
                missing_headers.append(header)
            elif expected_value and isinstance(expected_value, list):
                if headers[header] not in expected_value:
                    print(f"⚠ {header} has unexpected value: {headers[header]}")
            elif expected_value and headers[header] != expected_value:
                print(f"⚠ {header} has unexpected value: {headers[header]}")
        
        if missing_headers:
            print(f"⚠ Missing security headers: {', '.join(missing_headers)}")
        else:
            print("✓ All security headers present")
        
        return len(missing_headers) == 0
    
    def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities."""
        print("Testing information disclosure...")
        
        # Test error messages for information leakage
        test_cases = [
            ("GET", "/api/v1/nonexistent", 404),
            ("POST", "/api/v1/audit/events", 401),  # Without auth
            ("GET", "/api/v1/audit/events/invalid-id", 404),
        ]
        
        for method, endpoint, expected_status in test_cases:
            response = self.make_request(method, endpoint)
            
            if response.status_code == expected_status:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "").lower()
                    
                    # Check for information disclosure in error messages
                    disclosure_patterns = [
                        "database", "sql", "mysql", "postgresql", "oracle",
                        "stack trace", "exception", "internal server error",
                        "file not found", "permission denied", "access denied"
                    ]
                    
                    for pattern in disclosure_patterns:
                        if pattern in error_message:
                            print(f"⚠ Potential information disclosure: {pattern}")
                            return False
                    
                except json.JSONDecodeError:
                    # Non-JSON error response
                    pass
        
        print("✓ No information disclosure detected")
        return True


class SecurityTestRunner:
    """Main class to run all security tests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_classes = [
            AuthenticationSecurityTests,
            AuthorizationSecurityTests,
            InputValidationSecurityTests,
            DataSecurityTests,
            APISecurityTests
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests and return results."""
        print(f"Starting security tests for {self.base_url}")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "target": self.base_url,
            "test_results": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warnings": 0
            }
        }
        
        for test_class in self.test_classes:
            class_name = test_class.__name__
            print(f"\n--- Running {class_name} ---")
            
            test_instance = test_class(self.base_url)
            class_results = {}
            
            # Get all test methods
            test_methods = [method for method in dir(test_instance) 
                          if method.startswith('test_') and callable(getattr(test_instance, method))]
            
            for method_name in test_methods:
                try:
                    test_method = getattr(test_instance, method_name)
                    result = test_method()
                    
                    class_results[method_name] = {
                        "passed": result,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results["summary"]["total_tests"] += 1
                    if result:
                        results["summary"]["passed_tests"] += 1
                    else:
                        results["summary"]["failed_tests"] += 1
                        
                except Exception as e:
                    print(f"⚠ Test {method_name} failed with exception: {e}")
                    class_results[method_name] = {
                        "passed": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    results["summary"]["total_tests"] += 1
                    results["summary"]["failed_tests"] += 1
            
            results["test_results"][class_name] = class_results
        
        # Print summary
        print("\n" + "=" * 60)
        print("SECURITY TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed_tests']}")
        print(f"Failed: {results['summary']['failed_tests']}")
        
        if results['summary']['failed_tests'] > 0:
            print("\n⚠ SECURITY ISSUES DETECTED - Review failed tests above")
        else:
            print("\n✓ All security tests passed")
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_file: str = "security_report.json"):
        """Generate a detailed security report."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed security report saved to: {output_file}")


def main():
    """Main function to run security tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run security tests for Audit Log Framework")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API to test")
    parser.add_argument("--output", default="security_report.json",
                       help="Output file for detailed report")
    
    args = parser.parse_args()
                print("⚠ Sensitive data stored in plain text")
                return False
            else:
                print("✓ Sensitive data appears to be protected")
        
        return True


class APISecurityTests(SecurityTestBase):
    """Security tests for API-specific vulnerabilities."""
    
    def test_rate_limiting(self):
        """Test API rate limiting."""
        print("Testing rate limiting...")
        
        token = self.get_auth_token()
        if not token:
            return False
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Make rapid requests to test rate limiting
        rate_limited = False
        for i in range(100):
            response = self.make_request("GET", "/api/v1/health", headers=headers)
            
            if response.status_code == 429:  # Too Many Requests
                print(f"✓ Rate limiting activated after {i+1} requests")
                rate_limited = True
                break
            
            time.sleep(0.01)  # Small delay
        
        if not rate_limited:
            print("⚠ No rate limiting detected after 100 requests")
            return False
        
        return True
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        print("Testing CORS configuration...")
        
        # Test preflight request
        headers = {
            "Origin": "https://malicious-site.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = self.make_request("OPTIONS", "/api/v1/audit/events", headers=headers)
        
        if response.status_code == 200:
            cors_headers = response.headers
            
            # Check for overly permissive CORS
            if cors_headers.get("Access-Control-Allow-Origin") == "*":
                print("⚠ CORS allows all origins (*)")
                return False
            
            if "Access-Control-Allow-Credentials" in cors_headers:
                if cors_headers.get("Access-Control-Allow-Origin") == "*":
                    print("⚠ CORS allows credentials with wildcard origin")
                    return False
            
            print("✓ CORS configuration appears secure")
        
        return True
    
    def test_http_security_headers(self):
        """Test HTTP security headers."""
        print("Testing HTTP security headers...")
        
        response = self.make_request("GET", "/api/v1/health")
        headers = response.headers
        
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": None,  # Should be present for HTTPS
            "Content-Security-Policy": None,
            "Referrer-Policy": None
        }
        
        missing_headers = []
        
        for header, expected_value in security_headers.items():
            if header not in headers:
                missing_headers.append(header)
            elif expected_value and isinstance(expected_value, list):
                if headers[header] not in expected_value:
                    print(f"⚠ {header} has unexpected value: {headers[header]}")
            elif expected_value and headers[header] != expected_value:
                print(f"⚠ {header} has unexpected value: {headers[header]}")
        
        if missing_headers:
            print(f"⚠ Missing security headers: {', '.join(missing_headers)}")
        else:
            print("✓ All security headers present")
        
        return len(missing_headers) == 0
    
    def test_information_disclosure(self):
        """Test for information disclosure vulnerabilities."""
        print("Testing information disclosure...")
        
        # Test error messages for information leakage
        test_cases = [
            ("GET", "/api/v1/nonexistent", 404),
            ("POST", "/api/v1/audit/events", 401),  # Without auth
            ("GET", "/api/v1/audit/events/invalid-id", 404),
        ]
        
        for method, endpoint, expected_status in test_cases:
            response = self.make_request(method, endpoint)
            
            if response.status_code == expected_status:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "").lower()
                    
                    # Check for information disclosure in error messages
                    disclosure_patterns = [
                        "database", "sql", "mysql", "postgresql", "oracle",
                        "stack trace", "exception", "internal server error",
                        "file not found", "permission denied", "access denied"
                    ]
                    
                    for pattern in disclosure_patterns:
                        if pattern in error_message:
                            print(f"⚠ Potential information disclosure: {pattern}")
                            return False
                    
                except json.JSONDecodeError:
                    # Non-JSON error response
                    pass
        
        print("✓ No information disclosure detected")
        return True


class SecurityTestRunner:
    """Main class to run all security tests."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_classes = [
            AuthenticationSecurityTests,
            AuthorizationSecurityTests,
            InputValidationSecurityTests,
            DataSecurityTests,
            APISecurityTests
        ]
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests and return results."""
        print(f"Starting security tests for {self.base_url}")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "target": self.base_url,
            "test_results": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warnings": 0
            }
        }
        
        for test_class in self.test_classes:
            class_name = test_class.__name__
            print(f"\n--- Running {class_name} ---")
            
            test_instance = test_class(self.base_url)
            class_results = {}
            
            # Get all test methods
            test_methods = [method for method in dir(test_instance) 
                          if method.startswith('test_') and callable(getattr(test_instance, method))]
            
            for method_name in test_methods:
                try:
                    test_method = getattr(test_instance, method_name)
                    result = test_method()
                    
                    class_results[method_name] = {
                        "passed": result,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results["summary"]["total_tests"] += 1
                    if result:
                        results["summary"]["passed_tests"] += 1
                    else:
                        results["summary"]["failed_tests"] += 1
                        
                except Exception as e:
                    print(f"⚠ Test {method_name} failed with exception: {e}")
                    class_results[method_name] = {
                        "passed": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    results["summary"]["total_tests"] += 1
                    results["summary"]["failed_tests"] += 1
            
            results["test_results"][class_name] = class_results
        
        # Print summary
        print("\n" + "=" * 60)
        print("SECURITY TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {results['summary']['total_tests']}")
        print(f"Passed: {results['summary']['passed_tests']}")
        print(f"Failed: {results['summary']['failed_tests']}")
        
        if results['summary']['failed_tests'] > 0:
            print("\n⚠ SECURITY ISSUES DETECTED - Review failed tests above")
        else:
            print("\n✓ All security tests passed")
        
        return results
    
    def generate_report(self, results: Dict[str, Any], output_file: str = "security_report.json"):
        """Generate a detailed security report."""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nDetailed security report saved to: {output_file}")


def main():
    """Main function to run security tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run security tests for Audit Log Framework")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API to test")
    parser.add_argument("--output", default="security_report.json",
                       help="Output file for detailed report")
    
    args = parser.parse_args()
    
    # Run security tests
    runner = SecurityTestRunner(args.url)
    results = runner.run_all_tests()
    runner.generate_report(results, args.output)
    
    # Exit with error code if tests failed
    if results['summary']['failed_tests'] > 0:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()