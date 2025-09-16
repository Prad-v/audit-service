#!/bin/bash

# Database Setup Script for Audit Service
# This script creates all necessary databases, users, and schemas

set -e

echo "=================================="
echo "Audit Service - Database Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

print_status "Starting PostgreSQL container..."
docker-compose up -d postgres

print_status "Waiting for PostgreSQL to be ready..."
sleep 10

# Function to execute SQL command
execute_sql() {
    local sql="$1"
    local database="${2:-audit_logs}"
    local user="${3:-audit_user}"
    
    docker-compose exec -T postgres psql -U "$user" -d "$database" -c "$sql" || {
        print_warning "Command may have failed or already exists: $sql"
    }
}

print_status "Creating additional databases..."

# Create additional databases (audit_logs already exists from docker-compose)
docker-compose exec -T postgres psql -U audit_user -d audit_logs -c "CREATE DATABASE events_db;" || print_warning "events_db may already exist"
docker-compose exec -T postgres psql -U audit_user -d audit_logs -c "CREATE DATABASE alerting_db;" || print_warning "alerting_db may already exist"

print_status "Creating additional users..."

# Create additional users (audit_user already exists from docker-compose)
docker-compose exec -T postgres psql -U audit_user -d audit_logs -c "CREATE USER events_user WITH PASSWORD 'events_password';" || print_warning "events_user may already exist"
docker-compose exec -T postgres psql -U audit_user -d audit_logs -c "CREATE USER alerting_user WITH PASSWORD 'alerting_password';" || print_warning "alerting_user may already exist"

print_status "Granting privileges..."

# Grant privileges
docker-compose exec -T postgres psql -U audit_user -d audit_logs -c "GRANT ALL PRIVILEGES ON DATABASE events_db TO events_user;" || print_warning "Privileges may already be granted"
docker-compose exec -T postgres psql -U audit_user -d audit_logs -c "GRANT ALL PRIVILEGES ON DATABASE alerting_db TO alerting_user;" || print_warning "Privileges may already be granted"

print_status "Setting up audit_logs schema..."

# Setup audit_logs schema
execute_sql "
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(255),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
" audit_logs audit_user

print_status "Setting up events_db schema..."

# Setup events_db schema
execute_sql "
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    source VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    data JSONB NOT NULL,
    metadata JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_processors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_subscriptions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    event_types TEXT[] NOT NULL,
    processor_id INTEGER REFERENCES event_processors(id),
    config JSONB NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_event_id ON events(event_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_processed ON events(processed);
" events_db events_user

print_status "Setting up alerting_db schema..."

# Setup alerting_db schema
execute_sql "
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    source VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    condition TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alert_notifications (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(255) REFERENCES alerts(alert_id),
    notification_type VARCHAR(50) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'sent',
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_id ON alerts(alert_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
" alerting_db alerting_user

print_status "Setting up StackStorm tests schema..."

# Setup StackStorm tests schema in audit_logs database
execute_sql "
CREATE TABLE IF NOT EXISTS stackstorm_tests (
    test_id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_type VARCHAR(50) NOT NULL,
    stackstorm_pack VARCHAR(255) DEFAULT 'synthetic_tests',
    stackstorm_action VARCHAR(255),
    stackstorm_workflow VARCHAR(255),
    stackstorm_rule VARCHAR(255),
    stackstorm_sensor VARCHAR(255),
    test_code TEXT NOT NULL,
    test_parameters JSONB DEFAULT '{}',
    expected_result JSONB,
    timeout INTEGER DEFAULT 300,
    retry_count INTEGER DEFAULT 0,
    retry_delay INTEGER DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    tags JSONB DEFAULT '[]',
    enabled BOOLEAN DEFAULT TRUE,
    stackstorm_execution_id VARCHAR(255),
    stackstorm_pack_version VARCHAR(255),
    deployed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS test_executions (
    execution_id VARCHAR(255) PRIMARY KEY,
    test_id VARCHAR(255) NOT NULL,
    stackstorm_execution_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    error_message TEXT,
    output_data JSONB DEFAULT '{}',
    created_incident_id VARCHAR(255),
    execution_context JSONB DEFAULT '{}',
    node_results JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_stackstorm_tests_name ON stackstorm_tests(name);
CREATE INDEX IF NOT EXISTS idx_stackstorm_tests_test_type ON stackstorm_tests(test_type);
CREATE INDEX IF NOT EXISTS idx_stackstorm_tests_enabled ON stackstorm_tests(enabled);
CREATE INDEX IF NOT EXISTS idx_test_executions_test_id ON test_executions(test_id);
CREATE INDEX IF NOT EXISTS idx_test_executions_status ON test_executions(status);
CREATE INDEX IF NOT EXISTS idx_test_executions_started_at ON test_executions(started_at);
" audit_logs audit_user

print_status "Inserting sample data..."

# Insert sample data
execute_sql "
INSERT INTO event_processors (name, description, config, enabled) VALUES
('audit_processor', 'Processes audit events', '{\"type\": \"audit\", \"enabled\": true}', true),
('alert_processor', 'Processes alert events', '{\"type\": \"alert\", \"enabled\": true}', true)
ON CONFLICT (name) DO NOTHING;
" events_db events_user

execute_sql "
INSERT INTO alert_rules (name, description, condition, severity, enabled) VALUES
('high_error_rate', 'Alert when error rate is high', 'error_rate > 0.1', 'high', true),
('service_down', 'Alert when service is down', 'status = \"down\"', 'critical', true)
ON CONFLICT (name) DO NOTHING;
" alerting_db alerting_user

print_status "Database setup completed successfully!"
print_status "=================================="
print_status "Databases created:"
print_status "- audit_logs (user: audit_user)"
print_status "- events_db (user: events_user)"
print_status "- alerting_db (user: alerting_user)"
print_status "=================================="
print_status "You can now start the services with: make start"
print_status "=================================="
