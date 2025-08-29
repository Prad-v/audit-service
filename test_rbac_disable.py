#!/usr/bin/env python3
"""
Test script to demonstrate RBAC disable functionality.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_with_auth_enabled():
    """Test with authentication enabled (default)."""
    print("🔒 Testing with Authentication ENABLED (default)")
    print("=" * 50)
    
    # Test health endpoint (public)
    print("1. Testing health endpoint (public):")
    response = requests.get(f"{BASE_URL}/health/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}\n")
    
    # Test protected endpoint without auth
    print("2. Testing protected endpoint without authentication:")
    response = requests.get(f"{BASE_URL}/api/v1/audit/events")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...\n")
    
    # Test with invalid token
    print("3. Testing protected endpoint with invalid token:")
    headers = {"Authorization": "Bearer invalid-token"}
    response = requests.get(f"{BASE_URL}/api/v1/audit/events", headers=headers)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...\n")

def test_with_auth_disabled():
    """Test with authentication disabled."""
    print("🔓 Testing with Authentication DISABLED")
    print("=" * 50)
    
    # Update environment variable
    print("Setting RBAC_AUTHENTICATION_DISABLED=true...")
    
    # Test protected endpoint without auth (should work now)
    print("1. Testing protected endpoint without authentication:")
    response = requests.get(f"{BASE_URL}/api/v1/audit/events")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...\n")

def test_with_authz_disabled():
    """Test with authorization disabled."""
    print("🔓 Testing with Authorization DISABLED")
    print("=" * 50)
    
    # Update environment variable
    print("Setting RBAC_AUTHORIZATION_DISABLED=true...")
    
    # Test protected endpoint without auth (should work now)
    print("1. Testing protected endpoint without authentication:")
    response = requests.get(f"{BASE_URL}/api/v1/audit/events")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text[:200]}...\n")

def main():
    """Main test function."""
    print("🧪 RBAC Disable Functionality Test")
    print("=" * 60)
    
    # Test with default settings
    test_with_auth_enabled()
    
    print("\n" + "=" * 60)
    print("To test with RBAC disabled, update docker-compose.yml:")
    print("  RBAC_AUTHENTICATION_DISABLED=true")
    print("  RBAC_AUTHORIZATION_DISABLED=true")
    print("Then restart the services: docker-compose restart api")
    print("=" * 60)

if __name__ == "__main__":
    main()
