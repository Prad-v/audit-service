#!/usr/bin/env python3
"""
E2E Test for Events Service Functionality

This test covers:
1. Cloud project registration and management
2. Event subscription creation and management
3. Event ingestion through webhooks
4. Alert rule and policy creation
5. End-to-end event flow with alerting
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, List
import threading
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

# Test configuration
API_GATEWAY_URL = "http://localhost:8002"
EVENTS_SERVICE_URL = "http://localhost:8003"
FRONTEND_URL = "http://localhost:3000"

# Global variables for test data
test_data = {
    "project_id": None,
    "subscription_id": None,
    "rule_id": None,
    "policy_id": None,
    "webhook_received_events": []
}

class WebhookHandler(http.server.BaseHTTPRequestHandler):
    """Simple webhook server to receive events"""
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            event_data = json.loads(post_data.decode('utf-8'))
            test_data["webhook_received_events"].append(event_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode())
            
            print(f"📥 Webhook received event: {event_data.get('event_type', 'unknown')}")
        except Exception as e:
            print(f"❌ Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()

def start_webhook_server(port: int = 8081) -> threading.Thread:
    """Start webhook server in background thread"""
    handler = WebhookHandler
    httpd = socketserver.TCPServer(("", port), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    print(f"🌐 Webhook server started on port {port}")
    return thread

def test_api_gateway_health():
    """Test API Gateway health"""
    print("\n1. Testing API Gateway Health...")
    try:
        response = requests.get(f"{API_GATEWAY_URL}/health")
        if response.status_code == 200:
            print("✅ API Gateway is healthy")
            data = response.json()
            print(f"   Services: {list(data.get('services', {}).keys())}")
            return True
        else:
            print(f"❌ API Gateway health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Gateway health check error: {e}")
        return False

def test_events_service_health():
    """Test Events Service health"""
    print("\n2. Testing Events Service Health...")
    try:
        response = requests.get(f"{EVENTS_SERVICE_URL}/health")
        if response.status_code == 200:
            print("✅ Events Service is healthy")
            return True
        else:
            print(f"❌ Events Service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Events Service health check error: {e}")
        return False

def test_cloud_project_management():
    """Test cloud project creation and management"""
    print("\n3. Testing Cloud Project Management...")
    
    # Create a test project
    project_data = {
        "name": f"Test Project {uuid.uuid4().hex[:8]}",
        "description": "E2E Test Project",
        "cloud_provider": "aws",
        "project_identifier": "test-project-123",
        "config": {
            "region": "us-west-2",
            "access_key": "test-key",
            "secret_key": "test-secret"
        },
        "enabled": True,
        "auto_subscribe": True
    }
    
    try:
        # Create project
        response = requests.post(
            f"{API_GATEWAY_URL}/events/api/v1/providers/projects",
            json=project_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 201:
            created_project = response.json()
            test_data["project_id"] = created_project["project_id"]
            print(f"✅ Cloud project created: {created_project['name']}")
            print(f"   Project ID: {created_project['project_id']}")
        else:
            print(f"❌ Failed to create project: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # List projects
        response = requests.get(
            f"{API_GATEWAY_URL}/events/api/v1/providers/projects",
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Retrieved {len(projects)} projects")
            return True
        else:
            print(f"❌ Failed to list projects: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Cloud project management error: {e}")
        return False

def test_event_subscription_management():
    """Test event subscription creation and management"""
    print("\n4. Testing Event Subscription Management...")
    
    if not test_data["project_id"]:
        print("❌ No project ID available for subscription test")
        return False
    
    subscription_data = {
        "name": f"Test Subscription {uuid.uuid4().hex[:8]}",
        "description": "E2E Test Subscription",
        "project_id": test_data["project_id"],
        "event_types": ["grafana_alert", "cloud_alert"],
        "services": ["ec2", "rds", "lambda"],
        "regions": ["us-west-2", "us-east-1"],
        "severity_levels": ["critical", "warning"],
        "webhook_url": "http://host.docker.internal:8081/webhook",
        "webhook_headers": {"X-Test": "e2e-test"},
        "filters": {"environment": "test"},
        "enabled": True,
        "auto_resolve": True,
        "resolve_after_hours": 24
    }
    
    try:
        # Create subscription
        response = requests.post(
            f"{API_GATEWAY_URL}/events/api/v1/subscriptions/subscriptions",
            json=subscription_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 201:
            created_subscription = response.json()
            test_data["subscription_id"] = created_subscription["subscription_id"]
            print(f"✅ Event subscription created: {created_subscription['name']}")
            print(f"   Subscription ID: {created_subscription['subscription_id']}")
        else:
            print(f"❌ Failed to create subscription: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # List subscriptions
        response = requests.get(
            f"{API_GATEWAY_URL}/events/api/v1/subscriptions/subscriptions",
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 200:
            subscriptions = response.json()
            print(f"✅ Retrieved {len(subscriptions)} subscriptions")
            return True
        else:
            print(f"❌ Failed to list subscriptions: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Event subscription management error: {e}")
        return False

def test_alert_rule_creation():
    """Test alert rule creation"""
    print("\n5. Testing Alert Rule Creation...")
    
    rule_data = {
        "name": f"Test Rule {uuid.uuid4().hex[:8]}",
        "description": "E2E Test Alert Rule",
        "field": "severity",
        "operator": "eq",
        "value": "critical",
        "enabled": True
    }
    
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/api/v1/alerts/rules",
            json=rule_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 201:
            created_rule = response.json()
            test_data["rule_id"] = created_rule["rule_id"]
            print(f"✅ Alert rule created: {created_rule['name']}")
            print(f"   Rule ID: {created_rule['rule_id']}")
            return True
        else:
            print(f"❌ Failed to create alert rule: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Alert rule creation error: {e}")
        return False

def test_alert_provider_creation():
    """Test alert provider creation"""
    print("\n6. Testing Alert Provider Creation...")
    
    provider_data = {
        "name": f"Test Webhook Provider {uuid.uuid4().hex[:8]}",
        "provider_type": "webhook",
        "config": {
            "url": "http://localhost:8080/webhook",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "timeout": 30
        },
        "enabled": True
    }
    
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/api/v1/alerts/providers",
            json=provider_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 201:
            created_provider = response.json()
            test_data["provider_id"] = created_provider["provider_id"]
            print(f"✅ Alert provider created: {created_provider['name']}")
            print(f"   Provider ID: {created_provider['provider_id']}")
            return True
        else:
            print(f"❌ Failed to create alert provider: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Alert provider creation error: {e}")
        return False

def test_alert_policy_creation():
    """Test alert policy creation"""
    print("\n7. Testing Alert Policy Creation...")
    
    if not test_data["rule_id"] or not test_data.get("provider_id"):
        print("❌ Missing rule_id or provider_id for policy creation")
        return False
    
    policy_data = {
        "name": f"Test Policy {uuid.uuid4().hex[:8]}",
        "description": "E2E Test Alert Policy",
        "enabled": True,
        "rules": [
            {
                "field": "severity",
                "operator": "eq",
                "value": "critical"
            }
        ],
        "providers": [test_data["provider_id"]],
        "message_template": "Alert: {event_type} - {message}",
        "summary_template": "Critical alert detected"
    }
    
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/api/v1/alerts/policies",
            json=policy_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 201:
            created_policy = response.json()
            test_data["policy_id"] = created_policy["policy_id"]
            print(f"✅ Alert policy created: {created_policy['name']}")
            print(f"   Policy ID: {created_policy['policy_id']}")
            return True
        else:
            print(f"❌ Failed to create alert policy: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Alert policy creation error: {e}")
        return False

def test_event_ingestion():
    """Test event ingestion through webhook"""
    print("\n8. Testing Event Ingestion...")
    
    # Test event that should trigger alert
    test_event = {
        "event_type": "cloud_alert",
        "source": "aws",
        "service": "ec2",
        "severity": "critical",
        "message": "EC2 instance is down",
        "details": {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-west-2",
            "environment": "test"
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "project_id": test_data["project_id"]
    }
    
    try:
        # Send event to events service webhook
        response = requests.post(
            f"{API_GATEWAY_URL}/events/api/v1/events/events/webhook/aws",
            json=test_event,
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 200:
            created_event = response.json()
            print(f"✅ Event ingested successfully")
            print(f"   Message: {created_event.get('message', 'N/A')}")
            print(f"   Events: {created_event.get('events', [])}")
            return True
        else:
            print(f"❌ Failed to ingest event: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Event ingestion error: {e}")
        return False

def test_alert_triggering():
    """Test alert triggering and webhook delivery"""
    print("\n9. Testing Alert Triggering...")
    
    # Wait for alert processing
    print("   Waiting for alert processing...")
    time.sleep(5)
    
    # Check if webhook received the alert
    if test_data["webhook_received_events"]:
        print(f"✅ Alert triggered and delivered to webhook")
        print(f"   Received {len(test_data['webhook_received_events'])} events")
        
        for i, event in enumerate(test_data["webhook_received_events"]):
            print(f"   Event {i+1}: {event.get('event_type', 'unknown')} - {event.get('message', 'N/A')}")
        return True
    else:
        print("❌ No alerts received on webhook")
        return False

def test_events_listing():
    """Test events listing and filtering"""
    print("\n10. Testing Events Listing...")
    
    try:
        # List events
        response = requests.get(
            f"{API_GATEWAY_URL}/events/api/v1/events/events",
            headers={"Authorization": "Bearer test-token"}
        )
        
        if response.status_code == 200:
            events_data = response.json()
            events = events_data.get("events", [])
            print(f"✅ Retrieved {len(events)} events")
            
            if events:
                latest_event = events[0]  # Assuming events are sorted by timestamp desc
                print(f"   Latest event: {latest_event.get('event_type', 'N/A')} - {latest_event.get('message', 'N/A')}")
            
            return True
        else:
            print(f"❌ Failed to list events: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Events listing error: {e}")
        return False

def test_frontend_accessibility():
    """Test frontend accessibility"""
    print("\n11. Testing Frontend Accessibility...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend accessibility error: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n12. Cleaning up test data...")
    
    try:
        # Delete alert policy
        if test_data.get("policy_id"):
            requests.delete(
                f"{API_GATEWAY_URL}/api/v1/alerts/policies/{test_data['policy_id']}",
                headers={"Authorization": "Bearer test-token"}
            )
            print("   ✅ Alert policy deleted")
        
        # Delete alert rule
        if test_data.get("rule_id"):
            requests.delete(
                f"{API_GATEWAY_URL}/api/v1/alerts/rules/{test_data['rule_id']}",
                headers={"Authorization": "Bearer test-token"}
            )
            print("   ✅ Alert rule deleted")
        
        # Delete alert provider
        if test_data.get("provider_id"):
            requests.delete(
                f"{API_GATEWAY_URL}/api/v1/alerts/providers/{test_data['provider_id']}",
                headers={"Authorization": "Bearer test-token"}
            )
            print("   ✅ Alert provider deleted")
        
        # Delete event subscription
        if test_data.get("subscription_id"):
            requests.delete(
                f"{API_GATEWAY_URL}/events/api/v1/subscriptions/subscriptions/{test_data['subscription_id']}",
                headers={"Authorization": "Bearer test-token"}
            )
            print("   ✅ Event subscription deleted")
        
        # Delete cloud project
        if test_data.get("project_id"):
            requests.delete(
                f"{API_GATEWAY_URL}/events/api/v1/providers/projects/{test_data['project_id']}",
                headers={"Authorization": "Bearer test-token"}
            )
            print("   ✅ Cloud project deleted")
            
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")

def main():
    """Main E2E test function"""
    print("🚀 Starting Events Service E2E Test")
    print("=" * 60)
    
    # Start webhook server
    webhook_thread = start_webhook_server()
    time.sleep(2)  # Give server time to start
    
    test_results = []
    
    try:
        # Run all tests
        tests = [
            test_api_gateway_health,
            test_events_service_health,
            test_cloud_project_management,
            test_event_subscription_management,
            test_alert_rule_creation,
            test_alert_provider_creation,
            test_alert_policy_creation,
            test_event_ingestion,
            test_alert_triggering,
            test_events_listing,
            test_frontend_accessibility
        ]
        
        for test in tests:
            try:
                result = test()
                test_results.append((test.__name__, result))
            except Exception as e:
                print(f"❌ Test {test.__name__} failed with exception: {e}")
                test_results.append((test.__name__, False))
        
        # Cleanup
        cleanup_test_data()
        
    finally:
        # Stop webhook server
        print("\n🛑 Stopping webhook server...")
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 E2E Test Results Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Events Service is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the logs above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
