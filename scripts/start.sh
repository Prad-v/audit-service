#!/bin/bash

# Audit Log Framework Startup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker compose is available
check_docker_compose() {
    if ! docker compose version &> /dev/null; then
        print_error "docker compose is not available. Please install Docker Compose and try again."
        exit 1
    fi
}

# Function to start services
start_services() {
    local mode=$1
    local compose_file="docker-compose.yml"
    
    if [ "$mode" = "dev" ]; then
        compose_file="-f docker-compose.yml -f docker-compose.dev.yml"
        print_status "Starting services in DEVELOPMENT mode..."
    else
        print_status "Starting services in PRODUCTION mode..."
    fi
    
    print_status "Building and starting containers..."
    if [ "$mode" = "dev" ]; then
        docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
    else
        docker compose up --build -d
    fi
    
    print_success "Services started successfully!"
    print_status "Waiting for services to be ready..."
    
    # Wait for API to be ready
    print_status "Waiting for API service..."
    timeout=60
    counter=0
    while ! curl -f http://localhost:8000/health > /dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            print_error "API service failed to start within $timeout seconds"
            exit 1
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    echo ""
    print_success "API service is ready!"
    
    # Wait for frontend to be ready
    print_status "Waiting for frontend service..."
    timeout=30
    counter=0
    while ! curl -f http://localhost:3000 > /dev/null 2>&1; do
        if [ $counter -ge $timeout ]; then
            print_error "Frontend service failed to start within $timeout seconds"
            exit 1
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    echo ""
    print_success "Frontend service is ready!"
}

# Function to show service URLs
show_urls() {
    echo ""
    print_success "🎉 Audit Log Framework is running!"
    echo ""
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "  Frontend:     ${GREEN}http://localhost:3000${NC}"
    echo -e "  API:          ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
    echo -e "  Health Check: ${GREEN}http://localhost:8000/health${NC}"
    echo ""
    echo -e "${BLUE}Database:${NC}"
    echo -e "  PostgreSQL:   ${GREEN}localhost:5432${NC}"
    echo -e "  Redis:        ${GREEN}localhost:6379${NC}"
    echo -e "  NATS:         ${GREEN}localhost:4222${NC}"
    echo ""
    echo -e "${BLUE}Useful Commands:${NC}"
    echo -e "  View logs:    ${YELLOW}docker-compose logs -f${NC}"
    echo -e "  Stop:         ${YELLOW}docker-compose down${NC}"
    echo -e "  Restart:      ${YELLOW}docker-compose restart${NC}"
    echo ""
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    docker compose down
    print_success "Services stopped successfully!"
}

# Function to show logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker compose logs -f
    else
        docker compose logs -f "$service"
    fi
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker compose ps
}

# Main script logic
case "${1:-start}" in
    "start")
        check_docker
        check_docker_compose
        start_services "prod"
        show_urls
        ;;
    "dev")
        check_docker
        check_docker_compose
        start_services "dev"
        show_urls
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        start_services "prod"
        show_urls
        ;;
    "logs")
        show_logs "$2"
        ;;
    "status")
        show_status
        ;;
    "clean")
        print_status "Cleaning up containers and volumes..."
        docker compose down -v --remove-orphans
        docker system prune -f
        print_success "Cleanup completed!"
        ;;
    *)
        echo "Usage: $0 {start|dev|stop|restart|logs|status|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start services in production mode"
        echo "  dev     - Start services in development mode (with hot reload)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show logs (optionally specify service name)"
        echo "  status  - Show service status"
        echo "  clean   - Stop services and clean up volumes"
        exit 1
        ;;
esac
