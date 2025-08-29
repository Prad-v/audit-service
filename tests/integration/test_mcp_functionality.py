#!/usr/bin/env python3
"""
Test script for MCP (Model Context Protocol) natural language query functionality

This script tests the FastMCP server integration with the audit service,
verifying that natural language queries work correctly.
"""

import requests
import json
import time
from datetime import datetime, timedelta
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
BASE_URL = "http://localhost:8000"
MCP_BASE_URL = f"{BASE_URL}/api/v1/mcp"

def print_status(message, status="INFO"):
    """Print a status message with color coding"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status == "SUCCESS":
        color = Fore.GREEN
        symbol = "✅"
    elif status == "ERROR":
        color = Fore.RED
        symbol = "❌"
    elif status == "WARNING":
        color = Fore.YELLOW
        symbol = "⚠️"
    else:
        color = Fore.BLUE
        symbol = "ℹ️"
    
    print(f"{color}{symbol} [{timestamp}] {message}{Style.RESET_ALL}")

def test_mcp_health():
    """Test MCP service health endpoint"""
    print_status("Testing MCP service health...")
    
    try:
        response = requests.get(f"{MCP_BASE_URL}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status(f"MCP service is healthy: {data['service']} v{data['version']}", "SUCCESS")
            print(f"   Capabilities: {', '.join(data['capabilities'])}")
            return True
        else:
            print_status(f"MCP health check failed: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to connect to MCP service: {e}", "ERROR")
        return False

def test_mcp_capabilities():
    """Test MCP capabilities endpoint"""
    print_status("Testing MCP capabilities...")
    
    try:
        response = requests.get(f"{MCP_BASE_URL}/capabilities", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print_status("MCP capabilities retrieved successfully", "SUCCESS")
            print(f"   Service: {data['service']} v{data['version']}")
            print(f"   Supported time ranges: {', '.join(data['supported_time_ranges'])}")
            print(f"   Supported event types: {', '.join(data['supported_event_types'][:5])}...")
            print(f"   Supported severities: {', '.join(data['supported_severities'])}")
            return True
        else:
            print_status(f"Failed to get MCP capabilities: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to get MCP capabilities: {e}", "ERROR")
        return False

def test_natural_language_query(query, expected_type=None):
    """Test a natural language query"""
    print_status(f"Testing query: '{query}'")
    
    try:
        response = requests.post(
            f"{MCP_BASE_URL}/query",
            json={"query": query, "limit": 10},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                query_type = data.get("query_type", "unknown")
                result_count = data.get("result_count", 0)
                
                print_status(f"Query successful: {query_type} ({result_count} results)", "SUCCESS")
                
                if expected_type and query_type != expected_type:
                    print_status(f"Expected type '{expected_type}', got '{query_type}'", "WARNING")
                
                return True
            else:
                print_status(f"Query failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            print_status(f"Query request failed: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to execute query: {e}", "ERROR")
        return False

def test_get_query(query, expected_type=None):
    """Test a GET query"""
    print_status(f"Testing GET query: '{query}'")
    
    try:
        response = requests.get(
            f"{MCP_BASE_URL}/query",
            params={"q": query, "limit": 10},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                query_type = data.get("query_type", "unknown")
                result_count = data.get("result_count", 0)
                
                print_status(f"GET query successful: {query_type} ({result_count} results)", "SUCCESS")
                
                if expected_type and query_type != expected_type:
                    print_status(f"Expected type '{expected_type}', got '{query_type}'", "WARNING")
                
                return True
            else:
                print_status(f"GET query failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            print_status(f"GET query request failed: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to execute GET query: {e}", "ERROR")
        return False

def test_mcp_summary():
    """Test MCP summary endpoint"""
    print_status("Testing MCP summary...")
    
    try:
        response = requests.get(f"{MCP_BASE_URL}/summary?time_range=24h", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print_status("MCP summary retrieved successfully", "SUCCESS")
                return True
            else:
                print_status(f"Summary failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            print_status(f"Summary request failed: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to get summary: {e}", "ERROR")
        return False

def test_mcp_trends():
    """Test MCP trends endpoint"""
    print_status("Testing MCP trends...")
    
    try:
        response = requests.get(f"{MCP_BASE_URL}/trends?time_range=7d&metric=count", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print_status("MCP trends retrieved successfully", "SUCCESS")
                return True
            else:
                print_status(f"Trends failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            print_status(f"Trends request failed: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to get trends: {e}", "ERROR")
        return False

def test_mcp_alerts():
    """Test MCP alerts endpoint"""
    print_status("Testing MCP alerts...")
    
    try:
        response = requests.get(f"{MCP_BASE_URL}/alerts?severity=high&time_range=1h", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print_status("MCP alerts retrieved successfully", "SUCCESS")
                return True
            else:
                print_status(f"Alerts failed: {data.get('error', 'Unknown error')}", "ERROR")
                return False
        else:
            print_status(f"Alerts request failed: {response.status_code}", "ERROR")
            return False
            
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to get alerts: {e}", "ERROR")
        return False

def create_test_events():
    """Create some test audit events for querying"""
    print_status("Creating test audit events...")
    
    test_events = [
        {
            "event_type": "LOGIN",
            "action": "user_login",
            "status": "success",
            "severity": "INFO",
            "service_name": "auth-service",
            "user_id": "test-user-1",
            "tenant_id": "test-tenant",
            "metadata": {"ip_address": "192.168.1.100"}
        },
        {
            "event_type": "SECURITY_EVENT",
            "action": "failed_login_attempt",
            "status": "failed",
            "severity": "HIGH",
            "service_name": "auth-service",
            "user_id": "test-user-2",
            "tenant_id": "test-tenant",
            "metadata": {"ip_address": "192.168.1.101"}
        },
        {
            "event_type": "CREATE",
            "action": "create_document",
            "status": "success",
            "severity": "INFO",
            "service_name": "api-service",
            "user_id": "test-user-1",
            "tenant_id": "test-tenant",
            "metadata": {"resource_type": "document"}
        },
        {
            "event_type": "DELETE",
            "action": "delete_user",
            "status": "success",
            "severity": "CRITICAL",
            "service_name": "admin-service",
            "user_id": "admin-user",
            "tenant_id": "test-tenant",
            "metadata": {"resource_type": "user"}
        }
    ]
    
    try:
        for event in test_events:
            response = requests.post(
                f"{BASE_URL}/api/v1/audit/events",
                json=event,
                timeout=10
            )
            
            if response.status_code == 201:
                print_status(f"Created test event: {event['event_type']}", "SUCCESS")
            else:
                print_status(f"Failed to create test event: {response.status_code}", "WARNING")
                
    except requests.exceptions.RequestException as e:
        print_status(f"Failed to create test events: {e}", "WARNING")

def main():
    """Main test function"""
    print_status("Starting MCP functionality tests...", "INFO")
    print()
    
    # Test results tracking
    tests_passed = 0
    tests_failed = 0
    
    # Test MCP service health
    if test_mcp_health():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test MCP capabilities
    if test_mcp_capabilities():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Create test events
    create_test_events()
    
    # Wait a moment for events to be processed
    time.sleep(2)
    
    # Test natural language queries
    test_queries = [
        ("Show me all login events from today", "search_results"),
        ("How many failed authentication attempts in the last hour?", "analytics"),
        ("Get high severity events from the API service", "search_results"),
        ("Show me trends in user activity over the past week", "trends"),
        ("What are the recent security alerts?", "alerts"),
        ("Give me a summary of today's events", "summary"),
        ("Count all events by severity", "analytics"),
        ("Show me critical events from the last hour", "search_results"),
        ("Get events from the auth service", "search_results"),
        ("Show me failed events", "search_results")
    ]
    
    for query, expected_type in test_queries:
        if test_natural_language_query(query, expected_type):
            tests_passed += 1
        else:
            tests_failed += 1
    
    # Test GET queries
    get_queries = [
        ("Show me all login events", "search_results"),
        ("Count events by type", "analytics"),
        ("Get recent alerts", "alerts")
    ]
    
    for query, expected_type in get_queries:
        if test_get_query(query, expected_type):
            tests_passed += 1
        else:
            tests_failed += 1
    
    # Test specific endpoints
    if test_mcp_summary():
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_mcp_trends():
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_mcp_alerts():
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Print summary
    print()
    print_status("=" * 50, "INFO")
    print_status("MCP FUNCTIONALITY TEST SUMMARY", "INFO")
    print_status("=" * 50, "INFO")
    print_status(f"Tests Passed: {tests_passed}", "SUCCESS")
    print_status(f"Tests Failed: {tests_failed}", "ERROR" if tests_failed > 0 else "SUCCESS")
    print_status(f"Total Tests: {tests_passed + tests_failed}", "INFO")
    
    if tests_failed == 0:
        print_status("🎉 All MCP tests passed successfully!", "SUCCESS")
        return 0
    else:
        print_status("❌ Some MCP tests failed. Please check the logs above.", "ERROR")
        return 1

if __name__ == "__main__":
    exit(main())
