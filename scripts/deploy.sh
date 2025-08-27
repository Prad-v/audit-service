#!/bin/bash

# Audit Log Framework Deployment Script
# This script automates the deployment process for different environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-development}
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="$PROJECT_ROOT/backups"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_environment() {
    log_info "Setting up environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    # Create environment file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_info "Created .env file from .env.example"
        else
            log_error ".env.example file not found"
            exit 1
        fi
    fi
    
    # Set compose file based on environment
    case $ENVIRONMENT in
        production)
            if [[ -f "docker-compose.prod.yml" ]]; then
                COMPOSE_FILE="docker-compose.yml:docker-compose.prod.yml"
            fi
            ;;
        staging)
            if [[ -f "docker-compose.staging.yml" ]]; then
                COMPOSE_FILE="docker-compose.yml:docker-compose.staging.yml"
            fi
            ;;
        development)
            COMPOSE_FILE="docker-compose.yml"
            ;;
        *)
            log_warning "Unknown environment: $ENVIRONMENT. Using development configuration."
            ENVIRONMENT="development"
            ;;
    esac
    
    log_success "Environment setup completed"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    # Create data directories
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p data/nats
    mkdir -p data/prometheus
    mkdir -p data/grafana
    mkdir -p logs
    mkdir -p "$BACKUP_DIR"
    
    # Set permissions
    chmod 755 data/
    chmod 755 logs/
    chmod 755 "$BACKUP_DIR"
    
    log_success "Directories created"
}

pull_images() {
    log_info "Pulling Docker images..."
    
    IFS=':' read -ra COMPOSE_FILES <<< "$COMPOSE_FILE"
    COMPOSE_ARGS=""
    for file in "${COMPOSE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_ARGS="$COMPOSE_ARGS -f $file"
        fi
    done
    
    docker-compose $COMPOSE_ARGS pull
    
    log_success "Docker images pulled"
}

build_images() {
    log_info "Building application images..."
    
    IFS=':' read -ra COMPOSE_FILES <<< "$COMPOSE_FILE"
    COMPOSE_ARGS=""
    for file in "${COMPOSE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_ARGS="$COMPOSE_ARGS -f $file"
        fi
    done
    
    docker-compose $COMPOSE_ARGS build --no-cache
    
    log_success "Application images built"
}

start_infrastructure() {
    log_info "Starting infrastructure services..."
    
    IFS=':' read -ra COMPOSE_FILES <<< "$COMPOSE_FILE"
    COMPOSE_ARGS=""
    for file in "${COMPOSE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_ARGS="$COMPOSE_ARGS -f $file"
        fi
    done
    
    # Start infrastructure services first
    docker-compose $COMPOSE_ARGS up -d postgres redis nats
    
    # Wait for services to be ready
    log_info "Waiting for infrastructure services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health "postgres" "5432"
    check_service_health "redis" "6379"
    check_service_health "nats" "4222"
    
    log_success "Infrastructure services started"
}

check_service_health() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log_info "Checking health of $service service..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose exec -T $service sh -c "exit 0" &> /dev/null; then
            log_success "$service service is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    log_error "$service service failed to start properly"
    return 1
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Wait a bit more for database to be fully ready
    sleep 10
    
    # Run migrations
    if docker-compose exec -T api python -m alembic upgrade head; then
        log_success "Database migrations completed"
    else
        log_error "Database migrations failed"
        return 1
    fi
}

start_application() {
    log_info "Starting application services..."
    
    IFS=':' read -ra COMPOSE_FILES <<< "$COMPOSE_FILE"
    COMPOSE_ARGS=""
    for file in "${COMPOSE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_ARGS="$COMPOSE_ARGS -f $file"
        fi
    done
    
    # Start application services
    docker-compose $COMPOSE_ARGS up -d api worker
    
    # Wait for application to be ready
    log_info "Waiting for application services to be ready..."
    sleep 20
    
    # Check application health
    check_application_health
    
    log_success "Application services started"
}

start_monitoring() {
    log_info "Starting monitoring services..."
    
    IFS=':' read -ra COMPOSE_FILES <<< "$COMPOSE_FILE"
    COMPOSE_ARGS=""
    for file in "${COMPOSE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_ARGS="$COMPOSE_ARGS -f $file"
        fi
    done
    
    # Start monitoring services
    docker-compose $COMPOSE_ARGS up -d prometheus grafana alertmanager node-exporter postgres-exporter redis-exporter nats-exporter cadvisor
    
    log_success "Monitoring services started"
}

