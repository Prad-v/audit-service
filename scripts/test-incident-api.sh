#!/bin/bash

# Test Incident API Script
# This script tests the incident API endpoints to verify they are working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
EVENTS_SERVICE_URL="http://localhost:8003"
NAMESPACE="default"
TIMEOUT=30

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -u, --url URL           Events service URL (default: http://localhost:8003)
    -n, --namespace NS      Kubernetes namespace (default: default)
    -t, --timeout SECONDS   Request timeout in seconds (default: 30)
    -h, --help              Show this help message

Examples:
    # Test with default settings
    $0

    # Test with custom URL
    $0 -u http://audit.example.com/events

    # Test in specific namespace
    $0 -n audit-service
EOF
}

# Function to check if service is accessible
check_service_health() {
    print_status "Checking events service health..."
    
    if curl -s --max-time $TIMEOUT "$EVENTS_SERVICE_URL/health" > /dev/null; then
        print_success "Events service is accessible at $EVENTS_SERVICE_URL"
        return 0
    else
        print_error "Events service is not accessible at $EVENTS_SERVICE_URL"
        return 1
    fi
}

# Function to test incident creation
test_create_incident() {
    print_status "Testing incident creation..."
    
    local incident_data='{
        "title": "Test Incident",
        "description": "This is a test incident created by the API test script",
        "severity": "medium",
        "incident_type": "outage",
        "affected_services": ["test-service"],
        "affected_regions": ["us-east-1"],
        "affected_components": ["api", "database"],
        "start_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
        "public_message": "We are investigating a service outage",
        "internal_notes": "Test incident for API validation",
        "is_public": true,
        "rss_enabled": true
    }'
    
    local response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$incident_data" \
        "$EVENTS_SERVICE_URL/api/v1/incidents/")
    
    if [ $? -eq 0 ]; then
        local incident_id=$(echo "$response" | jq -r '.incident.id // empty')
        if [ -n "$incident_id" ]; then
            print_success "Incident created successfully with ID: $incident_id" >&2
            echo "$incident_id"
            return 0
        else
            print_error "Failed to create incident: $response"
            return 1
        fi
    else
        print_error "Failed to connect to incident creation endpoint"
        return 1
    fi
}

# Function to test incident listing
test_list_incidents() {
    print_status "Testing incident listing..."
    
    local response=$(curl -s --max-time $TIMEOUT \
        "$EVENTS_SERVICE_URL/api/v1/incidents/")
    
    if [ $? -eq 0 ]; then
        local count=$(echo "$response" | jq -r '.total // 0')
        print_success "Successfully retrieved incidents. Total count: $count"
        return 0
    else
        print_error "Failed to retrieve incidents: $response"
        return 1
    fi
}

# Function to test incident updates
test_incident_updates() {
    local incident_id=$1
    
    if [ -z "$incident_id" ]; then
        print_warning "No incident ID provided, skipping update test"
        return 0
    fi
    
    print_status "Testing incident updates for ID: $incident_id"
    
    local update_data='{
        "status": "investigating",
        "message": "Update: We are actively investigating this incident",
        "public_message": "We are investigating the reported issue",
        "internal_notes": "Test update via API",
        "update_type": "status_update"
    }'
    
    local response=$(curl -s --max-time $TIMEOUT \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$update_data" \
        "$EVENTS_SERVICE_URL/api/v1/incidents/$incident_id/updates")
    
    if [ $? -eq 0 ]; then
        local update_id=$(echo "$response" | jq -r '.last_update.id // empty')
        if [ -n "$update_id" ]; then
            print_success "Incident update created successfully with ID: $update_id"
            return 0
        else
            print_error "Failed to create incident update: $response"
            return 1
        fi
    else
        print_error "Failed to connect to incident update endpoint"
        return 1
    fi
}

# Function to test subscriptions API
test_subscriptions() {
    print_status "Testing subscriptions API..."
    
    local response=$(curl -s --max-time $TIMEOUT \
        "$EVENTS_SERVICE_URL/api/v1/subscriptions/")
    
    if [ $? -eq 0 ]; then
        local count=$(echo "$response" | jq -r '.total // 0')
        print_success "Successfully retrieved subscriptions. Total count: $count"
        return 0
    else
        print_error "Failed to retrieve subscriptions: $response"
        return 1
    fi
}

# Function to test events API
test_events() {
    print_status "Testing events API..."
    
    local response=$(curl -s --max-time $TIMEOUT \
        "$EVENTS_SERVICE_URL/api/v1/events/")
    
    if [ $? -eq 0 ]; then
        local count=$(echo "$response" | jq -r '.total // 0')
        print_success "Successfully retrieved events. Total count: $count"
        return 0
    else
        print_error "Failed to retrieve events: $response"
        return 1
    fi
}

# Function to check Kubernetes deployment
check_k8s_deployment() {
    print_status "Checking Kubernetes deployment..."
    
    if command -v kubectl >/dev/null 2>&1; then
        local events_pods=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=events --no-headers 2>/dev/null | wc -l)
        if [ "$events_pods" -gt 0 ]; then
            print_success "Found $events_pods events service pods in namespace $NAMESPACE"
            
            # Check pod status
            local running_pods=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=events --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l)
            if [ "$running_pods" -gt 0 ]; then
                print_success "$running_pods events service pods are running"
            else
                print_warning "No events service pods are in Running state"
            fi
        else
            print_warning "No events service pods found in namespace $NAMESPACE"
        fi
    else
        print_warning "kubectl not found, skipping Kubernetes deployment check"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--url)
            EVENTS_SERVICE_URL="$2"
            shift 2
            ;;
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Incident API Test Script"
    print_status "Events Service URL: $EVENTS_SERVICE_URL"
    print_status "Namespace: $NAMESPACE"
    print_status "Timeout: ${TIMEOUT}s"
    echo
    
    local tests_passed=0
    local tests_total=0
    
    # Check service health
    tests_total=$((tests_total + 1))
    if check_service_health; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Check Kubernetes deployment
    tests_total=$((tests_total + 1))
    if check_k8s_deployment; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test subscriptions API
    tests_total=$((tests_total + 1))
    if test_subscriptions; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test events API
    tests_total=$((tests_total + 1))
    if test_events; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test incident listing
    tests_total=$((tests_total + 1))
    if test_list_incidents; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test incident creation
    tests_total=$((tests_total + 1))
    local incident_id=""
    if incident_id=$(test_create_incident); then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test incident updates
    tests_total=$((tests_total + 1))
    if test_incident_updates "$incident_id"; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Summary
    echo
    print_status "Test Summary: $tests_passed/$tests_total tests passed"
    
    if [ $tests_passed -eq $tests_total ]; then
        print_success "All tests passed! Incident API is working correctly."
        exit 0
    else
        print_error "Some tests failed. Please check the events service deployment and configuration."
        exit 1
    fi
}

# Check dependencies
if ! command -v curl >/dev/null 2>&1; then
    print_error "curl is required but not installed"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    print_error "jq is required but not installed"
    exit 1
fi

# Run main function
main "$@"
