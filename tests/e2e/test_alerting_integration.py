#!/usr/bin/env python3
"""
Test script for Alerting Service Integration

This script demonstrates the complete alerting functionality by:
1. Starting the alerting service
2. Creating alert providers and policies
3. Processing events to trigger alerts
4. Verifying alert delivery
"""

import requests
import json
import time
import subprocess
import sys
from datetime import datetime
import uuid

# Configuration
ALERTING_BASE_URL = "http://localhost:8001"
AUDIT_BASE_URL = "http://localhost:3000"
HEADERS = {"Authorization": "Bearer test-token"}

# Generate unique test ID to avoid conflicts
TEST_ID = f"test-{int(time.time())}-{str(uuid.uuid4())[:8]}"

# Generate unique test ID to avoid conflicts
TEST_ID = f"test-{int(time.time())}-{str(uuid.uuid4())[:8]}"


def check_service_health(url, service_name):
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"❌ {service_name} health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {service_name} is not accessible: {e}")
        return False


def wait_for_service(url, service_name, max_attempts=30):
    """Wait for a service to become available"""
    print(f"⏳ Waiting for {service_name} to start...")
    for attempt in range(max_attempts):
        if check_service_health(url, service_name):
            return True
        time.sleep(2)
    print(f"❌ {service_name} failed to start after {max_attempts} attempts")
    return False


