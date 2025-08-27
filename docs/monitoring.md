# Monitoring & Observability Guide

This document provides comprehensive information about the monitoring and observability infrastructure for the Audit Log Framework.

## Overview

The monitoring stack includes:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Structured Logging**: Correlation IDs and centralized logging
- **Health Checks**: Service health monitoring
- **Exporters**: System and service metrics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Prometheus    │───▶│    Grafana      │
│   (Metrics)     │    │   (Storage)     │    │  (Dashboards)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  AlertManager   │───▶│  Notifications  │
                       │   (Routing)     │    │ (Email/Slack)   │
                       └─────────────────┘    └─────────────────┘
```

## Components

### 1. Prometheus Metrics

#### Application Metrics
- **API Metrics**: Request rate, latency, error rate
- **Audit Log Metrics**: Creation rate, batch sizes, query performance
- **Database Metrics**: Connection pool, query duration
- **Cache Metrics**: Hit rate, miss rate
- **NATS Metrics**: Message rate, publish errors

#### System Metrics
- **Node Exporter**: CPU, memory, disk, network
- **PostgreSQL Exporter**: Database performance
- **Redis Exporter**: Cache performance
- **NATS Exporter**: Message broker metrics
- **cAdvisor**: Container metrics

#### Custom Metrics
```python
from app.utils.metrics import audit_metrics

# Increment counters
audit_metrics.audit_logs_created.labels(
    tenant_id="tenant-123",
    event_type="user_login"
).inc()

# Observe histograms
audit_metrics.query_duration.labels(
    query_type="search"
).observe(0.5)

# Set gauges
audit_metrics.active_tenants.set(42)
```

### 2. Grafana Dashboards

#### System Overview Dashboard
- API request rate and latency
- Total audit logs created
- Database connections
- Cache hit rate
- NATS message rate

**URL**: http://localhost:3001/d/audit-system-overview

#### Performance Dashboard
- Query performance percentiles
- Batch processing metrics
- Database operation performance
- Error rates
- Export performance

**URL**: http://localhost:3001/d/audit-performance

#### Custom Dashboards
Create custom dashboards by:
1. Accessing Grafana at http://localhost:3001
2. Login: admin / admin123
3. Create new dashboard
4. Add panels with Prometheus queries

### 3. Alerting Rules

#### Critical Alerts
- **System Down**: Service unavailable
- **Database Connection Lost**: No DB connectivity
- **Tenant Isolation Breach**: Security violation
- **Health Check Failing**: Service health degraded

#### Warning Alerts
- **High Error Rate**: > 10 errors/second
- **High API Latency**: 95th percentile > 2s
- **Low Cache Hit Rate**: < 70%
- **High Memory Usage**: > 1GB

#### Business Alerts
- **No Audit Logs Created**: No activity for 15 minutes
- **High Audit Volume**: > 1000 logs/second
- **Slow Export Operations**: > 5 minutes

### 4. Structured Logging

#### Correlation IDs
Every request gets a unique correlation ID that tracks the request through all services:

```json
{
  "timestamp": "2025-08-27T08:15:00Z",
  "level": "info",
  "message": "Audit log created",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "tenant_id": "tenant-123",
  "user_id": "user-456",
  "event_type": "user_login"
}
```

#### Log Categories
- **HTTP**: Request/response logging
- **Performance**: Operation timing
- **Audit**: System audit events
- **Security**: Security-related events
- **Business**: Application logic events

#### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General information
- **WARNING**: Warning conditions
- **ERROR**: Error conditions
- **CRITICAL**: Critical conditions

## Accessing Monitoring Services

### Prometheus
- **URL**: http://localhost:9090
- **Purpose**: Metrics storage and querying
- **Key Endpoints**:
  - `/metrics`: Application metrics
  - `/targets`: Scrape targets status
  - `/alerts`: Active alerts

### Grafana
- **URL**: http://localhost:3001
- **Login**: admin / admin123
- **Purpose**: Visualization and dashboards
- **Pre-configured Dashboards**:
  - Audit System Overview
  - Performance Dashboard

### AlertManager
- **URL**: http://localhost:9093
- **Purpose**: Alert routing and notifications
- **Features**:
  - Alert grouping
  - Notification routing
  - Silence management

### Exporters
- **Node Exporter**: http://localhost:9100/metrics
- **PostgreSQL Exporter**: http://localhost:9187/metrics
- **Redis Exporter**: http://localhost:9121/metrics
- **NATS Exporter**: http://localhost:7777/metrics
- **cAdvisor**: http://localhost:8080

## Health Checks

### Application Health
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-08-27T08:15:00Z",
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "response_time_ms": 5},
    "cache": {"status": "healthy", "response_time_ms": 2},
    "messaging": {"status": "healthy", "response_time_ms": 3}
  }
}
```

