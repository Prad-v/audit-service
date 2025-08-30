#!/usr/bin/env python3
"""
E2E Test for Alerting Functionality

This test validates the complete alerting workflow:
1. Start a webhook server to receive alerts
2. Create alert rule, webhook provider, and policy
3. Send matching event and validate webhook reception
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
import threading
import queue

import httpx
import uvicorn
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for webhook server
webhook_app = FastAPI()
webhook_received_events = []
webhook_server_url = "http://localhost:8080"
webhook_server_running = False

# Queue for receiving webhook events
webhook_queue = queue.Queue()


@webhook_app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive webhook alerts"""
    try:
        body = await request.json()
        logger.info(f"Webhook received: {json.dumps(body, indent=2)}")
        
        # Store the event
        webhook_received_events.append({
            "timestamp": datetime.utcnow().isoformat(),
            "data": body
        })
        
        # Put in queue for test synchronization
        webhook_queue.put(body)
        
        return JSONResponse({"status": "received"})
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JSONResponse({"status": "error", "message": str(e)})


@webhook_app.get("/health")
async def webhook_health():
    """Health check for webhook server"""
    return {"status": "healthy", "events_received": len(webhook_received_events)}


def start_webhook_server():
    """Start the webhook server in a separate thread"""
    global webhook_server_running
    
    def run_server():
        uvicorn.run(webhook_app, host="0.0.0.0", port=8080, log_level="info")
    
    webhook_thread = threading.Thread(target=run_server, daemon=True)
    webhook_thread.start()
    webhook_server_running = True
    
    # Wait for server to start
    time.sleep(2)
    logger.info(f"Webhook server started at {webhook_server_url}")