def create_alert_providers():
    """Create alert providers for testing"""
    print("\n🔧 Creating alert providers...")
    
    providers = {}
    
    # Slack provider
    slack_provider = {
        "name": f"Test Slack {TEST_ID}",
        "provider_type": "slack",
        "enabled": True,
        "config": {
            "webhook_url": "https://hooks.slack.com/services/TEST/SLACK/WEBHOOK",
            "channel": "#test-alerts",
            "username": "Test Alert Bot"
        }
    }
    
    response = requests.post(
        f"{ALERTING_BASE_URL}/api/v1/alerts/providers",
        headers=HEADERS,
        json=slack_provider
    )
    if response.status_code == 201:
        providers['slack'] = response.json()["provider_id"]
        print(f"✅ Slack provider created: {providers['slack']}")
    else:
        print(f"❌ Failed to create Slack provider: {response.text}")
        return None

    # Webhook provider
    webhook_provider = {
        "name": f"Test Webhook {TEST_ID}",
        "provider_type": "webhook",
        "enabled": True,
        "config": {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    response = requests.post(
        f"{ALERTING_BASE_URL}/api/v1/alerts/providers",
        headers=HEADERS,
        json=webhook_provider
    )
    if response.status_code == 201:
        providers['webhook'] = response.json()["provider_id"]
        print(f"✅ Webhook provider created: {providers['webhook']}")
    else:
        print(f"❌ Failed to create Webhook provider: {response.text}")
        return None

    return providers


def create_alert_policies(providers):
    """Create alert policies for testing"""
    print("\n🔧 Creating alert policies...")
    
    policies = {}
    
    # Failed login policy
    failed_login_policy = {
        "name": f"Test Failed Login Alerts {TEST_ID}",
        "description": "Alert on failed login attempts",
        "enabled": True,
        "rules": [
            {
                "field": "event_type",
                "operator": "eq",
                "value": "user_login",
                "case_sensitive": True
            },
            {
                "field": "status",
                "operator": "eq",
                "value": "failed",
                "case_sensitive": True
            }
        ],
        "match_all": True,
        "severity": "high",
        "message_template": "Failed login attempt by user {user_id} from IP {ip_address}",
        "summary_template": "Failed login alert for {user_id}",
        "throttle_minutes": 5,
        "max_alerts_per_hour": 10,
        "providers": [providers['slack'], providers['webhook']]
    }
    
    response = requests.post(
        f"{ALERTING_BASE_URL}/api/v1/alerts/policies",
        headers=HEADERS,
        json=failed_login_policy
    )
    if response.status_code == 201:
        policies['failed_login'] = response.json()["policy_id"]
        print(f"✅ Failed login policy created: {policies['failed_login']}")
    else:
        print(f"❌ Failed to create failed login policy: {response.text}")
        return None

    # Add a small delay to ensure unique policy IDs
    time.sleep(1)

    # Unauthorized access policy
    unauthorized_policy = {
        "name": f"Test Unauthorized Access Alerts {TEST_ID}",
        "description": "Alert on unauthorized access attempts",
        "enabled": True,
        "rules": [
            {
                "field": "event_type",
                "operator": "eq",
                "value": "access_denied",
                "case_sensitive": True
            }
        ],
        "match_all": True,
        "severity": "critical",
        "message_template": "Unauthorized access attempt for resource {resource} by user {user_id}",
        "summary_template": "Unauthorized access alert for {resource}",
        "throttle_minutes": 0,
        "max_alerts_per_hour": 20,
        "providers": [providers['webhook']]
    }
    
    response = requests.post(
        f"{ALERTING_BASE_URL}/api/v1/alerts/policies",
        headers=HEADERS,
        json=unauthorized_policy
    )
    if response.status_code == 201:
        policies['unauthorized'] = response.json()["policy_id"]
        print(f"✅ Unauthorized access policy created: {policies['unauthorized']}")
    else:
        print(f"❌ Failed to create unauthorized access policy: {response.text}")
        return None

    return policies


def process_test_events(policies):
    """Process test events to trigger alerts"""
    print("\n🔧 Processing test events...")
    
    events = [
        {
            "event_type": "user_login",
            "user_id": "test.user",
            "ip_address": "192.168.1.100",
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "web-app",
            "resource": "/api/login",
            "reason": "Invalid credentials"
        },
        {
            "event_type": "access_denied",
            "user_id": "unauthorized.user",
            "ip_address": "10.0.0.50",
            "resource": "/api/admin/users",
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "admin-panel",
            "reason": "Insufficient permissions"
        },
        {
            "event_type": "user_login",
            "user_id": "test.user2",
            "ip_address": "192.168.1.101",
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "web-app",
            "resource": "/api/login",
            "reason": "Account locked"
        }
    ]
    
    triggered_alerts = []
    
    for i, event in enumerate(events, 1):
        print(f"   Processing event {i}: {event['event_type']} - {event.get('status', 'N/A')}")
        
        response = requests.post(
            f"{ALERTING_BASE_URL}/api/v1/alerts/process-event",
            headers=HEADERS,
            json=event,
            params={"tenant_id": "default"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result['triggered_alerts']:
                triggered_alerts.extend(result['triggered_alerts'])
                print(f"   ✅ Event triggered {len(result['triggered_alerts'])} alerts")
            else:
                print(f"   ⚠️  Event did not trigger any alerts")
        else:
            print(f"   ❌ Failed to process event: {response.text}")
    
    return triggered_alerts


def verify_alerts():
    """Verify that alerts were created"""
    print("\n🔍 Verifying alerts...")
    
    response = requests.get(f"{ALERTING_BASE_URL}/api/v1/alerts/alerts", headers=HEADERS)
    if response.status_code == 200:
        alerts = response.json()
        print(f"✅ Found {alerts['total']} alerts")
        
        for alert in alerts['alerts'][:5]:  # Show first 5 alerts
            print(f"   - {alert['title']} ({alert['severity']}) - {alert['status']}")
            if alert['delivery_status']:
                for provider, status in alert['delivery_status'].items():
                    print(f"     Provider {provider}: {status}")
        
        return alerts['total']
    else:
        print(f"❌ Failed to list alerts: {response.text}")
        return 0


def list_policies_and_providers():
    """List all policies and providers"""
    print("\n📋 Listing policies and providers...")
    
    # List policies
    response = requests.get(f"{ALERTING_BASE_URL}/api/v1/alerts/policies", headers=HEADERS)
    if response.status_code == 200:
        policies = response.json()
        print(f"✅ Found {policies['total']} policies:")
        for policy in policies['policies']:
            print(f"   - {policy['name']} ({policy['severity']}) - {'Enabled' if policy['enabled'] else 'Disabled'}")
    else:
        print(f"❌ Failed to list policies: {response.text}")
    
    # List providers
    response = requests.get(f"{ALERTING_BASE_URL}/api/v1/alerts/providers", headers=HEADERS)
    if response.status_code == 200:
        providers = response.json()
        print(f"✅ Found {providers['total']} providers:")
        for provider in providers['providers']:
            print(f"   - {provider['name']} ({provider['provider_type']}) - {'Enabled' if provider['enabled'] else 'Disabled'}")
    else:
        print(f"❌ Failed to list providers: {response.text}")


def cleanup_test_data(providers, policies):
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    # Delete policies
    if policies:
        for policy_id in policies.values():
            try:
                response = requests.delete(
                    f"{ALERTING_BASE_URL}/api/v1/alerts/policies/{policy_id}",
                    headers=HEADERS
                )
                if response.status_code == 204:
                    print(f"   ✅ Deleted policy: {policy_id}")
                else:
                    print(f"   ⚠️  Failed to delete policy {policy_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️  Error deleting policy {policy_id}: {e}")
    
    # Delete providers
    if providers:
        for provider_id in providers.values():
            try:
                response = requests.delete(
                    f"{ALERTING_BASE_URL}/api/v1/alerts/providers/{provider_id}",
                    headers=HEADERS
                )
                if response.status_code == 204:
                    print(f"   ✅ Deleted provider: {provider_id}")
                else:
                    print(f"   ⚠️  Failed to delete provider {provider_id}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️  Error deleting provider {provider_id}: {e}")


def main():
    """Main test function"""
    print("🧪 Testing Alerting Service Integration")
    print("=" * 60)
    
    # Check service health
    print("\n1. Checking service health...")
    if not check_service_health(ALERTING_BASE_URL, "Alerting Service"):
        print("❌ Alerting service is not available")
        return False
    
    if not check_service_health(AUDIT_BASE_URL, "Audit Service"):
        print("❌ Audit service is not available")
        return False
    
    # Create providers
    providers = create_alert_providers()
    if not providers:
        print("❌ Failed to create alert providers")
        return False
    
    # Create policies
    policies = create_alert_policies(providers)
    if not policies:
        print("❌ Failed to create alert policies")
        cleanup_test_data(providers, None)
        return False
    
    # Process test events
    triggered_alerts = process_test_events(policies)
    print(f"\n📊 Triggered {len(triggered_alerts)} alerts from test events")
    
    # Verify alerts
    total_alerts = verify_alerts()
    
    # List policies and providers
    list_policies_and_providers()
    
    # Cleanup
    cleanup_test_data(providers, policies)
    
    print(f"\n🎉 Alerting integration test completed!")
    print(f"   - Created {len(providers)} providers")
    print(f"   - Created {len(policies)} policies")
    print(f"   - Triggered {len(triggered_alerts)} alerts")
    print(f"   - Total alerts in system: {total_alerts}")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
