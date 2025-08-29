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

# Configuration
ALERTING_BASE_URL = "http://localhost:8001"
AUDIT_BASE_URL = "http://localhost:3000"
HEADERS = {"Authorization": "Bearer test-token"}


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
        "name": "Test Slack",
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
        "name": "Test Webhook",
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
        "name": "Test Failed Login Alerts",
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
        "throttle_minutes": 1,
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

    # Unauthorized access policy
    unauthorized_policy = {
        "name": "Test Unauthorized Access Alerts",
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


def test_alerting_integration():
    """Main test function"""
    print("🧪 Testing Alerting Service Integration")
    print("=" * 60)
    
    # 1. Check if services are running
    print("\n1. Checking service health...")
    if not check_service_health(ALERTING_BASE_URL, "Alerting Service"):
        print("❌ Alerting service is not running. Please start it first.")
        print("   Run: docker-compose up -d alerting")
        return False
    
    if not check_service_health(AUDIT_BASE_URL, "Audit Service"):
        print("⚠️  Audit service is not running, but we can still test the alerting service")
    
    # 2. Create alert providers
    providers = create_alert_providers()
    if not providers:
        print("❌ Failed to create alert providers")
        return False
    
    # 3. Create alert policies
    policies = create_alert_policies(providers)
    if not policies:
        print("❌ Failed to create alert policies")
        return False
    
    # 4. Process test events
    triggered_alerts = process_test_events(policies)
    print(f"\n✅ Processed events triggered {len(triggered_alerts)} alerts")
    
    # 5. Verify alerts
    total_alerts = verify_alerts()
    
    # 6. List policies and providers
    list_policies_and_providers()
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("✅ Alerting service integration test completed!")
    print("\n📋 Summary:")
    print(f"   - Created {len(providers)} alert providers")
    print(f"   - Created {len(policies)} alert policies")
    print(f"   - Generated {total_alerts} alerts")
    print(f"   - Triggered {len(triggered_alerts)} alerts from test events")
    
    print("\n🔗 Useful URLs:")
    print(f"   - Alerting API: {ALERTING_BASE_URL}")
    print(f"   - Alerting Docs: {ALERTING_BASE_URL}/docs")
    print(f"   - Audit Service: {AUDIT_BASE_URL}")
    
    print("\n💡 Next Steps:")
    print("   1. Configure real alert providers (PagerDuty, Slack, etc.)")
    print("   2. Create more specific alert policies")
    print("   3. Integrate with your audit events")
    print("   4. Set up monitoring and alerting dashboards")
    
    return True


if __name__ == "__main__":
    try:
        success = test_alerting_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
