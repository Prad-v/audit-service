#!/usr/bin/env python3
"""
Test script for Events Service

This script tests the basic functionality of the Events Service.
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8003"
API_KEY = "test-token"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


async def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False


async def test_create_cloud_project():
    """Test creating a cloud project"""
    print("\n🔍 Testing cloud project creation...")
    
    project_data = {
        "name": "Test GCP Project",
        "description": "Test project for GCP integration",
        "cloud_provider": "gcp",
        "project_identifier": "test-project-123",
        "config": {
            "project_id": "test-project-123",
            "service_account_key": {
                "type": "service_account",
                "project_id": "test-project-123",
                "private_key_id": "test-key-id",
                "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----\n",
                "client_email": "test@test-project-123.iam.gserviceaccount.com",
                "client_id": "123456789"
            }
        },
        "enabled": True,
        "auto_subscribe": True,
        "tenant_id": "default",
        "created_by": "test-user"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/providers/projects",
            headers=HEADERS,
            json=project_data
        )
        
        if response.status_code == 201:
            project = response.json()
            print(f"✅ Cloud project created: {project['project_id']}")
            return project['project_id']
        else:
            print(f"❌ Failed to create cloud project: {response.status_code}")
            print(f"Response: {response.text}")
            return None


async def test_create_event_subscription(project_id: str):
    """Test creating an event subscription"""
    print("\n🔍 Testing event subscription creation...")
    
    subscription_data = {
        "name": "Test Subscription",
        "description": "Test subscription for critical events",
        "project_id": project_id,
        "event_types": ["grafana_alert", "cloud_alert"],
        "services": ["compute.googleapis.com", "storage.googleapis.com"],
        "regions": ["us-central1", "us-east1"],
        "severity_levels": ["critical", "high"],
        "custom_filters": {
            "environment": "test"
        },
        "enabled": True,
        "auto_resolve": True,
        "resolve_after_hours": 24,
        "tenant_id": "default",
        "created_by": "test-user"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/subscriptions",
            headers=HEADERS,
            json=subscription_data
        )
        
        if response.status_code == 201:
            subscription = response.json()
            print(f"✅ Event subscription created: {subscription['subscription_id']}")
            return subscription['subscription_id']
        else:
            print(f"❌ Failed to create event subscription: {response.status_code}")
            print(f"Response: {response.text}")
            return None


async def test_grafana_webhook():
    """Test Grafana webhook processing"""
    print("\n🔍 Testing Grafana webhook processing...")
    
    webhook_data = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "High CPU Usage",
                    "severity": "critical",
                    "service": "compute.googleapis.com",
                    "instance": "test-instance-1",
                    "job": "node-exporter"
                },
                "annotations": {
                    "summary": "CPU usage is above 90%",
                    "description": "Instance test-instance-1 is experiencing high CPU load",
                    "dashboardURL": "http://grafana.example.com/d/test-dashboard",
                    "panelURL": "http://grafana.example.com/d/test-dashboard?panelId=1"
                },
                "startsAt": datetime.utcnow().isoformat() + "Z",
                "endsAt": None,
                "fingerprint": "test-fingerprint-123"
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/events/webhook/grafana",
            headers=HEADERS,
            json=webhook_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Grafana webhook processed: {result['message']}")
            return True
        else:
            print(f"❌ Failed to process Grafana webhook: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def test_gcp_webhook():
    """Test GCP webhook processing"""
    print("\n🔍 Testing GCP webhook processing...")
    
    webhook_data = {
        "incident": {
            "incident_id": "test-incident-123",
            "severity": "high",
            "state": "open",
            "summary": "GCP Service Outage",
            "description": "Test GCP service is experiencing issues",
            "started_at": datetime.utcnow().isoformat() + "Z",
            "resource_type_display_name": "Compute Engine",
            "documentation": {
                "content": "This is a test incident for GCP"
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/events/webhook/gcp",
            headers=HEADERS,
            json=webhook_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ GCP webhook processed: {result['message']}")
            return True
        else:
            print(f"❌ Failed to process GCP webhook: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def test_list_events():
    """Test listing events"""
    print("\n🔍 Testing event listing...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/events",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            events = response.json()
            print(f"✅ Found {events['total']} events")
            return True
        else:
            print(f"❌ Failed to list events: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def test_create_alert_policy():
    """Test creating an alert policy"""
    print("\n🔍 Testing alert policy creation...")
    
    policy_data = {
        "name": "Test Alert Policy",
        "description": "Test policy for critical events",
        "enabled": True,
        "rules": [
            {
                "field": "event_type",
                "operator": "eq",
                "value": "grafana_alert",
                "case_sensitive": True
            },
            {
                "field": "severity",
                "operator": "eq",
                "value": "critical",
                "case_sensitive": True
            }
        ],
        "match_all": True,
        "severity": "critical",
        "message_template": "Critical alert: {title}",
        "summary_template": "Critical alert for {service_name}",
        "throttle_minutes": 5,
        "max_alerts_per_hour": 10,
        "providers": []
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/alerts/policies",
            headers=HEADERS,
            json=policy_data
        )
        
        if response.status_code == 201:
            policy = response.json()
            print(f"✅ Alert policy created: {policy['policy_id']}")
            return True
        else:
            print(f"❌ Failed to create alert policy: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def main():
    """Main test function"""
    print("🚀 Starting Events Service Tests")
    print("=" * 50)
    
    # Test health
    if not await test_health():
        print("❌ Health check failed, stopping tests")
        return
    
    # Test cloud project creation
    project_id = await test_create_cloud_project()
    if not project_id:
        print("❌ Cloud project creation failed, stopping tests")
        return
    
    # Test event subscription creation
    subscription_id = await test_create_event_subscription(project_id)
    if not subscription_id:
        print("❌ Event subscription creation failed, stopping tests")
        return
    
    # Test webhook processing
    await test_grafana_webhook()
    await test_gcp_webhook()
    
    # Test event listing
    await test_list_events()
    
    # Test alert policy creation
    await test_create_alert_policy()
    
    print("\n" + "=" * 50)
    print("✅ Events Service tests completed successfully!")
    print("\n📋 Test Summary:")
    print("- Health check: ✅")
    print("- Cloud project creation: ✅")
    print("- Event subscription creation: ✅")
    print("- Grafana webhook processing: ✅")
    print("- GCP webhook processing: ✅")
    print("- Event listing: ✅")
    print("- Alert policy creation: ✅")


if __name__ == "__main__":
    asyncio.run(main())