### Detailed Metrics Health
```bash
curl http://localhost:8000/api/v1/metrics/health
```

### System Statistics
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/v1/metrics/stats
```

## Monitoring Best Practices

### 1. Metric Naming
- Use consistent prefixes: `audit_*`
- Include units in names: `_seconds`, `_bytes`, `_total`
- Use labels for dimensions: `{tenant_id="", event_type=""}`

### 2. Alert Design
- **Actionable**: Every alert should require action
- **Contextual**: Include runbook links
- **Severity-based**: Critical, warning, info
- **Avoid noise**: Use proper thresholds

### 3. Dashboard Design
- **User-focused**: Show what users care about
- **Hierarchical**: Overview → detailed views
- **Time-based**: Show trends over time
- **Actionable**: Link to runbooks

### 4. Log Management
- **Structured**: Use JSON format
- **Contextual**: Include correlation IDs
- **Searchable**: Use consistent field names
- **Retention**: Configure appropriate retention

## Troubleshooting

### Common Issues

#### High Memory Usage
1. Check Grafana dashboard for memory trends
2. Review application logs for memory leaks
3. Check database connection pool size
4. Monitor cache usage patterns

#### Slow API Response
1. Check API latency dashboard
2. Review database query performance
3. Check cache hit rates
4. Analyze slow query logs

#### Alert Fatigue
1. Review alert thresholds
2. Implement alert grouping
3. Add proper silencing rules
4. Create escalation policies

### Debugging Commands

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f api
docker-compose logs -f prometheus
docker-compose logs -f grafana

# Check metrics endpoint
curl http://localhost:8000/api/v1/metrics

# Test alert rules
curl -X POST http://localhost:9090/-/reload

# Check AlertManager status
curl http://localhost:9093/api/v1/status
```

## Configuration

### Environment Variables
```bash
# Monitoring configuration
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
METRICS_ENABLED=true
LOG_LEVEL=INFO
CORRELATION_ID_ENABLED=true
```

### Prometheus Configuration
Located in `monitoring/prometheus/prometheus.yml`:
- Scrape intervals
- Target configurations
- Alert rule files
- Storage settings

### Grafana Configuration
Located in `monitoring/grafana/grafana.ini`:
- Security settings
- Dashboard provisioning
- Data source configuration
- Plugin settings

### AlertManager Configuration
Located in `monitoring/alertmanager/alertmanager.yml`:
- Routing rules
- Notification channels
- Grouping settings
- Inhibition rules

## Scaling Considerations

### High Volume Environments
- Increase Prometheus retention
- Use remote storage for metrics
- Implement metric sampling
- Configure alert batching

### Multi-Instance Deployments
- Use service discovery
- Configure load balancer health checks
- Implement distributed tracing
- Use centralized logging

### Production Readiness
- Set up external alerting
- Configure backup strategies
- Implement monitoring monitoring
- Create operational runbooks

## Security

### Access Control
- Grafana authentication
- Prometheus security
- Network isolation
- API authentication

### Data Protection
- Metric data encryption
- Log data sanitization
- Alert notification security
- Backup encryption

## Maintenance

### Regular Tasks
- Review alert thresholds
- Update dashboards
- Clean up old metrics
- Test alert notifications

### Capacity Planning
- Monitor storage usage
- Plan for growth
- Review retention policies
- Optimize queries

This monitoring setup provides comprehensive observability for the Audit Log Framework, enabling proactive monitoring, quick troubleshooting, and performance optimization.