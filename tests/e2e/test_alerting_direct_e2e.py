#!/usr/bin/env python3
"""
Direct Alerting E2E Test

This test validates the alerting functionality directly:
1. Create alert providers (webhook, slack)
2. Create alert policies
3. Send events directly to alerting service
4. Verify alert creation and delivery
"""

import asyncio
import httpx
import json
import time
import threading
import http.server
import socketserver
from datetime import datetime
import uuid
import sys

# Configuration
BASE_URL = "http://localhost:3000"  # API Gateway
ALERTING_URL = "http://localhost:8001"  # Direct alerting service
HEADERS = {"Authorization": "Bearer test-token"}

# Test data storage
test_data = {
    "webhook_events": [],
    "provider_id": None,
    "policy_id": None,
    "alert_id": None
}

# Generate unique test ID
TEST_ID = f"test-{int(time.time())}-{str(uuid.uuid4())[:8]}"


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    """Simple webhook server to receive events"""
    
    def do_POST(self):
        if self.path == "/webhook":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                event_data = json.loads(post_data.decode('utf-8'))
                test_data["webhook_events"].append(event_data)
                
                print(f"📥 Webhook received: {json.dumps(event_data, indent=2)}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "received"}).encode())
                
            except Exception as e:
                print(f"❌ Error processing webhook: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "healthy",
                "events_received": len(test_data["webhook_events"])
            }).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass


def start_webhook_server(port: int = 8080) -> threading.Thread:
    """Start webhook server in background thread"""
    handler = WebhookHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    def run_server():
        httpd.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    # Wait for server to start
    time.sleep(1)
    print(f"🌐 Webhook server started on port {port}")
    return thread


async def test_alerting_service_health():
    """Test alerting service health"""
    print("\n🔍 Testing alerting service health...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ALERTING_URL}/health")
        if response.status_code == 200:
            print("✅ Alerting service is healthy")
            return True
        else:
            print(f"❌ Alerting service health check failed: {response.status_code}")
            return False


