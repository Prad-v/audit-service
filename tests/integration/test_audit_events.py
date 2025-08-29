#!/usr/bin/env python3
"""
Test script to post and retrieve audit events with RBAC disabled.
"""

import requests
import json
import time
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"

def test_post_audit_event():
    """Test posting an audit event."""
    print("📝 Testing Audit Event Creation")
    print("=" * 40)
    
    # Sample audit event data
    event_data = {
        "event_type": "user_login",
        "user_id": "test_user_123",
        "username": "testuser",
        "tenant_id": "default",
        "resource_type": "auth",
        "resource_id": "login_session_456",
        "action": "login",
        "status": "success",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Test Browser)",
        "metadata": {
            "login_method": "password",
            "session_duration": 3600
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    print("Event data to post:")
    print(json.dumps(event_data, indent=2))
    print()
    
    # Post the event with query parameters
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/events?args=%7B%7D&kwargs=%7B%7D",
        json=event_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"POST /api/v1/audit/events?args={{}}&kwargs={{}}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def test_get_audit_events():
    """Test retrieving audit events."""
    print("📋 Testing Audit Event Retrieval")
    print("=" * 40)
    
    # Get all events with query parameters
    response = requests.get(f"{BASE_URL}/api/v1/audit/events?args=%7B%7D&kwargs=%7B%7D")
    
    print(f"GET /api/v1/audit/events?args={{}}&kwargs={{}}")
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
    
    response = requests.get(f"{BASE_URL}/api/v1/audit/events/{event_id}?args=%7B%7D&kwargs=%7B%7D")
    
    print(f"GET /api/v1/audit/events/{event_id}?args={{}}&kwargs={{}}")
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
    """Test posting multiple events in batch."""
    print("📦 Testing Batch Event Creation")
    print("=" * 40)
    
    # Sample batch events
    batch_data = {
        "events": [
            {
                "event_type": "file_access",
                "user_id": "user_1",
                "username": "alice",
                "tenant_id": "default",
                "resource_type": "file",
                "resource_id": "file_123",
                "action": "read",
                "status": "success",
                "ip_address": "192.168.1.101",
                "metadata": {"file_size": 1024, "file_type": "pdf"}
            },
            {
                "event_type": "data_export",
                "user_id": "user_2", 
                "username": "bob",
                "tenant_id": "default",
                "resource_type": "report",
                "resource_id": "report_456",
                "action": "export",
                "status": "success",
                "ip_address": "192.168.1.102",
                "metadata": {"export_format": "csv", "record_count": 1000}
            }
        ]
    }
    
    print("Batch events to post:")
    print(json.dumps(batch_data, indent=2))
    print()
    
    # Post batch events with query parameters
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/events/batch?args=%7B%7D&kwargs=%7B%7D",
        json=batch_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"POST /api/v1/audit/events/batch?args={{}}&kwargs={{}}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def test_simple_event():
    """Test with a simpler event format."""
    print("🎯 Testing Simple Event Creation")
    print("=" * 40)
    
    # Try a simpler approach - just the event data without complex structure
    simple_event = {
        "message": "User login attempt",
        "level": "info",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    print("Simple event data:")
    print(json.dumps(simple_event, indent=2))
    print()
    
    response = requests.post(
        f"{BASE_URL}/api/v1/audit/events?args=%7B%7D&kwargs=%7B%7D",
        json=simple_event,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"POST /api/v1/audit/events (simple)")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}...")
    print()
    
    return response

def main():
    """Main test function."""
    print("🧪 Audit Event Posting and Retrieval Test")
    print("=" * 60)
    print()
    
    # Test 1: Try simple event first
    simple_response = test_simple_event()
    
    # Test 2: Post a single event
    post_response = test_post_audit_event()
    
    # Extract event ID if successful
    event_id = None
    if post_response.status_code in [200, 201]:
        try:
            data = post_response.json()
            event_id = data.get("id") or data.get("audit_id")
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
    final_response = requests.get(f"{BASE_URL}/api/v1/audit/events?args=%7B%7D&kwargs=%7B%7D")
    print(f"GET /api/v1/audit/events (after batch)")
    print(f"Status: {final_response.status_code}")
    if final_response.status_code == 200:
        try:
            data = final_response.json()
            print(f"Total events: {len(data.get('items', []))}")
        except:
            print(f"Response: {final_response.text[:200]}...")
    else:
        print(f"Response: {final_response.text[:200]}...")
    
    print()
    print("=" * 60)
    print("🎉 Audit Event Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
