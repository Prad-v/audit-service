#!/bin/bash

# Audit Log Framework Backup Script
# This script creates comprehensive backups of the system

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
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_$DATE"

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

create_backup_directory() {
    log_info "Creating backup directory: $BACKUP_DIR/$BACKUP_NAME"
    mkdir -p "$BACKUP_DIR/$BACKUP_NAME"
}

backup_database() {
    log_info "Backing up database..."
    
    cd "$PROJECT_ROOT"
    
    # Check if postgres container is running
    if ! docker-compose ps postgres | grep -q "Up"; then
        log_warning "PostgreSQL container is not running. Skipping database backup."
        return 0
    fi
    
    # Create database backup
    if docker-compose exec -T postgres pg_dump -U audit_user audit_logs | gzip > "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz"; then
        log_success "Database backup completed"
        
        # Get backup size
        local size=$(du -h "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz" | cut -f1)
        log_info "Database backup size: $size"
    else
        log_error "Database backup failed"
        return 1
    fi
}

backup_configuration() {
    log_info "Backing up configuration files..."
    
    cd "$PROJECT_ROOT"
    
    # Create configuration backup
    tar -czf "$BACKUP_DIR/$BACKUP_NAME/config.tar.gz" \
        .env* \
        docker-compose*.yml \
        monitoring/ \
        config/ \
        ssl/ \
        scripts/ \
        2>/dev/null || true
    
    if [[ -f "$BACKUP_DIR/$BACKUP_NAME/config.tar.gz" ]]; then
        log_success "Configuration backup completed"
        
        # Get backup size
        local size=$(du -h "$BACKUP_DIR/$BACKUP_NAME/config.tar.gz" | cut -f1)
        log_info "Configuration backup size: $size"
    else
        log_error "Configuration backup failed"
        return 1
    fi
}

backup_application_data() {
    log_info "Backing up application data..."
    
    cd "$PROJECT_ROOT"
    
    # Backup persistent data
    if [[ -d "data" ]]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/data.tar.gz" data/ 2>/dev/null || true
        
        if [[ -f "$BACKUP_DIR/$BACKUP_NAME/data.tar.gz" ]]; then
            log_success "Application data backup completed"
            
            # Get backup size
            local size=$(du -h "$BACKUP_DIR/$BACKUP_NAME/data.tar.gz" | cut -f1)
            log_info "Application data backup size: $size"
        fi
    else
        log_warning "No application data directory found"
    fi
}

backup_logs() {
    log_info "Backing up logs..."
    
    cd "$PROJECT_ROOT"
    
    # Backup logs
    if [[ -d "logs" ]] && [[ "$(ls -A logs)" ]]; then
        tar -czf "$BACKUP_DIR/$BACKUP_NAME/logs.tar.gz" logs/ 2>/dev/null || true
        
        if [[ -f "$BACKUP_DIR/$BACKUP_NAME/logs.tar.gz" ]]; then
            log_success "Logs backup completed"
            
            # Get backup size
            local size=$(du -h "$BACKUP_DIR/$BACKUP_NAME/logs.tar.gz" | cut -f1)
            log_info "Logs backup size: $size"
        fi
    else
        log_warning "No logs found to backup"
    fi
}

create_backup_manifest() {
    log_info "Creating backup manifest..."
    
    local manifest_file="$BACKUP_DIR/$BACKUP_NAME/manifest.txt"
    
    cat > "$manifest_file" << EOF
Audit Log Framework Backup
==========================

Backup Date: $(date)
Backup Name: $BACKUP_NAME
Hostname: $(hostname)
User: $(whoami)

Files in this backup:
EOF
    
    # List backup files
    ls -la "$BACKUP_DIR/$BACKUP_NAME/" >> "$manifest_file"
    
    # Add system information
    cat >> "$manifest_file" << EOF

System Information:
==================
OS: $(uname -a)
Docker Version: $(docker --version 2>/dev/null || echo "Not available")
Docker Compose Version: $(docker-compose --version 2>/dev/null || echo "Not available")

Container Status:
================
EOF
    
    cd "$PROJECT_ROOT"
    docker-compose ps >> "$manifest_file" 2>/dev/null || echo "Docker Compose not available" >> "$manifest_file"
    
    log_success "Backup manifest created"
}