async def create_webhook_provider():
    """Create a webhook provider"""
    print("\n🔗 Creating webhook provider...")
    
    provider_data = {
        "name": f"Test Webhook Provider {TEST_ID}",
        "provider_type": "webhook",
        "enabled": True,
        "config": {
            "url": "http://host.docker.internal:8080/webhook",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
            "retry_count": 3,
            "verify_ssl": False
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/alerts/providers",
            headers=HEADERS,
            json=provider_data
        )
        
        if response.status_code == 201:
            provider = response.json()
            test_data["provider_id"] = provider["provider_id"]
            print(f"✅ Webhook provider created: {provider['provider_id']}")
            return True
        else:
            print(f"❌ Failed to create webhook provider: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def create_alert_policy():
    """Create an alert policy"""
    print("\n📊 Creating alert policy...")
    
    policy_data = {
        "name": f"Test Policy {TEST_ID}",
        "description": "Test policy for failed login alerts",
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
        "providers": [test_data["provider_id"]]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/alerts/policies",
            headers=HEADERS,
            json=policy_data
        )
        
        if response.status_code == 201:
            policy = response.json()
            test_data["policy_id"] = policy["policy_id"]
            print(f"✅ Alert policy created: {policy['policy_id']}")
            return True
        else:
            print(f"❌ Failed to create alert policy: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def send_test_event():
    """Send a test event that should trigger an alert"""
    print("\n📤 Sending test event...")
    
    event_data = {
        "event_id": f"event-{str(uuid.uuid4())[:8]}",
        "event_type": "user_login",
        "user_id": "test-user-123",
        "ip_address": "192.168.1.100",
        "status": "failed",
        "timestamp": datetime.utcnow().isoformat(),
        "service_name": "test-service",
        "tenant_id": "default"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/alerts/process-event",
            headers=HEADERS,
            json=event_data,
            params={"tenant_id": "default"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Event processed: {result}")
            
            if result.get("triggered_alerts"):
                test_data["alert_id"] = result["triggered_alerts"][0]["alert_id"]
                print(f"✅ Alert triggered: {test_data['alert_id']}")
                return True
            else:
                print("⚠️  No alerts were triggered")
                return False
        else:
            print(f"❌ Failed to process event: {response.status_code}")
            print(f"Response: {response.text}")
            return False


async def verify_webhook_reception():
    """Verify that the webhook received the alert"""
    print("\n🔍 Verifying webhook reception...")
    
    # Wait a bit for the webhook to be processed
    await asyncio.sleep(3)
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8080/health")
        if response.status_code == 200:
            health_data = response.json()
            events_received = health_data.get("events_received", 0)
            
            if events_received > 0:
                print(f"✅ Webhook received {events_received} events")
                
                # Get the latest event
                if test_data["webhook_events"]:
                    latest_event = test_data["webhook_events"][-1]
                    print(f"✅ Latest webhook event: {json.dumps(latest_event, indent=2)}")
                    return True
                else:
                    print("❌ No webhook events recorded")
                    return False
            else:
                print("❌ No events received on webhook")
                return False
        else:
            print(f"❌ Webhook health check failed: {response.status_code}")
            return False


async def verify_alert_in_system():
    """Verify that the alert was created in the system"""
    print("\n🔍 Verifying alert in system...")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/v1/alerts/alerts",
            headers=HEADERS,
            params={"page": 1, "per_page": 10}
        )
        
        if response.status_code == 200:
            alerts_data = response.json()
            print(f"🔍 Found {alerts_data['total']} alerts in system")
            
            # Look for our specific alert from the webhook event
            if test_data["webhook_events"]:
                latest_event = test_data["webhook_events"][-1]
                expected_alert_id = latest_event.get("alert_id")
                
                if expected_alert_id:
                    for alert in alerts_data["alerts"]:
                        if alert["alert_id"] == expected_alert_id:
                            print(f"✅ Alert verified in system: {alert['alert_id']}")
                            return True
                    
                    print(f"❌ Alert {expected_alert_id} not found in system")
                    return False
                else:
                    print("⚠️  No alert ID in webhook event")
                    return False
            else:
                print("⚠️  No webhook events to verify")
                return False
        else:
            print(f"❌ Failed to list alerts: {response.status_code}")
            return False


async def cleanup_test_resources():
    """Clean up test resources"""
    print("\n🧹 Cleaning up test resources...")
    
    async with httpx.AsyncClient() as client:
        # Delete policy
        if test_data["policy_id"]:
            response = await client.delete(
                f"{BASE_URL}/api/v1/alerts/policies/{test_data['policy_id']}",
                headers=HEADERS
            )
            if response.status_code == 204:
                print("✅ Alert policy deleted")
            else:
                print(f"⚠️  Failed to delete policy: {response.status_code}")
        
        # Delete provider
        if test_data["provider_id"]:
            response = await client.delete(
                f"{BASE_URL}/api/v1/alerts/providers/{test_data['provider_id']}",
                headers=HEADERS
            )
            if response.status_code == 204:
                print("✅ Alert provider deleted")
            else:
                print(f"⚠️  Failed to delete provider: {response.status_code}")


async def main():
    """Main test function"""
    print("🧪 Starting Direct Alerting E2E Test")
    print("=" * 60)
    
    # Start webhook server
    webhook_thread = start_webhook_server()
    
    try:
        # Test alerting service health
        if not await test_alerting_service_health():
            return False
        
        # Create webhook provider
        if not await create_webhook_provider():
            return False
        
        # Create alert policy
        if not await create_alert_policy():
            return False
        
        # Send test event
        try:
            if not await send_test_event():
                print("❌ Failed to send test event")
                return False
        except Exception as e:
            print(f"❌ Error sending test event: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Wait for alert processing
        print("\n⏳ Waiting for alert processing to complete...")
        await asyncio.sleep(3)
        
        # Verify webhook reception
        if not await verify_webhook_reception():
            return False
        
        # Verify alert in system
        if not await verify_alert_in_system():
            return False
        
        # Cleanup
        await cleanup_test_resources()
        
        print("\n🎉 Direct Alerting E2E Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    finally:
        # Stop webhook server
        print("\n🛑 Stopping webhook server...")
        # The thread will be cleaned up automatically since it's daemon


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
