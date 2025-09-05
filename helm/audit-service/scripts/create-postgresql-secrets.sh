#!/bin/bash

# PostgreSQL Secrets Creation Script for Audit Service Helm Chart
# This script helps create the necessary Kubernetes secrets for PostgreSQL credentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="default"
SECRET_NAME="postgresql-credentials"
INTERNAL_MODE=true

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
    -n, --namespace NAMESPACE    Kubernetes namespace (default: default)
    -s, --secret-name NAME       Secret name (default: postgresql-credentials)
    -e, --external               Create secrets for external PostgreSQL
    -h, --help                   Show this help message

Examples:
    # Create secrets for internal PostgreSQL in default namespace
    $0

    # Create secrets for internal PostgreSQL in specific namespace
    $0 -n audit-service

    # Create secrets for external PostgreSQL
    $0 -e -n audit-service

    # Create secrets with custom secret name
    $0 -s my-postgresql-secret -n audit-service
EOF
}

# Function to generate random password
generate_password() {
    local length=${1:-16}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Function to create internal PostgreSQL secrets
create_internal_secrets() {
    print_status "Creating internal PostgreSQL secrets..."
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(generate_password 24)
    AUDIT_USER_PASSWORD=$(generate_password 24)
    READONLY_USER_PASSWORD=$(generate_password 24)
    
    # Create the secret
    kubectl create secret generic "$SECRET_NAME" \
        --namespace="$NAMESPACE" \
        --from-literal=postgres-password="$POSTGRES_PASSWORD" \
        --from-literal=username="audit_user" \
        --from-literal=password="$AUDIT_USER_PASSWORD" \
        --from-literal=database="audit_logs" \
        --from-literal=readonly_username="readonly_user" \
        --from-literal=readonly_password="$READONLY_USER_PASSWORD" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "Internal PostgreSQL secret '$SECRET_NAME' created in namespace '$NAMESPACE'"
    
    # Display the generated passwords (user should save these securely)
    echo
    print_warning "IMPORTANT: Save these passwords securely:"
    echo "PostgreSQL Superuser Password: $POSTGRES_PASSWORD"
    echo "Audit User Password: $AUDIT_USER_PASSWORD"
    echo "Readonly User Password: $READONLY_USER_PASSWORD"
    echo
}

# Function to create external PostgreSQL secrets
create_external_secrets() {
    print_status "Creating external PostgreSQL secrets..."
    
    # Prompt for external PostgreSQL password
    echo -n "Enter external PostgreSQL password: "
    read -s EXTERNAL_PASSWORD
    echo
    
    # Create the secret
    kubectl create secret generic "$SECRET_NAME" \
        --namespace="$NAMESPACE" \
        --from-literal=password="$EXTERNAL_PASSWORD" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    print_success "External PostgreSQL secret '$SECRET_NAME' created in namespace '$NAMESPACE'"
}

# Function to verify secret creation
verify_secret() {
    print_status "Verifying secret creation..."
    
    if kubectl get secret "$SECRET_NAME" --namespace="$NAMESPACE" >/dev/null 2>&1; then
        print_success "Secret '$SECRET_NAME' exists in namespace '$NAMESPACE'"
        
        # Show secret details
        echo
        print_status "Secret details:"
        kubectl get secret "$SECRET_NAME" --namespace="$NAMESPACE" -o yaml | grep -E "(name:|type:|data:)" -A 10
    else
        print_error "Failed to create secret '$SECRET_NAME' in namespace '$NAMESPACE'"
        exit 1
    fi
}

# Function to create namespace if it doesn't exist
create_namespace_if_needed() {
    if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        print_status "Creating namespace '$NAMESPACE'..."
        kubectl create namespace "$NAMESPACE"
        print_success "Namespace '$NAMESPACE' created"
    else
        print_status "Namespace '$NAMESPACE' already exists"
    fi
}

# Function to check kubectl connectivity
check_kubectl() {
    if ! kubectl cluster-info >/dev/null 2>&1; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    print_success "Connected to Kubernetes cluster"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -s|--secret-name)
            SECRET_NAME="$2"
            shift 2
            ;;
        -e|--external)
            INTERNAL_MODE=false
            shift
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
    print_status "PostgreSQL Secrets Creation Script for Audit Service"
    echo
    
    # Check prerequisites
    check_kubectl
    
    # Create namespace if needed
    create_namespace_if_needed
    
    # Create secrets based on mode
    if [ "$INTERNAL_MODE" = true ]; then
        create_internal_secrets
    else
        create_external_secrets
    fi
    
    # Verify secret creation
    verify_secret
    
    echo
    print_success "PostgreSQL secrets setup completed successfully!"
    
    # Show next steps
    echo
    print_status "Next steps:"
    if [ "$INTERNAL_MODE" = true ]; then
        echo "1. Update your Helm values to use the created secret"
        echo "2. Deploy the audit-service with: helm upgrade --install audit-service ./helm/audit-service"
        echo "3. Store the generated passwords securely"
    else
        echo "1. Update your Helm values for external PostgreSQL"
        echo "2. Deploy the audit-service with: helm upgrade --install audit-service ./helm/audit-service"
        echo "3. Ensure your external PostgreSQL is accessible"
    fi
}

# Run main function
main "$@"
