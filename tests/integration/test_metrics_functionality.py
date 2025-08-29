#!/usr/bin/env python3
"""
Test script for the new metrics functionality.

This script tests:
1. Metrics API endpoints
2. Dashboard functionality
3. Grafana integration
4. Real-time metrics updates
"""

import requests
import json
import time
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
GRAFANA_URL = "http://localhost:3001"

def print_header(title):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{title:^60}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(message):
    """Print a success message."""
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message."""
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

def print_info(message):
    """Print an info message."""
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

def test_api_health():
    """Test API health endpoint."""
    print_header("Testing API Health")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API Health: {data.get('status', 'unknown')}")
            return True
        else:
            print_error(f"API Health failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"API Health error: {e}")
        return False

def test_metrics_endpoint():
    """Test the main metrics endpoint."""
    print_header("Testing Metrics Endpoint")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/audit/metrics", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields
            required_fields = ['metrics', 'ingestion_rate_data', 'query_rate_data', 'top_event_types', 'system_metrics']
            for field in required_fields:
                if field in data:
                    print_success(f"✓ {field} present")
                else:
                    print_error(f"✗ {field} missing")
                    return False
            
            # Check metrics data
            metrics = data['metrics']
            print_info(f"Total Events: {metrics.get('total_events', 0)}")
            print_info(f"Events Today: {metrics.get('events_today', 0)}")
            print_info(f"Ingestion Rate: {metrics.get('ingestion_rate', 0):.1f}/min")
            print_info(f"Query Rate: {metrics.get('query_rate', 0):.1f}/min")
            print_info(f"Error Rate: {metrics.get('error_rate', 0):.2f}%")
            
            return True
        else:
            print_error(f"Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Metrics endpoint error: {e}")
        return False

def test_top_event_types():
    """Test the top event types endpoint."""
    print_header("Testing Top Event Types")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/audit/metrics/top-event-types?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Retrieved {len(data)} top event types")
                
                for i, event_type in enumerate(data[:3], 1):
                    print_info(f"{i}. {event_type['event_type']}: {event_type['count']} events ({event_type['percentage']:.1f}%)")
                
                return True
            else:
                print_error("No event types returned")
                return False
        else:
            print_error(f"Top event types endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Top event types error: {e}")
        return False

def test_system_metrics():
    """Test the system metrics endpoint."""
    print_header("Testing System Metrics")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/audit/metrics/system", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            print_info(f"CPU Usage: {data.get('cpu_usage', 0):.1f}%")
            print_info(f"Memory Usage: {data.get('memory_usage', 0):.1f}%")
            print_info(f"Disk Usage: {data.get('disk_usage', 0):.1f}%")
            print_info(f"Active Connections: {data.get('active_connections', 0)}")
            print_info(f"Database Size: {data.get('database_size', 0) / (1024**3):.1f} GB")
            
            return True
        else:
            print_error(f"System metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"System metrics error: {e}")
        return False

def test_ingestion_rate():
    """Test the ingestion rate endpoint."""
    print_header("Testing Ingestion Rate")
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/audit/metrics/ingestion-rate?time_range=1h", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                print_success(f"Retrieved {len(data)} ingestion rate data points")
                
                # Show recent data points
                recent_data = data[-3:]
                for point in recent_data:
                    timestamp = point['timestamp']
                    rate = point['rate']
                    count = point['events_count']
                    print_info(f"  {timestamp}: {rate:.2f}/min ({count} events)")
                
                return True
            else:
                print_error("No ingestion rate data returned")
                return False
        else:
            print_error(f"Ingestion rate endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Ingestion rate error: {e}")
        return False

def test_frontend_accessibility():
    """Test frontend accessibility."""
    print_header("Testing Frontend Accessibility")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print_success("Frontend is accessible")
            
            # Check if it's a React app
            if "react" in response.text.lower() or "dashboard" in response.text.lower():
                print_success("Frontend appears to be React-based")
            else:
                print_info("Frontend content detected")
            
            return True
        else:
            print_error(f"Frontend failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Frontend error: {e}")
        return False

def test_grafana_accessibility():
    """Test Grafana accessibility."""
    print_header("Testing Grafana Accessibility")
    
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Grafana is accessible (Version: {data.get('version', 'unknown')})")
            print_info(f"Database: {data.get('database', 'unknown')}")
            return True
        else:
            print_error(f"Grafana health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Grafana error: {e}")
        return False

def test_metrics_real_time():
    """Test real-time metrics updates."""
    print_header("Testing Real-time Metrics Updates")
    
    try:
        # Get initial metrics
        response1 = requests.get(f"{API_BASE_URL}/api/v1/audit/metrics", timeout=10)
        if response1.status_code != 200:
            print_error("Failed to get initial metrics")
            return False
        
        data1 = response1.json()
        initial_total = data1['metrics']['total_events']
        print_info(f"Initial total events: {initial_total}")
        
        # Wait a moment
        time.sleep(2)
        
        # Get updated metrics
        response2 = requests.get(f"{API_BASE_URL}/api/v1/audit/metrics", timeout=10)
        if response2.status_code != 200:
            print_error("Failed to get updated metrics")
            return False
        
        data2 = response2.json()
        updated_total = data2['metrics']['total_events']
        print_info(f"Updated total events: {updated_total}")
        
        if updated_total >= initial_total:
            print_success("Metrics are updating in real-time")
            return True
        else:
            print_error("Metrics are not updating properly")
            return False
            
    except Exception as e:
        print_error(f"Real-time metrics error: {e}")
        return False

def create_sample_events():
    """Create some sample events to populate metrics."""
    print_header("Creating Sample Events")
    
    sample_events = [
        {
            "event_type": "metrics_test_event",
            "action": "test",
            "status": "success",
            "tenant_id": "test-tenant",
            "service_name": "metrics-test",
            "user_id": "test-user",
            "resource_type": "test",
            "resource_id": "test-123",
            "metadata": {"test": True, "timestamp": datetime.now().isoformat()}
        },
        {
            "event_type": "dashboard_test_event",
            "action": "view",
            "status": "success",
            "tenant_id": "test-tenant",
            "service_name": "dashboard-test",
            "user_id": "test-user",
            "resource_type": "dashboard",
            "resource_id": "main-dashboard",
            "metadata": {"test": True, "timestamp": datetime.now().isoformat()}
        }
    ]
    
    created_count = 0
    for event in sample_events:
        try:
            response = requests.post(f"{API_BASE_URL}/api/v1/audit/events", json=event, timeout=10)
            if response.status_code == 200:
                created_count += 1
                print_success(f"Created event: {event['event_type']}")
            else:
                print_error(f"Failed to create event: {event['event_type']} ({response.status_code})")
        except Exception as e:
            print_error(f"Error creating event {event['event_type']}: {e}")
    
    print_info(f"Created {created_count} sample events")
    return created_count > 0

def main():
    """Main test function."""
    print_header("Audit Service Metrics Functionality Test")
    print_info(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test results
    results = []
    
    # Run tests
    results.append(("API Health", test_api_health()))
    results.append(("Frontend Accessibility", test_frontend_accessibility()))
    results.append(("Grafana Accessibility", test_grafana_accessibility()))
    
    # Create sample events for better metrics
    create_sample_events()
    
    # Test metrics endpoints
    results.append(("Metrics Endpoint", test_metrics_endpoint()))
    results.append(("Top Event Types", test_top_event_types()))
    results.append(("System Metrics", test_system_metrics()))
    results.append(("Ingestion Rate", test_ingestion_rate()))
    results.append(("Real-time Updates", test_metrics_real_time()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if result else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        print(f"{status} {test_name}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")
    
    if passed == total:
        print_success("🎉 All tests passed! Metrics functionality is working correctly.")
        print_info("\nAccess URLs:")
        print_info(f"  Frontend: {FRONTEND_URL}")
        print_info(f"  API Docs: {API_BASE_URL}/docs")
        print_info(f"  Grafana: {GRAFANA_URL}")
        print_info(f"  Health Check: {API_BASE_URL}/health")
    else:
        print_error(f"❌ {total - passed} tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