start_frontend() {
    log_info "Starting frontend service..."
    
    IFS=':' read -ra COMPOSE_FILES <<< "$COMPOSE_FILE"
    COMPOSE_ARGS=""
    for file in "${COMPOSE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            COMPOSE_ARGS="$COMPOSE_ARGS -f $file"
        fi
    done
    
    # Start frontend service
    docker-compose $COMPOSE_ARGS up -d frontend
    
    log_success "Frontend service started"
}

check_application_health() {
    local max_attempts=30
    local attempt=1
    
    log_info "Checking application health..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Application is healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Application not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Application health check failed"
    return 1
}

create_initial_data() {
    log_info "Creating initial data..."
    
    # Create admin user if it doesn't exist
    if docker-compose exec -T api python -c "
from app.db.database import get_database_manager
from app.db.schemas import User
from sqlalchemy import select
import asyncio

async def check_admin():
    db_manager = get_database_manager()
    await db_manager.initialize()
    async with db_manager.get_session() as session:
        result = await session.execute(select(User).where(User.email == 'admin@audit-system.local'))
        return result.scalar_one_or_none() is not None

if not asyncio.run(check_admin()):
    exit(1)
"; then
        log_info "Admin user already exists"
    else
        log_info "Creating admin user..."
        docker-compose exec -T api python -c "
import asyncio
from app.services.auth_service import AuthService
from app.db.database import get_database_manager

async def create_admin():
    db_manager = get_database_manager()
    await db_manager.initialize()
    auth_service = AuthService(db_manager)
    
    admin_user = await auth_service.create_user(
        email='admin@audit-system.local',
        password='admin123',
        full_name='System Administrator',
        is_active=True,
        is_superuser=True
    )
    print(f'Admin user created: {admin_user.email}')

asyncio.run(create_admin())
"
        log_success "Admin user created"
    fi
}

show_deployment_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "=== Service URLs ==="
    echo "API:          http://localhost:8000"
    echo "Frontend:     http://localhost:3000"
    echo "Prometheus:   http://localhost:9090"
    echo "Grafana:      http://localhost:3001 (admin/admin123)"
    echo "AlertManager: http://localhost:9093"
    echo
    echo "=== Health Checks ==="
    echo "API Health:   curl http://localhost:8000/health"
    echo "Metrics:      curl http://localhost:8000/api/v1/metrics"
    echo
    echo "=== Useful Commands ==="
    echo "View logs:    docker-compose logs -f"
    echo "Stop all:     docker-compose down"
    echo "Restart:      docker-compose restart"
    echo
    echo "=== Default Credentials ==="
    echo "Admin User:   admin@audit-system.local / admin123"
    echo "Grafana:      admin / admin123"
    echo
}

backup_before_deploy() {
    if [[ "$ENVIRONMENT" == "production" ]] && [[ -d "data" ]]; then
        log_info "Creating backup before deployment..."
        
        local backup_name="pre-deploy-$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR/$backup_name"
        
        # Backup database
        if docker-compose ps postgres | grep -q "Up"; then
            docker-compose exec -T postgres pg_dump -U audit_user audit_logs | gzip > "$BACKUP_DIR/$backup_name/database.sql.gz"
        fi
        
        # Backup configuration and data
        tar -czf "$BACKUP_DIR/$backup_name/data.tar.gz" data/ || true
        cp .env "$BACKUP_DIR/$backup_name/" || true
        
        log_success "Backup created: $backup_name"
    fi
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused images (be careful in production)
    if [[ "$ENVIRONMENT" != "production" ]]; then
        docker image prune -a -f
    fi
    
    log_success "Docker cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting deployment for environment: $ENVIRONMENT"
    
    check_prerequisites
    setup_environment
    create_directories
    backup_before_deploy
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose down || true
    
    pull_images
    build_images
    start_infrastructure
    run_migrations
    start_application
    create_initial_data
    start_monitoring
    start_frontend
    
    cleanup_old_images
    show_deployment_info
    
    log_success "Deployment completed successfully!"
}

# Script usage
usage() {
    echo "Usage: $0 [environment]"
    echo
    echo "Environments:"
    echo "  development  - Local development (default)"
    echo "  staging      - Staging environment"
    echo "  production   - Production environment"
    echo
    echo "Examples:"
    echo "  $0                    # Deploy to development"
    echo "  $0 development        # Deploy to development"
    echo "  $0 production         # Deploy to production"
    echo
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    ""|development|staging|production)
        deploy
        ;;
    *)
        log_error "Invalid environment: $1"
        usage
        exit 1
        ;;
esac