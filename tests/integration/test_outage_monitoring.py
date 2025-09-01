#!/usr/bin/env python3
"""
Test script for outage monitoring functionality

This script tests the multi-cloud outage monitoring features including:
- RSS feed parsing
- API status checking
- Event creation and processing
- Webhook delivery
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
EVENTS_SERVICE_URL = "http://localhost:8003"
API_BASE_URL = "http://localhost:8000"

class OutageMonitoringTester:
    """Test class for outage monitoring functionality"""
    
    def __init__(self):
        self.session = None
        self.test_results = []
    
    async def setup(self):
        """Setup test environment"""
        self.session = aiohttp.ClientSession()
        logger.info("Test environment setup complete")
    
    async def cleanup(self):
        """Cleanup test environment"""
        if self.session:
            await self.session.close()
        logger.info("Test environment cleanup complete")
    
    async def test_health_check(self) -> bool:
        """Test events service health"""
        try:
            async with self.session.get(f"{EVENTS_SERVICE_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Health check passed: {data}")
                    return True
                else:
                    logger.error(f"Health check failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    async def test_outage_monitoring_status(self) -> bool:
        """Test outage monitoring status endpoint"""
        try:
            async with self.session.get(f"{EVENTS_SERVICE_URL}/api/v1/outages/status") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Outage monitoring status: {data}")
                    return True
                else:
                    logger.error(f"Status check failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return False
    
    async def test_start_outage_monitoring(self) -> bool:
        """Test starting outage monitoring"""
        try:
            async with self.session.post(f"{EVENTS_SERVICE_URL}/api/v1/outages/start") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Started outage monitoring: {data}")
                    return True
                else:
                    logger.error(f"Start monitoring failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Start monitoring error: {e}")
            return False
    
    async def test_check_provider_outages(self, provider: str) -> bool:
        """Test checking outages for a specific provider"""
        try:
            async with self.session.post(f"{EVENTS_SERVICE_URL}/api/v1/outages/check/{provider}") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Checked {provider} outages: {data}")
                    return True
                else:
                    logger.error(f"Check {provider} outages failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Check {provider} outages error: {e}")
            return False
    
    async def test_check_all_providers(self) -> bool:
        """Test checking all providers for outages"""
        try:
            async with self.session.post(f"{EVENTS_SERVICE_URL}/api/v1/outages/check/all") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Checked all providers: {data}")
                    return True
                else:
                    logger.error(f"Check all providers failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Check all providers error: {e}")
            return False
    
    async def test_outage_history(self) -> bool:
        """Test getting outage history"""
        try:
            async with self.session.get(f"{EVENTS_SERVICE_URL}/api/v1/outages/history") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Outage history: {len(data.get('outages', []))} outages found")
                    return True
                else:
                    logger.error(f"Outage history failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Outage history error: {e}")
            return False
    
    async def test_webhook_delivery(self) -> bool:
        """Test webhook delivery"""
        try:
            # Create a test webhook URL (using webhook.site or similar)
            test_webhook_url = "https://webhook.site/your-test-url"  # Replace with actual test URL
            
            params = {
                "webhook_url": test_webhook_url,
                "provider": "gcp"
            }
            
            async with self.session.post(f"{EVENTS_SERVICE_URL}/api/v1/outages/webhook/test", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Webhook test: {data}")
                    return True
                else:
                    logger.error(f"Webhook test failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Webhook test error: {e}")
            return False
    
    async def test_rss_feed_parsing(self) -> bool:
        """Test RSS feed parsing functionality"""
        try:
            # Test GCP RSS feed
            gcp_feed_url = "https://status.cloud.google.com/feed"
            async with self.session.get(gcp_feed_url) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.info(f"GCP RSS feed accessible, content length: {len(content)}")
                    
                    # Basic RSS validation
                    if "<?xml" in content and "<rss" in content:
                        logger.info("GCP RSS feed format appears valid")
                        return True
                    else:
                        logger.warning("GCP RSS feed format may be invalid")
                        return False
                else:
                    logger.error(f"GCP RSS feed failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"RSS feed test error: {e}")
            return False
    
    async def test_create_outage_subscription(self) -> bool:
        """Test creating an outage subscription"""
        try:
            subscription_data = {
                "name": "Test Outage Subscription",
                "project_id": "test-project",
                "event_types": ["outage_status"],
                "services": ["compute.googleapis.com", "storage.googleapis.com"],
                "regions": ["us-central1"],
                "severity_levels": ["critical", "high"],
                "enabled": True,
                "auto_resolve": True,
                "resolve_after_hours": 24
            }
            
            async with self.session.post(
                f"{EVENTS_SERVICE_URL}/api/v1/subscriptions/subscriptions",
                json=subscription_data
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    logger.info(f"Created outage subscription: {data}")
                    return True
                else:
                    logger.error(f"Create subscription failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Create subscription error: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all outage monitoring tests"""
        logger.info("Starting outage monitoring tests...")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Outage Monitoring Status", self.test_outage_monitoring_status),
            ("Start Outage Monitoring", self.test_start_outage_monitoring),
            ("Check GCP Outages", lambda: self.test_check_provider_outages("gcp")),
            ("Check AWS Outages", lambda: self.test_check_provider_outages("aws")),
            ("Check Azure Outages", lambda: self.test_check_provider_outages("azure")),
            ("Check All Providers", self.test_check_all_providers),
            ("Outage History", self.test_outage_history),
            ("RSS Feed Parsing", self.test_rss_feed_parsing),
            ("Create Outage Subscription", self.test_create_outage_subscription),
            ("Webhook Delivery", self.test_webhook_delivery),
        ]
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Running test: {test_name}")
                result = await test_func()
                self.test_results.append((test_name, result))
                
                if result:
                    logger.info(f"✅ {test_name} - PASSED")
                else:
                    logger.error(f"❌ {test_name} - FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} - ERROR: {e}")
                self.test_results.append((test_name, False))
        
        # Print summary
        self.print_test_summary()
    
    def print_test_summary(self):
        """Print test results summary"""
        logger.info("\n" + "="*50)
        logger.info("OUTAGE MONITORING TEST SUMMARY")
        logger.info("="*50)
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Outage monitoring is working correctly.")
        else:
            logger.error(f"⚠️  {total - passed} tests failed. Please check the implementation.")


async def main():
    """Main test function"""
    tester = OutageMonitoringTester()
    
    try:
        await tester.setup()
        await tester.run_all_tests()
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
