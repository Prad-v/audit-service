#!/usr/bin/env python3
"""
Alerting E2E Test Runner

This script runs the comprehensive E2E test for alerting functionality.
It validates the complete alerting workflow including webhook server, 
alert rules, providers, policies, and event processing.
"""

import asyncio
import sys
import os

# Add the tests directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tests', 'e2e'))

from test_alerting_e2e import main

if __name__ == "__main__":
    print("🧪 Alerting E2E Test Runner")
    print("=" * 50)
    print("This test will:")
    print("1. Start a webhook server on port 8080")
    print("2. Create alert rule, webhook provider, and policy")
    print("3. Send matching event and validate webhook reception")
    print("4. Clean up all test resources")
    print("=" * 50)
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Alerting E2E test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Alerting E2E test failed!")
        sys.exit(1)