class AlertingE2ETest:
    """E2E test class for alerting functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:3000"  # API Gateway
        self.alerting_url = f"{self.base_url}/api/v1/alerts"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-token"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Test data
        self.test_rule_id = None
        self.test_provider_id = None
        self.test_policy_id = None
        self.test_event_id = None
    
    async def setup(self):
        """Setup test environment"""
        logger.info("🔧 Setting up E2E test environment...")
        
        # Start webhook server
        start_webhook_server()
        
        # Wait for webhook server to be ready
        await self._wait_for_webhook_server()
        
        # Clear any existing webhook events
        global webhook_received_events
        webhook_received_events.clear()
        
        logger.info("✅ Test environment setup complete")
    
    async def _wait_for_webhook_server(self, max_retries: int = 10):
        """Wait for webhook server to be ready"""
        for i in range(max_retries):
            try:
                response = await self.client.get(f"{webhook_server_url}/health")
                if response.status_code == 200:
                    logger.info("✅ Webhook server is ready")
                    return
            except Exception as e:
                logger.info(f"Waiting for webhook server... ({i+1}/{max_retries})")
                await asyncio.sleep(1)
        
        raise Exception("Webhook server failed to start")
    
    async def test_alerting_e2e_workflow(self):
        """Main E2E test workflow"""
        logger.info("🚀 Starting Alerting E2E Test Workflow")
        logger.info("=" * 60)
        
        try:
            # Step 1: Create Alert Rule
            await self._test_create_alert_rule()
            
            # Step 2: Create Webhook Provider
            await self._test_create_webhook_provider()
            
            # Step 3: Create Alert Policy
            await self._test_create_alert_policy()
            
            # Step 4: Send Matching Event
            await self._test_send_matching_event()
            
            # Step 5: Validate Webhook Reception
            await self._test_validate_webhook_reception()
            
            # Step 6: Cleanup
            await self._test_cleanup()
            
            logger.info("✅ All E2E tests passed!")
            return True
            
        except Exception as e:
            logger.error(f"❌ E2E test failed: {e}")
            # Add delay to allow background processing to complete
            logger.info("⏳ Waiting for background processing to complete...")
            await asyncio.sleep(5)
            await self._test_cleanup()
            return False
    
    async def _test_create_alert_rule(self):
        """Test creating an alert rule"""
        logger.info("\n📋 Step 1: Creating Alert Rule")
        
        rule_data = {
            "name": "Test Login Rule",
            "description": "Rule to detect failed login attempts",
            "rule_type": "compound",
            "conditions": [
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
            "group_operator": "AND",
            "enabled": True
        }
        
        response = await self.client.post(
            f"{self.alerting_url}/rules",
            headers=self.headers,
            json=rule_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create alert rule: {response.status_code} - {response.text}")
        
        rule_response = response.json()
        self.test_rule_id = rule_response["rule_id"]
        logger.info(f"✅ Alert rule created: {self.test_rule_id}")
        
        # Verify rule was created
        await self._verify_rule_created()
    
    async def _verify_rule_created(self):
        """Verify the rule was created successfully"""
        response = await self.client.get(
            f"{self.alerting_url}/rules/{self.test_rule_id}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to verify rule: {response.status_code}")
        
        rule_data = response.json()
        assert rule_data["rule_id"] == self.test_rule_id
        assert rule_data["name"] == "Test Login Rule"
        assert rule_data["rule_type"] == "compound"
        logger.info("✅ Alert rule verification successful")
    
    async def _test_create_webhook_provider(self):
        """Test creating a webhook provider"""
        logger.info("\n🔗 Step 2: Creating Webhook Provider")
        
        provider_data = {
            "name": "Test Webhook Provider",
            "provider_type": "webhook",
            "enabled": True,
            "config": {
                "url": "http://host.docker.internal:8080/webhook",
                "method": "POST",
                "headers": {
                    "Content-Type": "application/json",
                    "X-Test-Provider": "e2e-test"
                },
                "timeout": 30,
                "retry_count": 3,
                "verify_ssl": False
            }
        }
        
        response = await self.client.post(
            f"{self.alerting_url}/providers",
            headers=self.headers,
            json=provider_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create webhook provider: {response.status_code} - {response.text}")
        
        provider_response = response.json()
        self.test_provider_id = provider_response["provider_id"]
        logger.info(f"✅ Webhook provider created: {self.test_provider_id}")
        
        # Verify provider was created
        await self._verify_provider_created()
    
    async def _verify_provider_created(self):
        """Verify the provider was created successfully"""
        response = await self.client.get(
            f"{self.alerting_url}/providers/{self.test_provider_id}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to verify provider: {response.status_code}")
        
        provider_data = response.json()
        assert provider_data["provider_id"] == self.test_provider_id
        assert provider_data["name"] == "Test Webhook Provider"
        assert provider_data["provider_type"] == "webhook"
        assert provider_data["config"]["url"] == "http://host.docker.internal:8080/webhook"
        logger.info("✅ Webhook provider verification successful")
    
    async def _test_create_alert_policy(self):
        """Test creating an alert policy"""
        logger.info("\n📊 Step 3: Creating Alert Policy")
        
        policy_data = {
            "name": "Test Failed Login Policy",
            "description": "Policy to alert on failed login attempts",
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
            "throttle_minutes": 0,
            "max_alerts_per_hour": 10,
            "providers": [self.test_provider_id]
        }
        
        response = await self.client.post(
            f"{self.alerting_url}/policies",
            headers=self.headers,
            json=policy_data
        )
        
        if response.status_code != 201:
            raise Exception(f"Failed to create alert policy: {response.status_code} - {response.text}")
        
        policy_response = response.json()
        self.test_policy_id = policy_response["policy_id"]
        logger.info(f"✅ Alert policy created: {self.test_policy_id}")
        
        # Verify policy was created
        await self._verify_policy_created()
    
    async def _verify_policy_created(self):
        """Verify the policy was created successfully"""
        response = await self.client.get(
            f"{self.alerting_url}/policies/{self.test_policy_id}",
            headers=self.headers
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to verify policy: {response.status_code}")
        
        policy_data = response.json()
        assert policy_data["policy_id"] == self.test_policy_id
        assert policy_data["name"] == "Test Failed Login Policy"
        assert policy_data["severity"] == "high"
        assert self.test_provider_id in policy_data["providers"]
        logger.info("✅ Alert policy verification successful")
    
    async def _test_send_matching_event(self):
        """Test sending a matching event"""
        logger.info("\n📤 Step 4: Sending Matching Event")
        
        # Generate unique event ID
        self.test_event_id = f"event-{uuid.uuid4().hex[:8]}"
        
        event_data = {
            "event_id": self.test_event_id,
            "event_type": "user_login",
            "user_id": "test-user-123",
            "ip_address": "192.168.1.100",
            "status": "failed",
            "timestamp": datetime.utcnow().isoformat(),
            "service_name": "test-service",
            "tenant_id": "default"
        }
        
        response = await self.client.post(
            f"{self.alerting_url}/process-event",
            headers=self.headers,
            json=event_data,
            params={"tenant_id": "default"}
        )
        
        logger.info(f"🔍 Event processing response: {response.status_code} - {response.text}")
        
        if response.status_code != 200:
            raise Exception(f"Failed to process event: {response.status_code} - {response.text}")
        
        process_response = response.json()
        logger.info(f"✅ Event processed: {process_response}")
        
        # Wait for alert processing to complete
        logger.info("⏳ Waiting for alert processing to complete...")
        await asyncio.sleep(5)
    
    async def _test_validate_webhook_reception(self):
        """Test validating webhook reception"""
        logger.info("\n🔍 Step 5: Validating Webhook Reception")
        
        # Wait for webhook to be received (with timeout)
        try:
            webhook_event = webhook_queue.get(timeout=10)
            logger.info(f"✅ Webhook event received: {json.dumps(webhook_event, indent=2)}")
        except queue.Empty:
            raise Exception("Webhook event not received within timeout")
        
        # Validate webhook event structure
        await self._validate_webhook_event_structure(webhook_event)
        
        # Check webhook server health
        await self._check_webhook_server_health()
        
        # Verify alert was created in the system
        await self._verify_alert_created()
    
    async def _validate_webhook_event_structure(self, webhook_event: Dict[str, Any]):
        """Validate the structure of the received webhook event"""
        logger.info("🔍 Validating webhook event structure...")
        
        # Check required fields
        required_fields = ["alert_id", "policy_id", "severity", "title", "message", "summary"]
        for field in required_fields:
            if field not in webhook_event:
                raise Exception(f"Missing required field in webhook event: {field}")
        
        # Validate specific values
        assert webhook_event["severity"] == "high"
        assert "Failed login attempt by user test-user-123" in webhook_event["title"]
        assert "test-user-123" in webhook_event["message"]
        assert webhook_event["policy_id"] == self.test_policy_id
        
        # Check event data
        if "event_data" in webhook_event:
            event_data = webhook_event["event_data"]
            assert event_data["event_type"] == "user_login"
            assert event_data["user_id"] == "test-user-123"
            assert event_data["status"] == "failed"
        
        logger.info("✅ Webhook event structure validation successful")
    
    async def _check_webhook_server_health(self):
        """Check webhook server health"""
        response = await self.client.get(f"{webhook_server_url}/health")
        
        if response.status_code != 200:
            raise Exception("Webhook server health check failed")
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert health_data["events_received"] > 0
        logger.info(f"✅ Webhook server health check passed: {health_data['events_received']} events received")
    
    async def _verify_alert_created(self):
        """Verify alert was created in the alerting system"""
        logger.info("🔍 Verifying alert was created in system...")
        
        # Retry mechanism for alert verification
        for attempt in range(3):
            try:
                response = await self.client.get(
                    f"{self.alerting_url}/alerts",
                    headers=self.headers,
                    params={"page": 1, "per_page": 10}
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get alerts: {response.status_code}")
                
                alerts_response = response.json()
                alerts = alerts_response["alerts"]
                
                logger.info(f"🔍 Found {len(alerts)} alerts in system")
                logger.info(f"🔍 Looking for event_id: {self.test_event_id}")
                
                # Find our alert
                test_alert = None
                for alert in alerts:
                    logger.info(f"🔍 Checking alert {alert.get('alert_id')}: event_data={alert.get('event_data')}")
                    if alert.get("event_data", {}).get("event_id") == self.test_event_id:
                        test_alert = alert
                        break
                
                if test_alert:
                    break
                else:
                    logger.warning(f"⚠️ Alert not found on attempt {attempt + 1}/3, retrying...")
                    if attempt < 2:
                        await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"⚠️ Alert verification attempt {attempt + 1}/3 failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
        
        if not test_alert:
            logger.error(f"❌ Alert not found after 3 attempts. Available alerts: {[a.get('alert_id') for a in alerts]}")
            raise Exception("Alert not found in system")
        
        # Validate alert
        assert test_alert["severity"] == "high"
        assert test_alert["policy_id"] == self.test_policy_id
        assert test_alert["status"] == "active"
        
        # Check delivery status
        delivery_status = test_alert.get("delivery_status", {})
        if self.test_provider_id in delivery_status:
            assert delivery_status[self.test_provider_id] in ["sent", "delivered"]
        
        logger.info(f"✅ Alert verified in system: {test_alert['alert_id']}")
    
    async def _test_cleanup(self):
        """Clean up test resources"""
        logger.info("\n🧹 Step 6: Cleaning up test resources")
        
        try:
            # Delete policy
            if self.test_policy_id:
                response = await self.client.delete(
                    f"{self.alerting_url}/policies/{self.test_policy_id}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    logger.info(f"✅ Deleted policy: {self.test_policy_id}")
            
            # Delete provider
            if self.test_provider_id:
                response = await self.client.delete(
                    f"{self.alerting_url}/providers/{self.test_provider_id}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    logger.info(f"✅ Deleted provider: {self.test_provider_id}")
            
            # Delete rule
            if self.test_rule_id:
                response = await self.client.delete(
                    f"{self.alerting_url}/rules/{self.test_rule_id}",
                    headers=self.headers
                )
                if response.status_code == 204:
                    logger.info(f"✅ Deleted rule: {self.test_rule_id}")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")
        
        logger.info("✅ Cleanup completed")
    
    async def close(self):
        """Close the test client"""
        await self.client.aclose()


async def main():
    """Main test function"""
    logger.info("🧪 Starting Alerting E2E Test")
    logger.info("=" * 60)
    
    # Check if services are running
    try:
        async with httpx.AsyncClient() as client:
            # Check alerting service with retry
            for attempt in range(3):
                try:
                    response = await client.get(
                        "http://localhost:3000/api/v1/alerts/providers",
                        headers={"Authorization": "Bearer test-token"}
                    )
                    if response.status_code == 200:
                        logger.info("✅ Alerting service is accessible")
                        break
                    else:
                        logger.warning(f"Alerting service returned {response.status_code}, attempt {attempt + 1}/3")
                        if attempt < 2:
                            await asyncio.sleep(2)
                except Exception as e:
                    logger.warning(f"Connection attempt {attempt + 1}/3 failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(2)
            else:
                raise Exception("Alerting service not accessible after 3 attempts")
                
    except Exception as e:
        logger.error(f"❌ Services not ready: {e}")
        logger.error("Please ensure the alerting service is running:")
        logger.error("  docker-compose up -d alerting")
        return False
    
    # Run E2E test
    test = AlertingE2ETest()
    
    try:
        await test.setup()
        success = await test.test_alerting_e2e_workflow()
        
        if success:
            logger.info("\n🎉 E2E Test Summary")
            logger.info("=" * 60)
            logger.info("✅ All tests passed successfully!")
            logger.info("✅ Webhook server received alerts")
            logger.info("✅ Alert rules, providers, and policies created")
            logger.info("✅ Event processing and alert triggering working")
            logger.info("✅ End-to-end alerting workflow validated")
        else:
            logger.error("\n❌ E2E Test Summary")
            logger.error("=" * 60)
            logger.error("❌ Some tests failed")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ E2E test failed with exception: {e}")
        return False
    
    finally:
        await test.close()


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
