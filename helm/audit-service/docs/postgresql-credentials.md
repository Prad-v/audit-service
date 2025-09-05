# PostgreSQL Credentials Configuration

This document explains how to properly configure PostgreSQL credentials in the audit-service Helm chart.

## Overview

The Helm chart supports two PostgreSQL deployment modes:
1. **Internal PostgreSQL** - Uses the PostgreSQL subchart with managed credentials
2. **External PostgreSQL** - Connects to an existing PostgreSQL instance

## Security Best Practices

- **Never hardcode passwords** in values files
- **Use Kubernetes secrets** for all sensitive data
- **Implement external secret management** for production environments
- **Rotate credentials regularly**
- **Use least privilege principle** for database users

## Internal PostgreSQL Configuration

When using the internal PostgreSQL subchart (`database.postgresql.enabled: true`):

### 1. Create PostgreSQL Credentials Secret

```bash
# Create a secret with PostgreSQL credentials
kubectl create secret generic postgresql-credentials \
  --from-literal=postgres-password="your-superuser-password" \
  --from-literal=username="audit_user" \
  --from-literal=password="your-audit-user-password" \
  --from-literal=database="audit_logs" \
  --from-literal=readonly_username="readonly_user" \
  --from-literal=readonly_password="your-readonly-password"
```

### 2. Update Values File

```yaml
database:
  postgresql:
    enabled: true
    internal:
      postgresql:
        auth:
          # These will be overridden by secrets
          postgresPassword: "{{ .Values.database.postgresql.credentials.postgresPassword }}"
          database: "{{ .Values.database.postgresql.credentials.database }}"
          username: "{{ .Values.database.postgresql.credentials.username }}"
          password: "{{ .Values.database.postgresql.credentials.password }}"
        credentials:
          secretName: "postgresql-credentials"
          usernameKey: "username"
          passwordKey: "password"
          databaseKey: "database"
          postgresPasswordKey: "postgres-password"

  credentials:
    secretName: "postgresql-credentials"
    databases:
      - name: "audit_logs"
        description: "Main audit logs database"
      - name: "alerting_db"
        description: "Alerting service database"
      - name: "events_db"
        description: "Events service database"
    users:
      - username: "audit_user"
        description: "Main application user"
        databases: ["audit_logs", "alerting_db", "events_db"]
      - username: "readonly_user"
        description: "Read-only user for monitoring"
        databases: ["audit_logs"]
        readonly: true
```

### 3. Configure Secrets

```yaml
secrets:
  postgresql:
    secretName: "postgresql-credentials"
    postgresPassword: "{{ .Values.secrets.postgresql.postgresPassword }}"
    auditUserPassword: "{{ .Values.secrets.postgresql.auditUserPassword }}"
    readonlyUserPassword: "{{ .Values.secrets.postgresql.readonlyUserPassword }}"
```

## External PostgreSQL Configuration

When using an external PostgreSQL instance (`database.postgresql.enabled: false`):

### 1. Create External PostgreSQL Secret

```bash
# Create a secret for external PostgreSQL
kubectl create secret generic external-postgresql-credentials \
  --from-literal=password="your-external-postgres-password"
```

### 2. Update Values File

```yaml
database:
  postgresql:
    enabled: false
    external:
      host: "your-postgresql-host"
      port: 5432
      database: "audit_logs"
      username: "audit_user"
      sslMode: "require"
      poolSize: 20
      maxOverflow: 30
      poolTimeout: 30
      poolRecycle: 3600
      passwordSecret:
        secretName: "external-postgresql-credentials"
        passwordKey: "password"
```

## Environment Variables

The following environment variables are automatically injected into all deployments:

### Internal PostgreSQL
- `POSTGRES_USERNAME` - Database username
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DATABASE` - Database name

### External PostgreSQL
- `EXTERNAL_POSTGRES_PASSWORD` - External database password

## Database URLs

Database URLs are constructed using environment variables and secrets:

```yaml
# Internal PostgreSQL
DATABASE_URL: "postgresql+asyncpg://$(POSTGRES_USERNAME):$(POSTGRES_PASSWORD)@{{ include "audit-service.fullname" . }}-postgresql:5432/$(POSTGRES_DATABASE)"

# External PostgreSQL
DATABASE_URL: "postgresql+asyncpg://{{ .Values.database.postgresql.external.username }}:$(EXTERNAL_POSTGRES_PASSWORD)@{{ .Values.database.postgresql.external.host }}:{{ .Values.database.postgresql.external.port }}/{{ .Values.database.postgresql.external.database }}"
```

## Using External Secret Management

For production environments, use external secret management tools:

### Sealed Secrets
```bash
# Install sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.17.0/controller.yaml

# Create sealed secret
kubectl create secret generic postgresql-credentials \
  --from-literal=password="your-password" \
  --dry-run=client -o yaml | \
  kubeseal --format yaml > sealed-postgresql-credentials.yaml
```

### External Secrets Operator
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: postgresql-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: postgresql-credentials
  data:
    - secretKey: password
      remoteRef:
        key: postgresql/audit-service
        property: password
```

## Troubleshooting

### Common Issues

1. **Secret not found**
   - Ensure the secret exists in the correct namespace
   - Verify secret name matches the configuration

2. **Authentication failed**
   - Check password in the secret
   - Verify username and database name
   - Ensure database user has proper permissions

3. **Connection refused**
   - Verify PostgreSQL host and port
   - Check network policies and firewall rules
   - Ensure PostgreSQL is running and accessible

### Debug Commands

```bash
# Check if secret exists
kubectl get secret postgresql-credentials -o yaml

# Verify secret contents (base64 decoded)
kubectl get secret postgresql-credentials -o jsonpath='{.data.password}' | base64 -d

# Check pod environment variables
kubectl exec -it <pod-name> -- env | grep POSTGRES

# Test database connection
kubectl exec -it <pod-name> -- python -c "
import asyncpg
import asyncio

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='audit_user',
            password='your-password',
            database='audit_logs'
        )
        print('Connection successful')
        await conn.close()
    except Exception as e:
        print(f'Connection failed: {e}')

asyncio.run(test_connection())
"
```

## Migration Guide

### From Hardcoded Passwords

1. **Remove hardcoded passwords** from values files
2. **Create Kubernetes secrets** with proper credentials
3. **Update Helm chart** to use secret references
4. **Test deployment** with new configuration
5. **Update CI/CD** to handle secret management

### Example Migration

```yaml
# Before (insecure)
database:
  postgresql:
    internal:
      postgresql:
        auth:
          password: "hardcoded-password"

# After (secure)
database:
  postgresql:
    internal:
      postgresql:
        auth:
          password: "{{ .Values.database.postgresql.credentials.password }}"
  credentials:
    secretName: "postgresql-credentials"
```

## Security Checklist

- [ ] No hardcoded passwords in values files
- [ ] All credentials stored in Kubernetes secrets
- [ ] External secret management implemented
- [ ] Database users have minimal required permissions
- [ ] SSL/TLS enabled for external connections
- [ ] Credentials rotated regularly
- [ ] Access logs enabled and monitored
- [ ] Network policies restrict database access
- [ ] Secrets encrypted at rest
- [ ] RBAC properly configured
