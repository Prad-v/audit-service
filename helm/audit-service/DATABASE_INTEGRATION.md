# Database Integration Guide

## Overview

The Audit Service Helm chart now supports flexible database configuration with two deployment modes:

1. **Internal Subcharts Mode**: Uses built-in PostgreSQL and NATS subcharts for self-contained deployment
2. **External Services Mode**: Connects to existing PostgreSQL and NATS services

## Architecture

### Internal Subcharts Mode (Default)

```
┌─────────────────────────────────────────────────────────────┐
│                    Audit Service Chart                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   PostgreSQL    │  │      NATS       │  │    Redis    │ │
│  │   Subchart      │  │    Subchart     │  │  (External) │ │
│  │                 │  │                 │  │             │ │
│  │ • Database      │  │ • Message       │  │ • Cache     │ │
│  │ • Auth          │  │   Broker        │  │ • Sessions  │ │
│  │ • Persistence   │  │ • JetStream     │  │             │ │
│  │ • Metrics       │  │ • Clustering    │  │             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### External Services Mode

```
┌─────────────────────────────────────────────────────────────┐
│                    Audit Service Chart                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   PostgreSQL    │  │      NATS       │  │    Redis    │ │
│  │   (External)    │  │   (External)    │  │  (External) │ │
│  │                 │  │                 │  │             │ │
│  │ • Your DB       │  │ • Your NATS     │  │ • Your      │ │
│  │ • Your Auth     │  │ • Your Config   │  │   Cache     │ │
│  │ • Your Network  │  │ • Your Network  │  │ • Your      │ │
│  │ • Your Security │  │ • Your Security │  │   Network   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### 1. Internal Subcharts Configuration

```yaml
database:
  postgresql:
    enabled: true  # Enable internal PostgreSQL
    internal:
      postgresql:
        auth:
          username: "audit_user"
          password: "audit_password"
          database: "audit_logs"
        primary:
          persistence:
            enabled: true
            size: 10Gi
        metrics:
          enabled: true
  
  nats:
    enabled: true  # Enable internal NATS
    internal:
      nats:
        jetstream:
          enabled: true
          memStorage:
            size: 1Gi
          fileStorage:
            size: 10Gi
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
  
  redis:
    enabled: true
    host: "your-redis-host"
    port: 6379
```

### 2. External Services Configuration

```yaml
database:
  postgresql:
    enabled: false  # Disable internal PostgreSQL
    external:
      host: "your-postgres-host"
      port: 5432
      database: "audit_logs"
      username: "audit_user"
      password: "your-secure-password"
      sslMode: "prefer"
  
  nats:
    enabled: false  # Disable internal NATS
    external:
      host: "your-nats-host"
      port: 4222
      jetstream:
        enabled: true
  
  redis:
    enabled: true
    host: "your-redis-host"
    port: 6379
    password: "your-redis-password"
```

## Database URLs

The chart automatically generates database URLs based on your configuration:

### Internal Mode URLs

- **DATABASE_URL**: `postgresql+asyncpg://audit_user:audit_password@release-name-postgresql:5432/audit_logs`
- **NATS_URL**: `nats://release-name-nats:4222`
- **REDIS_URL**: `redis://your-redis-host:6379/0`
- **ALERTING_DATABASE_URL**: `postgresql+asyncpg://audit_user:audit_password@release-name-postgresql:5432/alerting_db`
- **EVENTS_DATABASE_URL**: `postgresql+asyncpg://audit_user:audit_password@release-name-postgresql:5432/events_db`

### External Mode URLs

- **DATABASE_URL**: `postgresql+asyncpg://your-user:your-password@your-host:5432/your-database`
- **NATS_URL**: `nats://your-nats-host:4222`
- **REDIS_URL**: `redis://your-redis-host:6379/0`
- **ALERTING_DATABASE_URL**: `postgresql+asyncpg://your-user:your-password@your-host:5432/alerting_db`
- **EVENTS_DATABASE_URL**: `postgresql+asyncpg://your-user:your-password@your-host:5432/events_db`

## Deployment Examples

### Example 1: Development with Internal Databases

```bash
# Install with internal PostgreSQL and NATS
helm install audit-service-dev ./audit-service \
  --namespace audit-service-dev \
  --create-namespace \
  --values values-internal.yaml
```

**values-internal.yaml**:
```yaml
database:
  postgresql:
    enabled: true
    internal:
      postgresql:
        auth:
          username: "dev_user"
          password: "dev_password"
          database: "audit_logs_dev"
        primary:
          persistence:
            size: 5Gi
  
  nats:
    enabled: true
    internal:
      nats:
        jetstream:
          enabled: true
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
  
  redis:
    enabled: true
    host: "host.docker.internal"  # Connect to Docker Compose
    port: 6379
```

