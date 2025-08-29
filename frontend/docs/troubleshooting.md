# Troubleshooting Guide

This document provides comprehensive troubleshooting procedures for the Audit Log Framework.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Service-Specific Issues](#service-specific-issues)
4. [Performance Issues](#performance-issues)
5. [Database Issues](#database-issues)
6. [Network and Connectivity](#network-and-connectivity)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Log Analysis](#log-analysis)
9. [Recovery Procedures](#recovery-procedures)
10. [Emergency Procedures](#emergency-procedures)

## Quick Diagnostics

### System Health Check
```bash
# Check all services status
docker-compose ps

# Check system resources
docker stats --no-stream

# Check disk space
df -h

# Check memory usage
free -h

# Quick health check
curl -f http://localhost:8000/health || echo "API health check failed"
```

### Service Connectivity Test
```bash
# Test database connection
docker-compose exec postgres psql -U audit_user audit_logs -c "SELECT 1;"

# Test Redis connection
docker-compose exec redis redis-cli ping

# Test NATS connection
curl -s http://localhost:8222/varz | jq '.connections'

# Test API endpoints
curl -s http://localhost:8000/api/v1/metrics/health | jq '.'
```

### Log Quick View
```bash
# View recent logs from all services
docker-compose logs --tail=50

# View API logs only
docker-compose logs --tail=100 api

# View error logs
docker-compose logs | grep -i error

# View logs with timestamps
docker-compose logs -t --tail=50
```

## Common Issues

### 1. Services Won't Start

#### Symptoms
- `docker-compose up` fails
- Services show "Exited" status
- Port binding errors

#### Diagnosis
```bash
# Check service status
docker-compose ps

# Check specific service logs
docker-compose logs <service-name>

# Check port conflicts
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
```

#### Solutions

**Port Conflicts**
```bash
# Find process using port
lsof -i :8000

# Kill process if safe
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Permission Issues**
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
chmod -R 755 data/

# Fix log directory permissions
sudo chown -R $USER:$USER logs/
chmod -R 755 logs/
```

**Docker Issues**
```bash
# Restart Docker daemon
sudo systemctl restart docker

# Clean up Docker resources
docker system prune -f

# Rebuild images
docker-compose build --no-cache
```

### 2. Database Connection Failures

#### Symptoms
- "Connection refused" errors
- "Database does not exist" errors
- Timeout errors

#### Diagnosis
```bash
# Check PostgreSQL container
docker-compose logs postgres

# Test direct connection
docker-compose exec postgres psql -U audit_user audit_logs

# Check connection string
echo $DATABASE_URL
```

#### Solutions

**Database Not Ready**
```bash
# Wait for database to be ready
docker-compose up -d postgres
sleep 30
docker-compose exec postgres pg_isready -U audit_user
```

**Wrong Credentials**
```bash
# Check environment variables
docker-compose exec api env | grep DATABASE

# Reset database password
docker-compose exec postgres psql -U postgres -c "ALTER USER audit_user PASSWORD 'new_password';"
```

**Database Corruption**
```bash
# Check database integrity
docker-compose exec postgres psql -U audit_user audit_logs -c "SELECT pg_database_size('audit_logs');"

# Restore from backup if needed
./scripts/restore.sh backup_YYYYMMDD_HHMMSS
```

### 3. High Memory Usage

#### Symptoms
- System becomes slow
- Out of memory errors
- Container restarts

#### Diagnosis
```bash
# Check container memory usage
docker stats

# Check system memory
free -h

# Check for memory leaks
docker-compose exec api python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

#### Solutions

**Increase Memory Limits**
```yaml
# In docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

**Optimize Database Connections**
```bash
# Check connection pool size
curl -s http://localhost:8000/api/v1/metrics/stats | jq '.database'

# Reduce pool size in configuration
# DATABASE_POOL_SIZE=10
# DATABASE_MAX_OVERFLOW=5
```

**Clear Cache**
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart services
docker-compose restart api worker
```

### 4. API Response Timeouts

#### Symptoms
- Slow API responses
- Gateway timeout errors
- Client timeouts

#### Diagnosis
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Check database query performance
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"

# Check system load
uptime
```

#### Solutions

**Database Optimization**
```sql
-- Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE tenant_id = 'tenant-123' LIMIT 100;

-- Update statistics
ANALYZE audit_logs;

-- Reindex if needed
REINDEX TABLE audit_logs;
```

**Increase Timeouts**
```bash
# In nginx configuration
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

# In application configuration
# API_TIMEOUT=60
```

**Scale Services**
```yaml
# Add more API workers
services:
  api:
    deploy:
      replicas: 3
```

## Service-Specific Issues

### PostgreSQL Issues

#### Connection Pool Exhaustion
```bash
# Check active connections
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';"

# Check max connections
docker-compose exec postgres psql -U audit_user audit_logs -c "SHOW max_connections;"

# Kill long-running queries
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' 
AND query_start < now() - interval '5 minutes';"
```

#### Disk Space Issues
```bash
# Check database size
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT pg_size_pretty(pg_database_size('audit_logs'));"

# Check table sizes
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Clean up old data
docker-compose exec postgres psql -U audit_user audit_logs -c "
DELETE FROM audit_logs 
WHERE created_at < now() - interval '90 days';"
```

### Redis Issues

#### Memory Issues
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli INFO memory

# Check key count
docker-compose exec redis redis-cli DBSIZE

# Clear expired keys
docker-compose exec redis redis-cli --scan --pattern "*" | xargs docker-compose exec redis redis-cli DEL
```

#### Connection Issues
```bash
# Check Redis connections
docker-compose exec redis redis-cli INFO clients

# Check Redis configuration
docker-compose exec redis redis-cli CONFIG GET "*"

# Restart Redis
docker-compose restart redis
```

### NATS Issues

#### Message Queue Backlog
```bash
# Check NATS statistics
curl -s http://localhost:8222/varz | jq '.in_msgs, .out_msgs, .slow_consumers'

# Check JetStream status
curl -s http://localhost:8222/jsz | jq '.streams'

# Purge messages if needed
docker-compose exec nats nats stream purge audit-logs --force
```

#### Connection Issues
```bash
# Check NATS connections
curl -s http://localhost:8222/connz | jq '.connections | length'

# Check NATS routes
curl -s http://localhost:8222/routez

# Restart NATS
docker-compose restart nats
```

## Performance Issues

### High CPU Usage

#### Diagnosis
```bash
# Check CPU usage by container
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Check system CPU
top -p $(docker-compose exec api pgrep python | tr '\n' ',' | sed 's/,$//')

# Profile application
docker-compose exec api python -m cProfile -o profile.stats -m app.main
```

#### Solutions
```bash
# Scale API workers
# API_WORKERS=4

# Optimize database queries
# Add indexes for frequently queried columns

# Enable query caching
# CACHE_ENABLED=true
# CACHE_TTL=300
```

### High Disk I/O

#### Diagnosis
```bash
# Check disk I/O
iostat -x 1 5

# Check database I/O
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT schemaname, tablename, heap_blks_read, heap_blks_hit 
FROM pg_statio_user_tables 
ORDER BY heap_blks_read DESC;"
```

#### Solutions
```bash
# Optimize PostgreSQL configuration
# shared_buffers = 256MB
# effective_cache_size = 1GB
# random_page_cost = 1.1

# Use SSD storage for database
# Move data directory to SSD mount point
```

### Network Latency

#### Diagnosis
```bash
# Test network latency
ping -c 5 localhost

# Check DNS resolution
nslookup localhost

# Test API latency
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/audit/logs
```

#### Solutions
```bash
# Use local DNS resolver
# Add to /etc/hosts: 127.0.0.1 api.local

# Optimize network settings
# net.core.rmem_max = 16777216
# net.core.wmem_max = 16777216
```

## Database Issues

### Slow Queries

#### Identification
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
WHERE mean_time > 1000
ORDER BY mean_time DESC;
```

#### Optimization
```sql
-- Add missing indexes
CREATE INDEX CONCURRENTLY idx_audit_logs_tenant_created 
ON audit_logs (tenant_id, created_at);

-- Update table statistics
ANALYZE audit_logs;

-- Check query plans
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM audit_logs 
WHERE tenant_id = 'tenant-123' 
ORDER BY created_at DESC 
LIMIT 100;
```

### Lock Contention

#### Diagnosis
```sql
-- Check for locks
SELECT 
    blocked_locks.pid AS blocked_pid,
    blocked_activity.usename AS blocked_user,
    blocking_locks.pid AS blocking_pid,
    blocking_activity.usename AS blocking_user,
    blocked_activity.query AS blocked_statement,
    blocking_activity.query AS current_statement_in_blocking_process
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

#### Resolution
```sql
-- Kill blocking queries
SELECT pg_terminate_backend(<blocking_pid>);

-- Optimize transactions
-- Keep transactions short
-- Use appropriate isolation levels
```

### Data Corruption

#### Detection
```sql
-- Check database integrity
SELECT pg_database_size('audit_logs');

-- Check table corruption
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
FROM pg_stat_user_tables;

-- Verify checksums (if enabled)
SELECT pg_verify_checksums();
```

#### Recovery
```bash
# Stop application
docker-compose stop api worker

# Restore from backup
./scripts/restore.sh backup_YYYYMMDD_HHMMSS

# Verify data integrity
docker-compose exec postgres psql -U audit_user audit_logs -c "
SELECT COUNT(*) FROM audit_logs;
SELECT MAX(created_at) FROM audit_logs;
"
```

## Network and Connectivity

### DNS Resolution Issues

#### Diagnosis
```bash
# Test DNS resolution
nslookup postgres
nslookup redis
nslookup nats

# Check /etc/hosts
cat /etc/hosts

# Test container networking
docker network ls
docker network inspect audit-service_audit-network
```

#### Solutions
```bash
# Restart Docker networking
docker network prune

# Use explicit container names
# In docker-compose.yml, ensure container_name is set

# Check firewall rules
sudo ufw status
```

### Port Conflicts

#### Diagnosis
```bash
# Check port usage
netstat -tulpn | grep :8000
netstat -tulpn | grep :5432
netstat -tulpn | grep :6379
netstat -tulpn | grep :4222

# Check Docker port mappings
docker port <container_name>
```

#### Solutions
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different external port

# Kill conflicting processes
sudo kill -9 <PID>
```

## Monitoring and Alerting

### Prometheus Issues

#### Metrics Not Collected
```bash
# Check Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

# Check metrics endpoint
curl -s http://localhost:8000/api/v1/metrics | head -20

# Verify Prometheus configuration
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml
```

#### High Memory Usage
```bash
# Check Prometheus memory usage
docker stats prometheus

# Reduce retention period
# --storage.tsdb.retention.time=15d

# Increase memory limit
# deploy.resources.limits.memory: 2G
```

### Grafana Issues

#### Dashboard Not Loading
```bash
# Check Grafana logs
docker-compose logs grafana

# Test data source connection
curl -s http://localhost:3001/api/datasources/proxy/1/api/v1/query?query=up

# Restart Grafana
docker-compose restart grafana
```

#### Authentication Issues
```bash
# Reset admin password
docker-compose exec grafana grafana-cli admin reset-admin-password admin123

# Check authentication configuration
docker-compose exec grafana cat /etc/grafana/grafana.ini | grep -A 10 "\[auth\]"
```

## Log Analysis

### Application Logs

#### Error Analysis
```bash
# Find error patterns
docker-compose logs api | grep -i error | sort | uniq -c | sort -nr

# Find correlation IDs for failed requests
docker-compose logs api | grep -i error | grep -o 'correlation_id=[^[:space:]]*'

# Analyze specific error
docker-compose logs api | grep "correlation_id=550e8400-e29b-41d4-a716-446655440000"
```

#### Performance Analysis
```bash
# Find slow requests
docker-compose logs api | grep "duration_ms" | awk '$NF > 1000' | head -10

# Analyze request patterns
docker-compose logs api | grep "Incoming request" | awk '{print $NF}' | sort | uniq -c | sort -nr
```

### System Logs

#### Container Logs
```bash
# Check container events
docker events --filter container=audit-api --since="1h"

# Check system logs
sudo journalctl -u docker.service --since="1 hour ago"

# Check kernel logs
dmesg | tail -50
```

## Recovery Procedures

### Service Recovery

#### API Service Recovery
```bash
# Check API health
curl -f http://localhost:8000/health

# Restart API service
docker-compose restart api

# Scale API service
docker-compose up -d --scale api=2

# Check API logs
docker-compose logs --tail=100 api
```

#### Database Recovery
```bash
# Check database status
docker-compose exec postgres pg_isready -U audit_user

# Restart database
docker-compose restart postgres

# Restore from backup if needed
./scripts/restore.sh backup_YYYYMMDD_HHMMSS

# Run health check
docker-compose exec postgres psql -U audit_user audit_logs -c "SELECT 1;"
```

### Data Recovery

#### Point-in-Time Recovery
```bash
# Stop services
docker-compose stop api worker

# Restore database to specific point
# (Requires WAL archiving to be enabled)
docker-compose exec postgres pg_basebackup -D /var/lib/postgresql/recovery -U audit_user

# Start database in recovery mode
# Edit postgresql.conf: restore_command = 'cp /path/to/wal/%f %p'

# Start services
docker-compose start postgres
docker-compose start api worker
```

#### Partial Data Recovery
```sql
-- Recover specific tenant data
INSERT INTO audit_logs 
SELECT * FROM audit_logs_backup 
WHERE tenant_id = 'tenant-123' 
AND created_at > '2025-01-01';

-- Verify recovery
SELECT COUNT(*) FROM audit_logs WHERE tenant_id = 'tenant-123';
```

## Emergency Procedures

### System Down

#### Immediate Actions
1. **Assess Impact**
   ```bash
   # Check all services
   docker-compose ps
   
   # Check system resources
   df -h && free -h
   
   # Check network connectivity
   ping -c 3 8.8.8.8
   ```

2. **Quick Recovery**
   ```bash
   # Restart all services
   docker-compose down && docker-compose up -d
   
   # Check health
   curl -f http://localhost:8000/health
   ```

3. **Escalation**
   - Notify operations team
   - Check monitoring dashboards
   - Review recent changes

### Data Loss

#### Immediate Actions
1. **Stop Writes**
   ```bash
   # Stop API to prevent further writes
   docker-compose stop api worker
   ```

2. **Assess Damage**
   ```sql
   -- Check data integrity
   SELECT COUNT(*) FROM audit_logs;
   SELECT MAX(created_at) FROM audit_logs;
   ```

3. **Restore from Backup**
   ```bash
   # Find latest backup
   ls -la backups/ | tail -5
   
   # Restore
   ./scripts/restore.sh backup_YYYYMMDD_HHMMSS
   ```

### Security Incident

#### Immediate Actions
1. **Isolate System**
   ```bash
   # Stop external access
   docker-compose stop nginx
   
   # Check for unauthorized access
   docker-compose logs api | grep -i "401\|403\|unauthorized"
   ```

2. **Preserve Evidence**
   ```bash
   # Create forensic backup
   ./scripts/backup.sh -d /secure/forensics/
   
   # Capture logs
   docker-compose logs > incident_logs_$(date +%Y%m%d_%H%M%S).txt
   ```

3. **Notify Security Team**
   - Document incident details
   - Preserve all logs and evidence
   - Follow incident response procedures

This troubleshooting guide provides comprehensive procedures for diagnosing and resolving issues in the Audit Log Framework. Regular review and practice of these procedures will help maintain system reliability and minimize downtime.