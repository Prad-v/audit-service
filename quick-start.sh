#!/bin/bash

# Quick Start Script for Audit Service
# This script provides a one-command setup for new machines

set -e

echo "=================================="
echo "Audit Service - Quick Start"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check prerequisites
print_header "Checking prerequisites..."

if ! command -v docker > /dev/null 2>&1; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v make > /dev/null 2>&1; then
    print_error "Make is not installed. Please install Make first."
    exit 1
fi

print_status "Prerequisites check passed!"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

print_status "Docker is running!"

# Setup environment
print_header "Setting up environment..."
make setup-env

# Setup databases
print_header "Setting up databases..."
make create-db
make setup-db

# Build and start services
print_header "Building and starting services..."
make build
make start

# Wait for services to be ready
print_header "Waiting for services to be ready..."
sleep 30

# Check health
print_header "Checking service health..."
make health

print_status "=================================="
print_status "Setup completed successfully!"
print_status "=================================="
print_status "Application is available at:"
print_status "  Frontend: http://localhost:3000"
print_status "  Backend API: http://localhost:8000"
print_status "  StackStorm Tests: http://localhost:8004"
print_status "=================================="
print_status "Useful commands:"
print_status "  make logs          - View all logs"
print_status "  make health        - Check service health"
print_status "  make stop          - Stop all services"
print_status "  make restart       - Restart all services"
print_status "  make clean         - Clean up everything"
print_status "=================================="
