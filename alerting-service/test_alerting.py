#!/usr/bin/env python3
"""
Test script for Alerting Service

This script demonstrates the alerting functionality by:
1. Creating alert providers (PagerDuty, Slack, Webhook, Email)
2. Creating alert policies
3. Processing events to trigger alerts
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8001"
HEADERS = {"Authorization": "Bearer test-token"}


def test_alerting_functionality():
    """Test the complete alerting functionality"""
    print("🧪 Testing Alerting Service Functionality")
    print("=" * 60)

    # 1. Test health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return

    # 2. Create alert providers
    print("\n2. Creating alert providers...")
    
    # PagerDuty provider
    pagerduty_provider = {
        "name": "Production PagerDuty",
        "provider_type": "pagerduty",
        "enabled": True,
        "config": {
            "api_key": "your-pagerduty-api-key",
            "service_id": "your-service-id",
            "urgency": "high"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/providers",
        headers=HEADERS,
        json=pagerduty_provider
    )
    if response.status_code == 201:
        pagerduty_id = response.json()["provider_id"]
        print(f"✅ PagerDuty provider created: {pagerduty_id}")
    else:
        print(f"❌ Failed to create PagerDuty provider: {response.text}")
        return

    # Slack provider
    slack_provider = {
        "name": "DevOps Slack",
        "provider_type": "slack",
        "enabled": True,
        "config": {
            "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            "channel": "#alerts",
            "username": "Alert Bot"
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/providers",
        headers=HEADERS,
        json=slack_provider
    )
    if response.status_code == 201:
        slack_id = response.json()["provider_id"]
        print(f"✅ Slack provider created: {slack_id}")
    else:
        print(f"❌ Failed to create Slack provider: {response.text}")
        return

    # Webhook provider
    webhook_provider = {
        "name": "Custom Webhook",
        "provider_type": "webhook",
        "enabled": True,
        "config": {
            "url": "https://your-webhook-endpoint.com/alerts",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
            "retry_count": 3
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/providers",
        headers=HEADERS,
        json=webhook_provider
    )
    if response.status_code == 201:
        webhook_id = response.json()["provider_id"]
        print(f"✅ Webhook provider created: {webhook_id}")
    else:
        print(f"❌ Failed to create Webhook provider: {response.text}")
        return

    # 3. Create alert policies
    print("\n3. Creating alert policies...")
    
    # Failed login policy
    failed_login_policy = {
        "name": "Failed Login Alerts",
        "description": "Alert on multiple failed login attempts",
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
        "providers": [pagerduty_id, slack_id]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/policies",
        headers=HEADERS,
        json=failed_login_policy
    )
    if response.status_code == 201:
        failed_login_policy_id = response.json()["policy_id"]
        print(f"✅ Failed login policy created: {failed_login_policy_id}")
    else:
        print(f"❌ Failed to create failed login policy: {response.text}")
        return

    # Unauthorized access policy
    unauthorized_policy = {
        "name": "Unauthorized Access Alerts",
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
        "message_template": "Unauthorized access attempt detected for resource {resource} by user {user_id}",
        "summary_template": "Unauthorized access alert for {resource}",
        "throttle_minutes": 0,
        "max_alerts_per_hour": 20,
        "providers": [pagerduty_id, slack_id, webhook_id]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/policies",
        headers=HEADERS,
        json=unauthorized_policy
    )
    if response.status_code == 201:
        unauthorized_policy_id = response.json()["policy_id"]
        print(f"✅ Unauthorized access policy created: {unauthorized_policy_id}")
    else:
        print(f"❌ Failed to create unauthorized access policy: {response.text}")
        return

    # 4. Process events to trigger alerts
    print("\n4. Processing events to trigger alerts...")
    
    # Failed login event
    failed_login_event = {
        "event_type": "user_login",
        "user_id": "john.doe",
        "ip_address": "192.168.1.100",
        "status": "failed",
        "timestamp": datetime.utcnow().isoformat(),
        "service_name": "web-app",
        "resource": "/api/login"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/process-event",
        headers=HEADERS,
        json=failed_login_event,
        params={"tenant_id": "default"}
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Failed login event processed: {result['message']}")
        if result['triggered_alerts']:
            print(f"   Triggered alerts: {len(result['triggered_alerts'])}")
    else:
        print(f"❌ Failed to process failed login event: {response.text}")

    # Unauthorized access event
    unauthorized_event = {
        "event_type": "access_denied",
        "user_id": "unknown",
        "ip_address": "10.0.0.50",
        "resource": "/api/admin/users",
        "timestamp": datetime.utcnow().isoformat(),
        "service_name": "admin-panel",
        "reason": "Insufficient permissions"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/alerts/process-event",
        headers=HEADERS,
        json=unauthorized_event,
        params={"tenant_id": "default"}
    )
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Unauthorized access event processed: {result['message']}")
        if result['triggered_alerts']:
            print(f"   Triggered alerts: {len(result['triggered_alerts'])}")
    else:
        print(f"❌ Failed to process unauthorized access event: {response.text}")

    # 5. List alerts
    print("\n5. Listing alerts...")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/alerts", headers=HEADERS)
    if response.status_code == 200:
        alerts = response.json()
        print(f"✅ Found {alerts['total']} alerts")
        for alert in alerts['alerts'][:3]:  # Show first 3 alerts
            print(f"   - {alert['title']} ({alert['severity']}) - {alert['status']}")
    else:
        print(f"❌ Failed to list alerts: {response.text}")

    # 6. List policies
    print("\n6. Listing policies...")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/policies", headers=HEADERS)
    if response.status_code == 200:
        policies = response.json()
        print(f"✅ Found {policies['total']} policies")
        for policy in policies['policies']:
            print(f"   - {policy['name']} ({policy['severity']}) - {'Enabled' if policy['enabled'] else 'Disabled'}")
    else:
        print(f"❌ Failed to list policies: {response.text}")

    # 7. List providers
    print("\n7. Listing providers...")
    response = requests.get(f"{BASE_URL}/api/v1/alerts/providers", headers=HEADERS)
    if response.status_code == 200:
        providers = response.json()
        print(f"✅ Found {providers['total']} providers")
        for provider in providers['providers']:
            print(f"   - {provider['name']} ({provider['provider_type']}) - {'Enabled' if provider['enabled'] else 'Disabled'}")
    else:
        print(f"❌ Failed to list providers: {response.text}")

    print("\n" + "=" * 60)
    print("✅ Alerting service test completed!")
    print("\n📋 Summary:")
    print(f"   - Created {providers['total']} alert providers")
    print(f"   - Created {policies['total']} alert policies")
    print(f"   - Generated {alerts['total']} alerts")
    print("\n🔗 API Documentation: http://localhost:8001/docs")


if __name__ == "__main__":
    test_alerting_functionality()
