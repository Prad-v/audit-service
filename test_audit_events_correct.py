#!/usr/bin/env python3
"""
Test script to post and retrieve audit events with correct API format.
"""

import requests
import json
import time
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"

def test_post_audit_event():
    """Test posting an audit event with correct format."""
    print("📝 Testing Audit Event Creation")
    print("=" * 40)
    
    # Sample audit event data using the correct model
    event_data = {
        "event_type": "user_login",
        "user_id": "test_user_123",
        "session_id": "session_456",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Test Browser)",
        "resource_type": "auth",
        "resource_id": "login_session_456",
        "action": "login",
        "status": "success",
        "request_data": {
            "login_method": "password",
            "username": "testuser"
        },
        "response_data": {
            "session_duration": 3600
        },
        "metadata": {
            "login_method": "password",
            "session_duration": 3600
        },
        "tenant_id": "default",
        "service_name": "audit-service",
        "correlation_id": "test_correlation_123",
        "retention_period_days": 90
    }
    
    print("Event data to post:")
    print(json.dumps(event_data, indent=2))
    print()
    
    # Post the event (no query parameters needed)
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/events",
        json=event_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"POST /api/v1/audit/events")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def test_get_audit_events():
    """Test retrieving audit events with correct format."""
    print("📋 Testing Audit Event Retrieval")
    print("=" * 40)
    
    # Get all events with proper query parameters
    params = {
        "page": 1,
        "size": 10,
        "sort_by": "timestamp",
        "sort_order": "desc"
    }
    
    response = requests.get(f"{BASE_URL}/api/v1/audit/events", params=params)
    
    print(f"GET /api/v1/audit/events")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response: {response.text[:500]}...")
    else:
        print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def test_get_specific_event(event_id):
    """Test retrieving a specific audit event."""
    print(f"🔍 Testing Specific Event Retrieval (ID: {event_id})")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/v1/audit/events/{event_id}")
    
    print(f"GET /api/v1/audit/events/{event_id}")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response: {response.text[:500]}...")
    else:
        print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def test_batch_events():
    """Test posting multiple events in batch with correct format."""
    print("📦 Testing Batch Event Creation")
    print("=" * 40)
    
    # Sample batch events using the correct model
    batch_data = {
        "events": [
            {
                "event_type": "file_access",
                "user_id": "user_1",
                "session_id": "session_789",
                "ip_address": "192.168.1.101",
                "user_agent": "Mozilla/5.0 (Test Browser)",
                "resource_type": "file",
                "resource_id": "file_123",
                "action": "read",
                "status": "success",
                "request_data": {"file_path": "/documents/test.pdf"},
                "response_data": {"file_size": 1024},
                "metadata": {"file_size": 1024, "file_type": "pdf"},
                "tenant_id": "default",
                "service_name": "audit-service",
                "correlation_id": "batch_correlation_1",
                "retention_period_days": 90
            },
            {
                "event_type": "data_export",
                "user_id": "user_2",
                "session_id": "session_790",
                "ip_address": "192.168.1.102",
                "user_agent": "Mozilla/5.0 (Test Browser)",
                "resource_type": "report",
                "resource_id": "report_456",
                "action": "export",
                "status": "success",
                "request_data": {"export_format": "csv"},
                "response_data": {"record_count": 1000},
                "metadata": {"export_format": "csv", "record_count": 1000},
                "tenant_id": "default",
                "service_name": "audit-service",
                "correlation_id": "batch_correlation_2",
                "retention_period_days": 90
            }
        ]
    }
    
    print("Batch events to post:")
    print(json.dumps(batch_data, indent=2))
    print()
    
    # Post batch events (no query parameters needed)
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/events/batch",
        json=batch_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"POST /api/v1/audit/events/batch")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def test_audit_health():
    """Test audit service health endpoint."""
    print("🏥 Testing Audit Service Health")
    print("=" * 40)
    
    response = requests.get(f"{BASE_URL}/api/v1/audit/health")
    
    print(f"GET /api/v1/audit/health")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response: {response.text[:500]}...")
    else:
        print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def main():
    """Main test function."""
    print("🧪 Audit Event Posting and Retrieval Test (Correct Format)")
    print("=" * 70)
    print()
    
    # Test 1: Audit health check
    health_response = test_audit_health()
    
    # Test 2: Post a single event
    post_response = test_post_audit_event()
    
    # Extract event ID if successful
    event_id = None
    if post_response.status_code in [200, 201]:
        try:
            data = post_response.json()
            event_id = data.get("id") or data.get("audit_id")
            print(f"✅ Created event with ID: {event_id}")
        except:
            pass
    
    # Test 3: Get all events
    get_response = test_get_audit_events()
    
    # Test 4: Get specific event if we have an ID
    if event_id:
        test_get_specific_event(event_id)
    
    # Test 5: Post batch events
    batch_response = test_batch_events()
    
    # Test 6: Get events again to see the new ones
    print("📋 Testing Event Retrieval After Batch Post")
    print("=" * 50)
    final_response = requests.get(f"{BASE_URL}/api/v1/audit/events", params={"page": 1, "size": 20})
    print(f"GET /api/v1/audit/events (after batch)")
    print(f"Status: {final_response.status_code}")
    if final_response.status_code == 200:
        try:
            data = final_response.json()
            print(f"Total events: {data.get('total', 0)}")
            print(f"Items in response: {len(data.get('items', []))}")
        except:
            print(f"Response: {final_response.text[:200]}...")
    else:
        print(f"Response: {final_response.text[:200]}...")
    
    print()
    print("=" * 70)
    print("🎉 Audit Event Test Complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()
