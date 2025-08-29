# Deployment Guide

This document provides comprehensive instructions for deploying the Audit Log Framework in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database Setup](#database-setup)
6. [Service Configuration](#service-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Security Configuration](#security-configuration)
9. [Backup and Recovery](#backup-and-recovery)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

#### Minimum Requirements (Development)
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB available space
- **OS**: Linux, macOS, or Windows with WSL2

#### Recommended Requirements (Production)
- **CPU**: 8+ cores
- **RAM**: 16GB+
- **Storage**: 100GB+ SSD
- **OS**: Linux (Ubuntu 20.04+ or CentOS 8+)

### Software Dependencies

#### Required Software
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.30+
- **Make**: 4.0+ (optional, for convenience scripts)

#### Development Dependencies
- **Python**: 3.11+
- **Node.js**: 18+
- **Go**: 1.19+ (for SDK development)

### Installation Commands

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Git and Make
sudo apt install -y git make

# Logout and login to apply Docker group changes
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install docker docker-compose git make

# Start Docker Desktop
open /Applications/Docker.app
```

#### Windows (WSL2)
```powershell
# Install WSL2 and Ubuntu
wsl --install -d Ubuntu

# Follow Ubuntu instructions inside WSL2
```

## Local Development Setup

### Quick Start

1. **Clone the Repository**
```bash
git clone <repository-url>
cd audit-service
```

2. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional for development)
nano .env
```

3. **Start Services**
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

4. **Initialize Database**
```bash
# Run database migrations
docker-compose exec api python -m alembic upgrade head

# Create initial data (optional)
docker-compose exec api python -m app.scripts.seed_data
```

5. **Verify Installation**
```bash
# Check API health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check monitoring
curl http://localhost:9090  # Prometheus
curl http://localhost:3001  # Grafana
```

### Development Workflow

#### Starting Development Environment
```bash
# Start core services only
docker-compose up -d postgres redis nats

# Start API in development mode
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend in development mode
cd frontend
npm run dev
```

#### Running Tests
```bash
# Run all tests
make test

# Run specific test suites
docker-compose exec api python -m pytest tests/unit/
docker-compose exec api python -m pytest tests/integration/
python tests/load/run_load_tests.py
```

#### Code Quality Checks
```bash
# Run linting and formatting
make lint
make format

# Run security checks
make security-check

# Run type checking
make type-check
```

## Production Deployment

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │───▶│   API Servers   │───▶│   Database      │
│   (nginx/ALB)   │    │   (Multiple)    │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Workers       │───▶│   Message Queue │
                       │   (Background)  │    │   (NATS)        │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Cache         │    │   Monitoring    │
                       │   (Redis)       │    │   (Prometheus)  │
                       └─────────────────┘    └─────────────────┘
```

### Production Environment Setup

#### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y docker.io docker-compose nginx certbot python3-certbot-nginx

# Configure firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Create application user
sudo useradd -m -s /bin/bash audit-app
sudo usermod -aG docker audit-app
```

#### 2. Application Deployment
```bash
# Switch to application user
sudo su - audit-app

# Clone repository
git clone <repository-url> /opt/audit-service
cd /opt/audit-service

# Configure production environment
cp .env.example .env.production
nano .env.production
```

#### 3. Production Environment Variables
```bash
# .env.production
ENVIRONMENT=production
DEBUG=false

# Database
DATABASE_URL=postgresql+asyncpg://audit_user:secure_password@localhost:5432/audit_logs

# Redis
REDIS_URL=redis://localhost:6379/0

# NATS
NATS_URL=nats://localhost:4222

# Security
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here
API_KEY_SECRET=your-api-key-secret-here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# CORS
CORS_ORIGINS=["https://yourdomain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
METRICS_ENABLED=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# SSL/TLS
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/audit-service.crt
SSL_KEY_PATH=/etc/ssl/private/audit-service.key
```

#### 4. SSL Certificate Setup
```bash
# Using Let's Encrypt
sudo certbot --nginx -d yourdomain.com -d api.yourdomain.com

# Or use existing certificates
sudo cp your-cert.crt /etc/ssl/certs/audit-service.crt
sudo cp your-key.key /etc/ssl/private/audit-service.key
sudo chmod 600 /etc/ssl/private/audit-service.key
```

#### 5. Nginx Configuration
```nginx
# /etc/nginx/sites-available/audit-service
upstream audit_api {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # If running multiple instances
}

upstream audit_frontend {
    server 127.0.0.1:3000;
}

upstream audit_grafana {
    server 127.0.0.1:3001;
}

# API Server
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/audit-service.crt;
    ssl_certificate_key /etc/ssl/private/audit-service.key;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://audit_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://audit_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend Server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/audit-service.crt;
    ssl_certificate_key /etc/ssl/private/audit-service.key;

    location / {
        proxy_pass http://audit_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Monitoring Dashboard
server {
    listen 443 ssl http2;
    server_name monitoring.yourdomain.com;

    ssl_certificate /etc/ssl/certs/audit-service.crt;
    ssl_certificate_key /etc/ssl/private/audit-service.key;

    # Basic auth for monitoring
    auth_basic "Monitoring Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://audit_grafana;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com api.yourdomain.com monitoring.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

#### 6. Start Production Services
```bash
# Start services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Initialize database
docker-compose exec api python -m alembic upgrade head

# Create admin user
docker-compose exec api python -m app.scripts.create_admin_user

# Enable nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

## Environment Configuration

### Configuration Files

#### Docker Compose Override for Production
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    restart: always
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - API_WORKERS=4
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  worker:
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  postgres:
    restart: always
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - /opt/audit-service/data/postgres:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  redis:
    restart: always
    volumes:
      - /opt/audit-service/data/redis:/data
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  prometheus:
    restart: always
    volumes:
      - /opt/audit-service/data/prometheus:/prometheus
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  grafana:
    restart: always
    volumes:
      - /opt/audit-service/data/grafana:/var/lib/grafana
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

### Environment Variables Reference

#### Core Application
- `ENVIRONMENT`: Environment name (development/staging/production)
- `DEBUG`: Enable debug mode (true/false)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `LOG_FORMAT`: Log format (json/text)

#### Database
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_POOL_SIZE`: Connection pool size (default: 20)
- `DATABASE_MAX_OVERFLOW`: Max overflow connections (default: 0)
- `DATABASE_POOL_TIMEOUT`: Pool timeout in seconds (default: 30)

#### Cache
- `REDIS_URL`: Redis connection string
- `REDIS_POOL_SIZE`: Redis connection pool size (default: 10)
- `REDIS_TIMEOUT`: Redis operation timeout (default: 5)

#### Message Queue
- `NATS_URL`: NATS connection string
- `NATS_MAX_RECONNECT_ATTEMPTS`: Max reconnection attempts (default: 10)
- `NATS_RECONNECT_WAIT`: Reconnection wait time (default: 2)

#### API Configuration
- `API_HOST`: API bind host (default: 0.0.0.0)
- `API_PORT`: API port (default: 8000)
- `API_WORKERS`: Number of worker processes (default: 1)
- `API_RELOAD`: Enable auto-reload in development (default: false)

#### Security
- `JWT_SECRET_KEY`: JWT signing secret
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `JWT_EXPIRE_MINUTES`: JWT expiration time (default: 30)
- `API_KEY_SECRET`: API key encryption secret
- `CORS_ORIGINS`: Allowed CORS origins (JSON array)

#### Rate Limiting
- `RATE_LIMIT_ENABLED`: Enable rate limiting (default: true)
- `RATE_LIMIT_REQUESTS_PER_MINUTE`: Requests per minute (default: 60)
- `RATE_LIMIT_BURST`: Burst limit (default: 10)

#### Monitoring
- `PROMETHEUS_ENABLED`: Enable Prometheus metrics (default: true)
- `GRAFANA_ENABLED`: Enable Grafana dashboards (default: true)
- `METRICS_ENABLED`: Enable custom metrics (default: true)
- `HEALTH_CHECK_ENABLED`: Enable health checks (default: true)

## Database Setup

### PostgreSQL Configuration

#### Production Database Setup
```sql
-- Create database and user
CREATE DATABASE audit_logs;
CREATE USER audit_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE audit_logs TO audit_user;

-- Configure for performance
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Reload configuration
SELECT pg_reload_conf();
```

#### Database Migrations
```bash
# Run migrations
docker-compose exec api python -m alembic upgrade head

# Create new migration
docker-compose exec api python -m alembic revision --autogenerate -m "description"

# Rollback migration
docker-compose exec api python -m alembic downgrade -1
```

#### Database Backup
```bash
# Create backup
docker-compose exec postgres pg_dump -U audit_user audit_logs > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker-compose exec -T postgres psql -U audit_user audit_logs < backup_file.sql
```

### Database Partitioning

#### Audit Logs Partitioning (for high volume)
```sql
-- Create partitioned table
CREATE TABLE audit_logs_partitioned (
    LIKE audit_logs INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Create monthly partitions
CREATE TABLE audit_logs_2025_01 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE audit_logs_2025_02 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Create indexes on partitions
CREATE INDEX idx_audit_logs_2025_01_tenant_created 
    ON audit_logs_2025_01 (tenant_id, created_at);
```

## Service Configuration

### Systemd Service Files

#### API Service
```ini
# /etc/systemd/system/audit-api.service
[Unit]
Description=Audit Log API Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/audit-service
ExecStart=/usr/local/bin/docker-compose up -d api
ExecStop=/usr/local/bin/docker-compose stop api
TimeoutStartSec=0
User=audit-app
Group=audit-app

[Install]
WantedBy=multi-user.target
```

#### Worker Service
```ini
# /etc/systemd/system/audit-worker.service
[Unit]
Description=Audit Log Worker Service
After=docker.service audit-api.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/audit-service
ExecStart=/usr/local/bin/docker-compose up -d worker
ExecStop=/usr/local/bin/docker-compose stop worker
TimeoutStartSec=0
User=audit-app
Group=audit-app

[Install]
WantedBy=multi-user.target
```

#### Enable Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable audit-api.service
sudo systemctl enable audit-worker.service
sudo systemctl start audit-api.service
sudo systemctl start audit-worker.service
```

### Log Rotation

#### Logrotate Configuration
```bash
# /etc/logrotate.d/audit-service
/opt/audit-service/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 audit-app audit-app
    postrotate
        docker-compose -f /opt/audit-service/docker-compose.yml kill -s USR1 api worker
    endscript
}
```

## Monitoring Setup

### Prometheus Configuration

#### Production Prometheus Config
```yaml
# monitoring/prometheus/prometheus.prod.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'audit-log-production'
    environment: 'production'

rule_files:
  - "alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'audit-log-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 10s

  - job_name: 'audit-log-health'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/health'
    scrape_interval: 30s

# Remote storage for long-term retention
remote_write:
  - url: "https://prometheus-remote-write-endpoint"
    basic_auth:
      username: "username"
      password: "password"
```

### Grafana Production Setup

#### Grafana Configuration
```ini
# monitoring/grafana/grafana.prod.ini
[server]
http_port = 3000
domain = monitoring.yourdomain.com
root_url = https://monitoring.yourdomain.com

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}
secret_key = ${GRAFANA_SECRET_KEY}

[auth]
disable_login_form = false

[auth.basic]
enabled = true

[users]
allow_sign_up = false
allow_org_create = false

[log]
mode = file
level = info
```

## Security Configuration

### SSL/TLS Configuration

#### Generate Self-Signed Certificates (Development)
```bash
# Create certificate directory
mkdir -p ssl

# Generate private key
openssl genrsa -out ssl/audit-service.key 2048

# Generate certificate signing request
openssl req -new -key ssl/audit-service.key -out ssl/audit-service.csr

# Generate self-signed certificate
openssl x509 -req -days 365 -in ssl/audit-service.csr -signkey ssl/audit-service.key -out ssl/audit-service.crt
```

### Firewall Configuration

#### UFW Rules
```bash
# Reset firewall
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# SSH access
sudo ufw allow 22/tcp

# HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Database (only from application servers)
sudo ufw allow from 10.0.0.0/8 to any port 5432

# Redis (only from application servers)
sudo ufw allow from 10.0.0.0/8 to any port 6379

# NATS (only from application servers)
sudo ufw allow from 10.0.0.0/8 to any port 4222

# Monitoring (only from monitoring network)
sudo ufw allow from 10.0.0.0/8 to any port 9090
sudo ufw allow from 10.0.0.0/8 to any port 3001

# Enable firewall
sudo ufw --force enable
```

### Application Security

#### Security Headers
```python
# backend/app/middleware/security.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
```

## Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/opt/audit-service/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
docker-compose exec -T postgres pg_dump -U audit_user audit_logs | gzip > $BACKUP_DIR/database_$DATE.sql.gz

# Configuration backup
echo "Creating configuration backup..."
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    .env.production \
    docker-compose.yml \
    docker-compose.prod.yml \
    monitoring/ \
    ssl/

# Application data backup
echo "Creating application data backup..."
tar -czf $BACKUP_DIR/data_$DATE.tar.gz \
    data/grafana \
    data/prometheus \
    logs/

# Clean old backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $DATE"
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop services
docker-compose stop api worker

# Restore database
gunzip -c backups/database_YYYYMMDD_HHMMSS.sql.gz | docker-compose exec -T postgres psql -U audit_user audit_logs

# Start services
docker-compose start api worker
```

#### Full System Recovery
```bash
# Extract configuration
tar -xzf backups/config_YYYYMMDD_HHMMSS.tar.gz

# Extract application data
tar -xzf backups/data_YYYYMMDD_HHMMSS.tar.gz

# Restore database
gunzip -c backups/database_YYYYMMDD_HHMMSS.sql.gz | docker-compose exec -T postgres psql -U audit_user audit_logs

# Restart all services
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs api

# Check resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

#### Database Connection Issues
```bash
# Test database connection
docker-compose exec postgres psql -U audit_user audit_logs -c "SELECT 1;"

# Check database logs
docker-compose logs postgres

# Check connection pool
curl http://localhost:8000/api/v1/metrics/stats
```

#### High Memory Usage
```bash
# Check container memory usage
docker stats

# Check application metrics
curl http://localhost:8000/api/v1/metrics

# Restart services if needed
docker-compose restart api worker
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in ssl/audit-service.crt -text -noout

# Test SSL connection
openssl s_client -connect yourdomain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew
```

### Performance Tuning

#### Database Optimization
```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE tenant_id = 'tenant-123';

-- Update table statistics
ANALYZE audit_logs;

-- Reindex tables
REINDEX TABLE audit_logs;
```

#### Application Optimization
```bash
# Monitor API performance
curl http://localhost:8000/api/v1/metrics/stats

# Check cache hit rates
redis-cli info stats

# Monitor NATS performance
curl http://localhost:8222/varz
```

### Log Analysis

#### Application Logs
```bash
# View real-time logs
docker-compose logs -f api

# Search for errors
docker-compose logs api | grep ERROR

# Filter by correlation ID
docker-compose logs api | grep "correlation_id.*550e8400"
```

#### System Logs
```bash
# Check system logs
sudo journalctl -u audit-api.service -f

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

This deployment guide provides comprehensive instructions for setting up the Audit Log Framework in both development and production environments, with detailed configuration options, security considerations, and troubleshooting procedures.