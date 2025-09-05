# Helm Chart Scripts

This directory contains utility scripts for managing the audit-service Helm chart deployment.

## Available Scripts

### 1. `create-postgresql-secrets.sh`

Creates Kubernetes secrets for PostgreSQL credentials required by the audit-service.

#### Features
- Generates secure random passwords for internal PostgreSQL
- Supports both internal and external PostgreSQL configurations
- Creates secrets in specified namespaces
- Verifies secret creation
- Provides colored output and helpful messages

#### Usage

```bash
# Create secrets for internal PostgreSQL in default namespace
./create-postgresql-secrets.sh

# Create secrets for internal PostgreSQL in specific namespace
./create-postgresql-secrets.sh -n audit-service

# Create secrets for external PostgreSQL
./create-postgresql-secrets.sh -e -n audit-service

# Create secrets with custom secret name
./create-postgresql-secrets.sh -s my-postgresql-secret -n audit-service

# Show help
./create-postgresql-secrets.sh -h
```

#### Options
- `-n, --namespace NAMESPACE` - Kubernetes namespace (default: default)
- `-s, --secret-name NAME` - Secret name (default: postgresql-credentials)
- `-e, --external` - Create secrets for external PostgreSQL
- `-h, --help` - Show help message

#### Example Output

```bash
[INFO] PostgreSQL Secrets Creation Script for Audit Service

[SUCCESS] Connected to Kubernetes cluster
[INFO] Namespace 'audit-service' already exists
[INFO] Creating internal PostgreSQL secrets...
[SUCCESS] Internal PostgreSQL secret 'postgresql-credentials' created in namespace 'audit-service'
[INFO] Verifying secret creation...
[SUCCESS] Secret 'postgresql-credentials' exists in namespace 'audit-service'

[WARNING] IMPORTANT: Save these passwords securely:
PostgreSQL Superuser Password: xK9mP2nQ8vR5sT7wY
Audit User Password: aB3cD4eF6gH8iJ9kL
Readonly User Password: mN2oP4qR6sT8uV0wX

[SUCCESS] PostgreSQL secrets setup completed successfully!

[INFO] Next steps:
1. Update your Helm values to use the created secret
2. Deploy the audit-service with: helm upgrade --install audit-service ./helm/audit-service
3. Store the generated passwords securely
```

## Prerequisites

- `kubectl` configured and connected to a Kubernetes cluster
- `openssl` for password generation (usually available by default)
- Appropriate permissions to create secrets in the target namespace

## Security Notes

- **Never commit passwords to version control**
- **Store generated passwords securely** (password manager, secure notes, etc.)
- **Use external secret management** for production environments
- **Rotate credentials regularly**
- **Follow least privilege principle** for database users

## Integration with Helm Chart

After running the script, update your Helm values to reference the created secret:

```yaml
database:
  credentials:
    secretName: "postgresql-credentials"  # Created by the script
  postgresql:
    enabled: true
    internal:
      postgresql:
        auth:
          # These will be overridden by the secret
          postgresPassword: "{{ .Values.database.postgresql.credentials.postgresPassword }}"
          database: "{{ .Values.database.postgresql.credentials.database }}"
          username: "{{ .Values.database.postgresql.credentials.username }}"
          password: "{{ .Values.database.postgresql.credentials.password }}"
```

## Troubleshooting

### Common Issues

1. **Permission denied**
   - Ensure you have RBAC permissions to create secrets
   - Check if you're in the correct namespace

2. **kubectl not found**
   - Install kubectl and configure it properly
   - Verify cluster connectivity with `kubectl cluster-info`

3. **Secret already exists**
   - The script will update existing secrets
   - Use `-s` flag to specify a different secret name

4. **Password generation fails**
   - Ensure `openssl` is installed
   - Check if the system has sufficient entropy

### Debug Commands

```bash
# Check if secret exists
kubectl get secret postgresql-credentials -n <namespace>

# View secret details
kubectl describe secret postgresql-credentials -n <namespace>

# Check namespace
kubectl get namespace <namespace>

# Verify cluster connectivity
kubectl cluster-info
```

## Contributing

When adding new scripts:

1. Follow the existing script structure and style
2. Include proper error handling and validation
3. Add usage documentation and examples
4. Test thoroughly in different environments
5. Update this README with new script information

## License

This script is part of the audit-service project and follows the same license terms.