calculate_backup_size() {
    local total_size=$(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)
    log_info "Total backup size: $total_size"
}

cleanup_old_backups() {
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    local deleted_count=0
    
    # Find and delete old backups
    if [[ -d "$BACKUP_DIR" ]]; then
        while IFS= read -r -d '' backup_dir; do
            rm -rf "$backup_dir"
            ((deleted_count++))
            log_info "Deleted old backup: $(basename "$backup_dir")"
        done < <(find "$BACKUP_DIR" -maxdepth 1 -type d -name "backup_*" -mtime +$RETENTION_DAYS -print0)
    fi
    
    if [[ $deleted_count -gt 0 ]]; then
        log_success "Cleaned up $deleted_count old backups"
    else
        log_info "No old backups to clean up"
    fi
}

verify_backup() {
    log_info "Verifying backup integrity..."
    
    local verification_failed=false
    
    # Verify database backup
    if [[ -f "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz" ]]; then
        if gzip -t "$BACKUP_DIR/$BACKUP_NAME/database.sql.gz"; then
            log_success "Database backup verification passed"
        else
            log_error "Database backup verification failed"
            verification_failed=true
        fi
    fi
    
    # Verify configuration backup
    if [[ -f "$BACKUP_DIR/$BACKUP_NAME/config.tar.gz" ]]; then
        if tar -tzf "$BACKUP_DIR/$BACKUP_NAME/config.tar.gz" >/dev/null; then
            log_success "Configuration backup verification passed"
        else
            log_error "Configuration backup verification failed"
            verification_failed=true
        fi
    fi
    
    # Verify data backup
    if [[ -f "$BACKUP_DIR/$BACKUP_NAME/data.tar.gz" ]]; then
        if tar -tzf "$BACKUP_DIR/$BACKUP_NAME/data.tar.gz" >/dev/null; then
            log_success "Data backup verification passed"
        else
            log_error "Data backup verification failed"
            verification_failed=true
        fi
    fi
    
    if [[ "$verification_failed" == "true" ]]; then
        log_error "Backup verification failed"
        return 1
    else
        log_success "All backup verifications passed"
        return 0
    fi
}

# Main backup function
create_backup() {
    log_info "Starting backup process..."
    
    create_backup_directory
    backup_database
    backup_configuration
    backup_application_data
    backup_logs
    create_backup_manifest
    calculate_backup_size
    
    if verify_backup; then
        log_success "Backup completed successfully: $BACKUP_NAME"
        cleanup_old_backups
        
        # Show backup location
        echo
        echo "=== Backup Information ==="
        echo "Backup Name: $BACKUP_NAME"
        echo "Backup Location: $BACKUP_DIR/$BACKUP_NAME"
        echo "Total Size: $(du -sh "$BACKUP_DIR/$BACKUP_NAME" | cut -f1)"
        echo
        echo "=== Backup Contents ==="
        ls -la "$BACKUP_DIR/$BACKUP_NAME/"
        echo
    else
        log_error "Backup verification failed"
        exit 1
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -d, --dir DIR        Backup directory (default: ./backups)"
    echo "  -r, --retention DAYS Retention period in days (default: 30)"
    echo "  -h, --help          Show this help message"
    echo
    echo "Environment Variables:"
    echo "  BACKUP_DIR          Backup directory"
    echo "  RETENTION_DAYS      Retention period in days"
    echo
    echo "Examples:"
    echo "  $0                           # Create backup with defaults"
    echo "  $0 -d /opt/backups          # Use custom backup directory"
    echo "  $0 -r 7                     # Keep backups for 7 days"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        -r|--retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Run backup
create_backup