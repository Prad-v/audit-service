#!/usr/bin/env python3
"""
Dynamic Filter Examples

This script demonstrates how to use the dynamic filtering functionality
for querying audit events with flexible field filtering.
"""

import json
import requests
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "test-token"  # Replace with your actual API key

def make_request(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the audit API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    url = f"{API_BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return {}

def print_example(title: str, description: str, params: Dict[str, Any], results: Dict[str, Any]):
    """Print a formatted example."""
    print(f"\n{'='*60}")
    print(f"EXAMPLE: {title}")
    print(f"{'='*60}")
    print(f"Description: {description}")
    print(f"\nParameters:")
    print(json.dumps(params, indent=2))
    print(f"\nResults:")
    print(f"Total events: {results.get('total_count', 0)}")
    print(f"Page: {results.get('page', 1)}")
    print(f"Page size: {results.get('page_size', 50)}")
    
    items = results.get('items', [])
    if items:
        print(f"\nSample events:")
        for i, item in enumerate(items[:3]):  # Show first 3 events
            print(f"  {i+1}. {item.get('event_type')} - {item.get('user_id')} - {item.get('status')}")
    else:
        print("  No events found")

def example_1_basic_equals_filter():
    """Example 1: Basic equals filter."""
    title = "Find all user login events"
    description = "Use dynamic filter to find all events where event_type equals 'user_login'"
    
    dynamic_filters = [
        {
            "field": "event_type",
            "operator": "eq",
            "value": "user_login"
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_2_not_equals_filter():
    """Example 2: Not equals filter."""
    title = "Find all non-success events"
    description = "Use dynamic filter to find all events where status is not 'success'"
    
    dynamic_filters = [
        {
            "field": "status",
            "operator": "ne",
            "value": "success"
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_3_contains_filter():
    """Example 3: Contains filter for nested JSON field."""
    title = "Find events with admin in user_id metadata"
    description = "Use dynamic filter to find events where metadata.user_id contains 'admin'"
    
    dynamic_filters = [
        {
            "field": "metadata.user_id",
            "operator": "contains",
            "value": "admin",
            "case_sensitive": False
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_4_in_list_filter():
    """Example 4: In list filter."""
    title = "Find events with specific event types"
    description = "Use dynamic filter to find events where event_type is in a list of values"
    
    dynamic_filters = [
        {
            "field": "event_type",
            "operator": "in",
            "value": ["user_login", "user_logout", "data_access"]
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_5_starts_with_filter():
    """Example 5: Starts with filter."""
    title = "Find events from internal network"
    description = "Use dynamic filter to find events where IP address starts with '192.168'"
    
    dynamic_filters = [
        {
            "field": "ip_address",
            "operator": "starts_with",
            "value": "192.168"
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_6_greater_than_filter():
    """Example 6: Greater than filter for nested JSON field."""
    title = "Find events with error status codes"
    description = "Use dynamic filter to find events where response_data.status_code >= 400"
    
    dynamic_filters = [
        {
            "field": "response_data.status_code",
            "operator": "gte",
            "value": 400
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_7_is_null_filter():
    """Example 7: Is null filter."""
    title = "Find events with missing correlation IDs"
    description = "Use dynamic filter to find events where correlation_id is null"
    
    dynamic_filters = [
        {
            "field": "correlation_id",
            "operator": "is_null"
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_8_multiple_filters():
    """Example 8: Multiple filters (AND condition)."""
    title = "Find failed login attempts from internal network"
    description = "Use multiple dynamic filters to find failed login events from internal network"
    
    dynamic_filters = [
        {
            "field": "event_type",
            "operator": "eq",
            "value": "user_login"
        },
        {
            "field": "status",
            "operator": "eq",
            "value": "failed"
        },
        {
            "field": "ip_address",
            "operator": "starts_with",
            "value": "192.168"
        }
    ]
    
    params = {
        "dynamic_filters": json.dumps(dynamic_filters),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_9_filter_group_or():
    """Example 9: Filter group with OR condition."""
    title = "Find login or logout events"
    description = "Use filter group to find events where event_type is either 'user_login' OR 'user_logout'"
    
    filter_groups = [
        {
            "filters": [
                {
                    "field": "event_type",
                    "operator": "eq",
                    "value": "user_login"
                },
                {
                    "field": "event_type",
                    "operator": "eq",
                    "value": "user_logout"
                }
            ],
            "operator": "OR"
        }
    ]
    
    params = {
        "filter_groups": json.dumps(filter_groups),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def example_10_complex_filter_group():
    """Example 10: Complex filter group with AND/OR combinations."""
    title = "Find admin activities or failed events from internal network"
    description = "Use complex filter group to find admin activities OR failed events from internal network"
    
    filter_groups = [
        {
            "filters": [
                {
                    "field": "metadata.user_id",
                    "operator": "contains",
                    "value": "admin"
                }
            ],
            "operator": "AND"
        },
        {
            "filters": [
                {
                    "field": "status",
                    "operator": "eq",
                    "value": "failed"
                },
                {
                    "field": "ip_address",
                    "operator": "starts_with",
                    "value": "192.168"
                }
            ],
            "operator": "AND"
        }
    ]
    
    params = {
        "filter_groups": json.dumps(filter_groups),
        "page": 1,
        "size": 10
    }
    
    results = make_request("/api/v1/audit/events", params)
    print_example(title, description, params, results)

def get_filter_info():
    """Get information about available fields and operators."""
    print(f"\n{'='*60}")
    print("FILTER INFORMATION")
    print(f"{'='*60}")
    
    results = make_request("/api/v1/audit/filters/info")
    
    if results:
        print(f"Available fields: {len(results.get('available_fields', []))}")
        print(f"Supported operators: {len(results.get('supported_operators', []))}")
        print(f"Examples: {len(results.get('examples', []))}")
        
        print(f"\nSample available fields:")
        fields = results.get('available_fields', [])
        for field in fields[:10]:  # Show first 10 fields
            print(f"  - {field}")
        
        print(f"\nSupported operators:")
        operators = results.get('supported_operators', [])
        for operator in operators:
            print(f"  - {operator}")
        
        print(f"\nSample examples:")
        examples = results.get('examples', [])
        for i, example in enumerate(examples[:3]):  # Show first 3 examples
            print(f"  {i+1}. {example.get('description')}")
            print(f"     Field: {example.get('field')}")
            print(f"     Operator: {example.get('operator')}")
            print(f"     Value: {example.get('value')}")

def main():
    """Run all examples."""
    print("Dynamic Filter Examples for Audit Service API")
    print("=" * 60)
    
    # Get filter information first
    get_filter_info()
    
    # Run examples
    examples = [
        example_1_basic_equals_filter,
        example_2_not_equals_filter,
        example_3_contains_filter,
        example_4_in_list_filter,
        example_5_starts_with_filter,
        example_6_greater_than_filter,
        example_7_is_null_filter,
        example_8_multiple_filters,
        example_9_filter_group_or,
        example_10_complex_filter_group
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError running example: {e}")
    
    print(f"\n{'='*60}")
    print("All examples completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
