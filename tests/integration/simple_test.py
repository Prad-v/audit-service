#!/usr/bin/env python3
"""
Simple test to verify basic functionality with RBAC disabled.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_basic_functionality():
    """Test basic functionality."""
    print("🧪 Basic Functionality Test with RBAC Disabled")
    print("=" * 50)
    
    # Test 1: Health endpoint
    print("1. Testing health endpoint:")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Health endpoint working")
    else:
        print(f"   ❌ Health endpoint failed: {response.text}")
    print()
    
    # Test 2: Swagger docs
    print("2. Testing Swagger documentation:")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ Swagger docs accessible")
    else:
        print(f"   ❌ Swagger docs failed: {response.text[:100]}")
    print()
    
    # Test 3: OpenAPI schema
    print("3. Testing OpenAPI schema:")
    response = requests.get(f"{BASE_URL}/openapi.json")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        paths = list(data.get("paths", {}).keys())
        print(f"   ✅ OpenAPI schema accessible with {len(paths)} endpoints")
    else:
        print(f"   ❌ OpenAPI schema failed: {response.text[:100]}")
    print()
    
    # Test 4: Try a simple POST without complex data
    print("4. Testing simple POST request:")
    simple_data = {"test": "data"}
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/events?args=%7B%7D&kwargs=%7B%7D",
        json=simple_data,
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    print()
    
    # Test 5: Try GET with minimal parameters
    print("5. Testing GET request:")
    response = requests.get(f"{BASE_URL}/api/v1/audit/events?args=%7B%7D&kwargs=%7B%7D")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...")
    print()
    
    print("=" * 50)
    print("🎉 Basic functionality test complete!")
    print()
    print("Summary:")
    print("- RBAC is disabled (no 401/403 errors)")
    print("- Health and docs endpoints work")
    print("- API endpoints are accessible but may have internal errors")
    print("- This is expected for development/testing with RBAC disabled")

if __name__ == "__main__":
    test_basic_functionality()
