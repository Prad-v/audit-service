#!/bin/bash

# Audit Log Framework Restore Script
# This script restores the system from backups

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
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups}"
BACKUP_NAME="$1"

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

usage() {
    echo "Usage: $0 <backup_name> [options]"
    echo
    echo "Arguments:"
    echo "  backup_name          Name of the backup to restore (e.g., backup_20250827_143000)"
    echo
    echo "Options:"
    echo "  --database-only      Restore only the database"
    echo "  --config-only        Restore only configuration files"
    echo "  --data-only          Restore only application data"
    echo "  --force              Skip confirmation prompts"
    echo "  -h, --help           Show this help message"
    echo
    echo "Examples:"
    echo "  $0 backup_20250827_143000                    # Full restore"
    echo "  $0 backup_20250827_143000 --database-only    # Database only"
    echo "  $0 backup_20250827_143000 --force            # Skip confirmations"
    echo
}

validate_backup() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup directory not found: $backup_path"
        echo
        echo "Available backups:"
        ls -la "$BACKUP_DIR" | grep "^d" | grep "backup_" || echo "No backups found"
        exit 1
    fi
    
    log_info "Validating backup: $BACKUP_NAME"
    
    # Check manifest file
    if [[ ! -f "$backup_path/manifest.txt" ]]; then
        log_warning "Manifest file not found. Backup may be incomplete."
    else
        log_info "Manifest file found"
        echo "Backup details:"
        head -10 "$backup_path/manifest.txt"
        echo
    fi
    
    # Check backup files
    local files_found=0
    
    if [[ -f "$backup_path/database.sql.gz" ]]; then
        log_info "Database backup found ($(du -h "$backup_path/database.sql.gz" | cut -f1))"
        ((files_found++))
    fi
    
    if [[ -f "$backup_path/config.tar.gz" ]]; then
        log_info "Configuration backup found ($(du -h "$backup_path/config.tar.gz" | cut -f1))"
        ((files_found++))
    fi
    
    if [[ -f "$backup_path/data.tar.gz" ]]; then
        log_info "Application data backup found ($(du -h "$backup_path/data.tar.gz" | cut -f1))"
        ((files_found++))
    fi
    
    if [[ -f "$backup_path/logs.tar.gz" ]]; then
        log_info "Logs backup found ($(du -h "$backup_path/logs.tar.gz" | cut -f1))"
        ((files_found++))
    fi
    
    if [[ $files_found -eq 0 ]]; then
        log_error "No backup files found in $backup_path"
        exit 1
    fi
    
    log_success "Backup validation completed ($files_found files found)"
}

confirm_restore() {
    if [[ "$FORCE" == "true" ]]; then
        return 0
    fi
    
    echo
    log_warning "WARNING: This will restore data from backup and may overwrite existing data!"
    echo
    echo "Backup: $BACKUP_NAME"
    echo "Location: $BACKUP_DIR/$BACKUP_NAME"
    echo
    echo "This operation will:"
    
    if [[ "$DATABASE_ONLY" != "true" && "$CONFIG_ONLY" != "true" && "$DATA_ONLY" != "true" ]]; then
        echo "  - Stop all services"
        echo "  - Restore database from backup"
        echo "  - Restore configuration files"
        echo "  - Restore application data"
        echo "  - Restart services"
    elif [[ "$DATABASE_ONLY" == "true" ]]; then
        echo "  - Stop API and worker services"
        echo "  - Restore database from backup"
        echo "  - Restart services"
    elif [[ "$CONFIG_ONLY" == "true" ]]; then
        echo "  - Restore configuration files"
        echo "  - Restart services (if needed)"
    elif [[ "$DATA_ONLY" == "true" ]]; then
        echo "  - Stop services"
        echo "  - Restore application data"
        echo "  - Restart services"
    fi
    
    echo
    read -p "Do you want to continue? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
}

stop_services() {
    log_info "Stopping services..."
    
    cd "$PROJECT_ROOT"
    
    if [[ "$DATABASE_ONLY" == "true" ]]; then
        # Stop only API and worker services for database restore
        docker-compose stop api worker
    elif [[ "$CONFIG_ONLY" == "true" ]]; then
        # No need to stop services for config restore
        return 0
    else
        # Stop all services for full restore
        docker-compose down
    fi
    
    log_success "Services stopped"
}

restore_database() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    if [[ ! -f "$backup_path/database.sql.gz" ]]; then
        log_warning "Database backup not found, skipping database restore"
        return 0
    fi
    
    log_info "Restoring database..."
    
    cd "$PROJECT_ROOT"
    
    # Start PostgreSQL if not running
    if ! docker-compose ps postgres | grep -q "Up"; then
        log_info "Starting PostgreSQL..."
        docker-compose up -d postgres
        sleep 10
    fi
    
    # Drop existing connections
    log_info "Dropping existing database connections..."
    docker-compose exec -T postgres psql -U postgres -c "
        SELECT pg_terminate_backend(pid) 
        FROM pg_stat_activity 
        WHERE datname = 'audit_logs' AND pid <> pg_backend_pid();
    " || true
    
    # Restore database
    log_info "Restoring database from backup..."
    if gunzip -c "$backup_path/database.sql.gz" | docker-compose exec -T postgres psql -U audit_user audit_logs; then
        log_success "Database restore completed"
    else
        log_error "Database restore failed"
        return 1
    fi
    
    # Verify restore
    log_info "Verifying database restore..."
    local record_count=$(docker-compose exec -T postgres psql -U audit_user audit_logs -t -c "SELECT COUNT(*) FROM audit_logs;" | tr -d ' \n')
    log_info "Restored $record_count audit log records"
}