### Example 2: Production with External Databases

```bash
# Install with external database services
helm install audit-service ./audit-service \
  --namespace audit-service \
  --create-namespace \
  --values values-external.yaml
```

**values-external.yaml**:
```yaml
database:
  postgresql:
    enabled: false
    external:
      host: "prod-postgres.example.com"
      port: 5432
      database: "audit_logs_prod"
      username: "audit_user"
      password: "{{ .Values.secrets.postgresPassword }}"
  
  nats:
    enabled: false
    external:
      host: "prod-nats.example.com"
      port: 4222
  
  redis:
    enabled: true
    host: "prod-redis.example.com"
    port: 6379
    password: "{{ .Values.secrets.redisPassword }}"

secrets:
  postgresPassword: "your-secure-password"
  redisPassword: "your-redis-password"
```

## Migration Guide

### From Previous Versions

If upgrading from a version without database subcharts:

1. **Backup your data** if using external databases
2. **Review the new configuration** options
3. **Choose your deployment mode**:
   - **Internal**: For self-contained deployments
   - **External**: For existing infrastructure
4. **Update your values** to use the new database configuration
5. **Upgrade the chart**:

```bash
helm upgrade audit-service ./audit-service \
  --namespace audit-service \
  --values your-new-values.yaml
```

### From Docker Compose

If migrating from Docker Compose:

1. **Keep Docker Compose running** for Redis (if needed)
2. **Use external mode** for PostgreSQL and NATS initially
3. **Gradually migrate** to internal subcharts if desired
4. **Update Redis configuration** to point to your production Redis

## Security Considerations

### Internal Subcharts

- **Default passwords**: Change from default values in production
- **Network isolation**: Services communicate within the cluster
- **Persistent storage**: Ensure proper storage class and backup strategy
- **Resource limits**: Configure appropriate CPU/memory limits

### External Services

- **Network security**: Ensure secure connections (TLS, VPN, etc.)
- **Authentication**: Use strong passwords and proper user management
- **Access control**: Limit database access to required permissions
- **Monitoring**: Monitor external service health and performance

## Troubleshooting

### Common Issues

#### 1. Database Connection Failures

**Symptoms**: Pods in CrashLoopBackOff with database connection errors

**Solutions**:
- Verify database hostnames are resolvable
- Check database credentials
- Ensure database services are accessible from the cluster
- Verify ConfigMap contains correct database URLs

#### 2. Subchart Installation Failures

**Symptoms**: Helm install fails with subchart errors

**Solutions**:
- Ensure Helm repositories are added and updated
- Check subchart versions compatibility
- Verify storage class exists for persistent volumes
- Check resource quotas and limits

#### 3. Configuration Mismatch

**Symptoms**: Services start but can't connect to databases

**Solutions**:
- Verify ConfigMap contains correct database URLs
- Check environment variables in pod descriptions
- Ensure database configuration matches actual services
- Check service names and ports

### Debug Commands

```bash
# Check pod status
kubectl get pods -n audit-service

# View pod logs
kubectl logs -n audit-service deployment/audit-service-backend

# Check ConfigMap
kubectl get configmap -n audit-service
kubectl describe configmap audit-service-config -n audit-service

# Check services
kubectl get services -n audit-service

# Check persistent volumes
kubectl get pvc -n audit-service

# Check Helm release
helm list -n audit-service
helm get values audit-service -n audit-service
```

## Best Practices

### Development

- Use **internal subcharts** for quick setup and testing
- Configure **smaller resource limits** for development
- Use **host.docker.internal** to connect to Docker Compose services
- **Disable metrics** to reduce resource usage

### Staging

- Use **external services** to match production environment
- Test **database migrations** and **upgrade procedures**
- Validate **security configurations** and **network policies**
- Test **backup and restore** procedures

### Production

- Use **external services** for existing infrastructure
- Implement **proper monitoring** and **alerting**
- Configure **backup strategies** and **disaster recovery**
- Use **external secret management** for sensitive data
- Implement **network policies** and **security contexts**

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [README.md](README.md)
3. Check [GitHub issues](https://github.com/your-org/audit-service/issues)
4. Contact the Audit Service team

## Future Enhancements

- **Redis subchart**: Add built-in Redis support
- **Database migration tools**: Automated schema updates
- **Backup/restore**: Built-in backup solutions
- **Monitoring**: Enhanced metrics and dashboards
- **Security**: Additional security features and policies

