#!/usr/bin/env python3
"""
Demonstration of RBAC Disable Functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health endpoint (always public)."""
    print("🏥 Testing Health Endpoint (Public)")
    print("=" * 40)
    
    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()

def test_protected_endpoint_with_auth_disabled():
    """Test protected endpoint with authentication disabled."""
    print("🔓 Testing Protected Endpoint with Authentication DISABLED")
    print("=" * 60)
    
    # Test /api/v1/auth/me endpoint
    print("1. Testing /api/v1/auth/me endpoint:")
    response = requests.get(f"{BASE_URL}/api/v1/auth/me")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    print()
    
    # Test /api/v1/audit/events endpoint
    print("2. Testing /api/v1/audit/events endpoint:")
    response = requests.get(f"{BASE_URL}/api/v1/audit/events")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    print()

def test_swagger_docs():
    """Test Swagger documentation."""
    print("📚 Testing Swagger Documentation")
    print("=" * 40)
    
    # Test /docs endpoint
    print("1. Testing /docs endpoint:")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Swagger UI is accessible")
    else:
        print(f"   ❌ Swagger UI not accessible: {response.text[:100]}...")
    print()
    
    # Test /openapi.json endpoint
    print("2. Testing /openapi.json endpoint:")
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        paths = list(data.get("paths", {}).keys())
        print(f"   ✅ OpenAPI schema accessible with {len(paths)} endpoints")
        print(f"   Sample endpoints: {paths[:5]}")
    else:
        print(f"   ❌ OpenAPI schema not accessible: {response.text[:100]}...")
    print()

def show_configuration():
    """Show current RBAC configuration."""
    print("⚙️  Current RBAC Configuration")
    print("=" * 40)
    
    # Check environment variables
    print("Environment Variables:")
    print("  RBAC_AUTHENTICATION_DISABLED=true")
    print("  RBAC_AUTHORIZATION_DISABLED=true")
    print()
    
    print("Expected Behavior:")
    print("  ✅ Authentication is disabled - no login required")
    print("  ✅ Authorization is disabled - no permission checks")
    print("  ✅ All endpoints should be accessible without tokens")
    print("  ✅ System defaults are used for user context")
    print()

def main():
    """Main demonstration function."""
    print("🧪 RBAC Disable Functionality Demonstration")
    print("=" * 70)
    print()
    
    show_configuration()
    test_health_endpoint()
    test_swagger_docs()
    test_protected_endpoint_with_auth_disabled()
    
    print("=" * 70)
    print("🎉 RBAC Disable Demonstration Complete!")
    print()
    print("To re-enable RBAC, update docker-compose.yml:")
    print("  RBAC_AUTHENTICATION_DISABLED=false")
    print("  RBAC_AUTHORIZATION_DISABLED=false")
    print("Then restart: docker-compose restart api")
    print("=" * 70)

if __name__ == "__main__":
    main()