restore_configuration() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    if [[ ! -f "$backup_path/config.tar.gz" ]]; then
        log_warning "Configuration backup not found, skipping configuration restore"
        return 0
    fi
    
    log_info "Restoring configuration files..."
    
    cd "$PROJECT_ROOT"
    
    # Create backup of current config
    if [[ -f ".env" ]]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        log_info "Current .env backed up"
    fi
    
    # Extract configuration
    if tar -xzf "$backup_path/config.tar.gz"; then
        log_success "Configuration files restored"
    else
        log_error "Configuration restore failed"
        return 1
    fi
    
    # Set proper permissions
    chmod 600 .env* 2>/dev/null || true
    chmod -R 755 monitoring/ 2>/dev/null || true
    chmod -R 755 config/ 2>/dev/null || true
    chmod -R 755 scripts/ 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "Configuration restore completed"
}

restore_application_data() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    if [[ ! -f "$backup_path/data.tar.gz" ]]; then
        log_warning "Application data backup not found, skipping data restore"
        return 0
    fi
    
    log_info "Restoring application data..."
    
    cd "$PROJECT_ROOT"
    
    # Create backup of current data
    if [[ -d "data" ]]; then
        mv data data.backup.$(date +%Y%m%d_%H%M%S)
        log_info "Current data directory backed up"
    fi
    
    # Extract application data
    if tar -xzf "$backup_path/data.tar.gz"; then
        log_success "Application data restored"
    else
        log_error "Application data restore failed"
        return 1
    fi
    
    # Set proper permissions
    chmod -R 755 data/ 2>/dev/null || true
    
    log_success "Application data restore completed"
}

restore_logs() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    if [[ ! -f "$backup_path/logs.tar.gz" ]]; then
        log_info "Logs backup not found, skipping logs restore"
        return 0
    fi
    
    log_info "Restoring logs..."
    
    cd "$PROJECT_ROOT"
    
    # Create backup of current logs
    if [[ -d "logs" ]] && [[ "$(ls -A logs)" ]]; then
        mv logs logs.backup.$(date +%Y%m%d_%H%M%S)
        log_info "Current logs directory backed up"
    fi
    
    # Extract logs
    if tar -xzf "$backup_path/logs.tar.gz"; then
        log_success "Logs restored"
    else
        log_warning "Logs restore failed (non-critical)"
    fi
    
    # Set proper permissions
    chmod -R 755 logs/ 2>/dev/null || true
}

start_services() {
    log_info "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    if [[ "$CONFIG_ONLY" == "true" ]]; then
        # Restart services to pick up new configuration
        docker-compose restart
    else
        # Start all services
        docker-compose up -d
    fi
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "Services are healthy"
            return 0
        fi
        
        log_info "Attempt $attempt/$max_attempts: Services not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    log_warning "Services may not be fully ready. Check logs: docker-compose logs"
}

verify_restore() {
    log_info "Verifying restore..."
    
    # Check API health
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "API health check passed"
    else
        log_warning "API health check failed"
    fi
    
    # Check database connectivity
    cd "$PROJECT_ROOT"
    if docker-compose exec -T postgres psql -U audit_user audit_logs -c "SELECT 1;" &> /dev/null; then
        log_success "Database connectivity verified"
    else
        log_warning "Database connectivity check failed"
    fi
    
    # Check service status
    echo
    echo "=== Service Status ==="
    docker-compose ps
    echo
}

show_restore_summary() {
    log_success "Restore completed successfully!"
    echo
    echo "=== Restore Summary ==="
    echo "Backup: $BACKUP_NAME"
    echo "Restored at: $(date)"
    echo
    echo "=== Service URLs ==="
    echo "API:          http://localhost:8000"
    echo "Frontend:     http://localhost:3000"
    echo "Grafana:      http://localhost:3001"
    echo "Prometheus:   http://localhost:9090"
    echo
    echo "=== Next Steps ==="
    echo "1. Verify application functionality"
    echo "2. Check logs: docker-compose logs -f"
    echo "3. Monitor system health"
    echo
}

# Parse command line arguments
DATABASE_ONLY=false
CONFIG_ONLY=false
DATA_ONLY=false
FORCE=false

while [[ $# -gt 1 ]]; do
    case $2 in
        --database-only)
            DATABASE_ONLY=true
            shift
            ;;
        --config-only)
            CONFIG_ONLY=true
            shift
            ;;
        --data-only)
            DATA_ONLY=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $2"
            usage
            exit 1
            ;;
    esac
done

# Check if backup name is provided
if [[ -z "$BACKUP_NAME" ]]; then
    log_error "Backup name is required"
    usage
    exit 1
fi

# Main restore process
log_info "Starting restore process..."

validate_backup
confirm_restore
stop_services

if [[ "$CONFIG_ONLY" == "true" ]]; then
    restore_configuration
elif [[ "$DATABASE_ONLY" == "true" ]]; then
    restore_database
elif [[ "$DATA_ONLY" == "true" ]]; then
    restore_application_data
else
    # Full restore
    restore_database
    restore_configuration
    restore_application_data
    restore_logs
fi

start_services
verify_restore
show_restore_summary

log_success "Restore process completed!"