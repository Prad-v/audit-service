# Audit Service Helm Chart

A comprehensive Helm chart for deploying the Audit Service with flexible database configuration options.

## Features

- **Flexible Database Configuration**: Choose between internal subcharts or external services
- **PostgreSQL Support**: Built-in PostgreSQL subchart or connect to external database
- **NATS Integration**: Built-in NATS subchart or connect to external message broker
- **Redis Support**: Connect to external Redis cache
- **Production Ready**: Includes monitoring, security, and scaling configurations

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Storage class for persistent volumes (if using internal databases)

## Quick Start

### 1. Add Required Helm Repositories

```bash
# Add Bitnami repository for PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami

# Add NATS repository
helm repo add nats https://nats-io.github.io/k8s/helm/charts/

# Update repositories
helm repo update
```

### 2. Install with Internal Databases (Default)

```bash
# Install with internal PostgreSQL and NATS subcharts
helm install audit-service ./audit-service \
  --namespace audit-service \
  --create-namespace
```

### 3. Install with External Databases

```bash
# Install using external database services
helm install audit-service ./audit-service \
  --namespace audit-service \
  --create-namespace \
  --values values-external.yaml
```

## Configuration

### PostgreSQL Credentials Configuration

**⚠️ IMPORTANT: Security Best Practices**

The Helm chart now requires proper PostgreSQL credentials configuration using Kubernetes secrets. Hardcoded passwords are no longer supported.

#### Quick Setup

Use the provided script to create PostgreSQL secrets:

```bash
# Create secrets for internal PostgreSQL
./scripts/create-postgresql-secrets.sh -n audit-service

# Create secrets for external PostgreSQL
./scripts/create-postgresql-secrets.sh -e -n audit-service
```

#### Manual Secret Creation

```bash
# For internal PostgreSQL
kubectl create secret generic postgresql-credentials \
  --namespace=audit-service \
  --from-literal=postgres-password="your-superuser-password" \
  --from-literal=username="audit_user" \
  --from-literal=password="your-audit-user-password" \
  --from-literal=database="audit_logs"

# For external PostgreSQL
kubectl create secret generic external-postgresql-credentials \
  --namespace=audit-service \
  --from-literal=password="your-external-password"
```

For detailed configuration instructions, see [PostgreSQL Credentials Documentation](docs/postgresql-credentials.md).

### Database Configuration Options

The chart supports two deployment modes:

#### Mode 1: Internal Subcharts (Default)

Uses built-in PostgreSQL and NATS subcharts for self-contained deployment.

```yaml
database:
  postgresql:
    enabled: true  # Use internal PostgreSQL
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
  
  nats:
    enabled: true  # Use internal NATS
    internal:
      nats:
        jetstream:
          enabled: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
```

#### Mode 2: External Services

Connect to existing PostgreSQL and NATS services.

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
  
  nats:
    enabled: false  # Disable internal NATS
    external:
      host: "your-nats-host"
      port: 4222
      jetstream:
        enabled: true
```

### Redis Configuration

Redis is always external (no subchart included):

```yaml
database:
  redis:
    enabled: true
    host: "your-redis-host"
    port: 6379
    password: "your-redis-password"
    database: 0
```

## Values Reference

### Global Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.environment` | Environment name | `production` |
| `global.imageRegistry` | Global image registry | `""` |
| `global.imagePullSecrets` | Global image pull secrets | `[]` |

### Database Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `database.postgresql.enabled` | Enable PostgreSQL subchart | `true` |
| `database.postgresql.internal.*` | Internal PostgreSQL configuration | See values.yaml |
| `database.postgresql.external.*` | External PostgreSQL configuration | See values.yaml |
| `database.nats.enabled` | Enable NATS subchart | `true` |
| `database.nats.internal.*` | Internal NATS configuration | See values.yaml |
| `database.nats.external.*` | External NATS configuration | See values.yaml |
| `database.redis.*` | Redis configuration | See values.yaml |

### Application Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.replicas` | Backend service replicas | `3` |
| `frontend.replicas` | Frontend service replicas | `2` |
| `worker.replicas` | Worker service replicas | `2` |
| `alerting.replicas` | Alerting service replicas | `2` |

## Examples

### Example 1: Production with External Databases

```yaml
# values-prod.yaml
global:
  environment: production
  imageRegistry: "gcr.io/your-project"

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
  jwtSecretKey: "your-jwt-secret"
```

### Example 2: Development with Internal Databases

```yaml
# values-dev.yaml
global:
  environment: development

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
    host: "redis-service"
    port: 6379
```

## Upgrading

### From Previous Versions

If upgrading from a version without database subcharts:

1. **Backup your data** if using external databases
2. **Review the new configuration** options
3. **Update your values** to use the new database configuration
4. **Upgrade the chart**:

```bash
helm upgrade audit-service ./audit-service \
  --namespace audit-service \
  --values your-values.yaml
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Failures

**Symptoms**: Pods in CrashLoopBackOff with database connection errors

**Solutions**:
- Verify database hostnames are resolvable
- Check database credentials
- Ensure database services are accessible from the cluster

#### 2. Subchart Installation Failures

**Symptoms**: Helm install fails with subchart errors

**Solutions**:
- Ensure Helm repositories are added and updated
- Check subchart versions compatibility
- Verify storage class exists for persistent volumes

#### 3. Configuration Mismatch

**Symptoms**: Services start but can't connect to databases

**Solutions**:
- Verify ConfigMap contains correct database URLs
- Check environment variables in pod descriptions
- Ensure database configuration matches actual services

### Debugging Commands

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
```

## Security Considerations

### Secrets Management

- **Never commit secrets** to version control
- Use **external secret management** (e.g., Sealed Secrets, External Secrets Operator)
- **Rotate secrets** regularly
- Use **RBAC** to limit access to secrets

### Network Security

- **Enable TLS** for database connections in production
- Use **network policies** to restrict pod-to-pod communication
- **Isolate database services** in separate namespaces if possible

### Database Security

- **Use strong passwords** for database users
- **Limit database permissions** to minimum required
- **Enable SSL/TLS** for database connections
- **Regular security updates** for database images

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review [GitHub issues](https://github.com/your-org/audit-service/issues)
3. Contact the Audit Service team

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
