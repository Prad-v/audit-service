#!/usr/bin/env python3
"""
Test script to verify Grafana dashboard functionality.
"""

import requests
import json
import time
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

GRAFANA_URL = "http://localhost:3001"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

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

def test_grafana_health():
    """Test Grafana health."""
    print_header("Testing Grafana Health")
    
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Grafana is healthy (Version: {data.get('version', 'unknown')})")
            return True
        else:
            print_error(f"Grafana health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Grafana health error: {e}")
        return False

def test_datasource():
    """Test PostgreSQL datasource."""
    print_header("Testing PostgreSQL Datasource")
    
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/datasources",
            auth=(GRAFANA_USER, GRAFANA_PASS),
            timeout=10
        )
        
        if response.status_code == 200:
            datasources = response.json()
            
            postgres_ds = None
            for ds in datasources:
                if ds.get('type') == 'postgres':
                    postgres_ds = ds
                    break
            
            if postgres_ds:
                print_success(f"PostgreSQL datasource found: {postgres_ds.get('name')}")
                print_info(f"UID: {postgres_ds.get('uid')}")
                print_info(f"URL: {postgres_ds.get('url')}")
                print_info(f"Database: {postgres_ds.get('jsonData', {}).get('database')}")
                return True
            else:
                print_error("PostgreSQL datasource not found")
                return False
        else:
            print_error(f"Failed to get datasources: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Datasource test error: {e}")
        return False

def test_dashboard():
    """Test dashboard availability."""
    print_header("Testing Dashboard Availability")
    
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/dashboards/uid/audit-service",
            auth=(GRAFANA_USER, GRAFANA_PASS),
            timeout=10
        )
        
        if response.status_code == 200:
            dashboard = response.json()
            dashboard_data = dashboard.get('dashboard', {})
            
            print_success(f"Dashboard found: {dashboard_data.get('title')}")
            print_info(f"UID: {dashboard_data.get('uid')}")
            print_info(f"Version: {dashboard_data.get('version')}")
            
            # Check panels
            panels = dashboard_data.get('panels', [])
            print_info(f"Number of panels: {len(panels)}")
            
            # Check if panels are using PostgreSQL datasource
            postgres_panels = 0
            for panel in panels:
                datasource = panel.get('datasource', {})
                if isinstance(datasource, dict) and datasource.get('uid') == 'postgres':
                    postgres_panels += 1
            
            print_info(f"Panels using PostgreSQL: {postgres_panels}/{len(panels)}")
            
            if postgres_panels == len(panels):
                print_success("All panels are configured to use PostgreSQL datasource")
                return True
            else:
                print_error(f"Only {postgres_panels}/{len(panels)} panels use PostgreSQL")
                return False
        else:
            print_error(f"Failed to get dashboard: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Dashboard test error: {e}")
        return False

def test_dashboard_access():
    """Test dashboard web access."""
    print_header("Testing Dashboard Web Access")
    
    try:
        response = requests.get(f"{GRAFANA_URL}/d/audit-service/audit-service-dashboard", timeout=10)
        if response.status_code == 200:
            print_success("Dashboard is accessible via web interface")
            return True
        else:
            print_error(f"Dashboard web access failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Dashboard web access error: {e}")
        return False

def main():
    """Main test function."""
    print_header("Grafana Dashboard Test")
    
    results = []
    
    # Run tests
    results.append(("Grafana Health", test_grafana_health()))
    results.append(("PostgreSQL Datasource", test_datasource()))
    results.append(("Dashboard Configuration", test_dashboard()))
    results.append(("Dashboard Web Access", test_dashboard_access()))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if result else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        print(f"{status} {test_name}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")
    
    if passed == total:
        print_success("🎉 Grafana dashboard is working correctly!")
        print_info(f"\nAccess your dashboard at: {GRAFANA_URL}")
        print_info("Username: admin")
        print_info("Password: admin123")
    else:
        print_error(f"❌ {total - passed} tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
