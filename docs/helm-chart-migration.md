# Helm Chart Migration Guide

## Overview

This document describes the migration from raw Kubernetes manifests to a comprehensive Helm chart for the Audit Service. The Helm chart provides better deployment management, versioning, and configuration flexibility.

## What's Changed

### Before: Raw Kubernetes Manifests
- Individual YAML files in `k8s/` directory
- Manual image tag updates
- Environment-specific configurations scattered
- No versioning or rollback capabilities
- Manual deployment process

### After: Helm Chart
- Structured Helm chart in `helm/audit-service/`
- Automated versioning and packaging
- Environment-specific values files
- CI/CD integration with automated publishing
- Rollback and upgrade capabilities

## Helm Chart Structure

```
helm/audit-service/
├── Chart.yaml                 # Chart metadata
├── values.yaml               # Default values
├── README.md                 # Chart documentation
├── templates/                # Kubernetes templates
│   ├── _helpers.tpl         # Template helpers
│   ├── namespace.yaml       # Namespace, quotas, limits
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── worker-deployment.yaml
│   ├── services.yaml        # Backend and frontend services
│   ├── ingress.yaml         # Ingress configuration
│   ├── hpa.yaml            # Horizontal Pod Autoscalers
│   ├── rbac.yaml           # ServiceAccount, Role, RoleBinding
│   ├── configmap.yaml      # Application configuration
│   └── secret.yaml         # Sensitive data
└── values/                  # Environment-specific values
    ├── values-dev.yaml
    ├── values-staging.yaml
    └── values-prod.yaml
```

## Key Features

### 🔧 **Configuration Management**
- Centralized configuration in `values.yaml`
- Environment-specific overrides
- Secret management integration
- Configurable resource limits

### 🚀 **Deployment Features**
- Rolling updates with configurable strategies
- Health checks and readiness probes
- Resource quotas and limits
- Horizontal Pod Autoscaling

### 🔒 **Security Features**
- Non-root containers
- Security contexts
- RBAC integration
- Network policies support

### 📊 **Monitoring Integration**
- Prometheus metrics endpoints
- ServiceMonitor configuration
- Grafana dashboard integration
- Custom alerting rules

## Migration Steps

### 1. **Install Helm Chart Locally**

```bash
# Test the chart locally
python3 scripts/test-helm-chart.py

# Install in development
helm install audit-service-dev ./helm/audit-service \
  --namespace audit-service-dev \
  --create-namespace \
  -f helm/audit-service/values/values-dev.yaml
```

### 2. **Update CI/CD Pipeline**

The CI/CD pipeline has been updated to:
- Package Helm charts automatically
- Generate versioned releases
- Publish to OCI registries
- Deploy using Helm instead of raw manifests

### 3. **Environment Migration**

#### Development
```bash
helm install audit-service-dev ./helm/audit-service \
  --namespace audit-service-dev \
  --create-namespace \
  -f helm/audit-service/values/values-dev.yaml \
  --set image.tag=dev
```

#### Staging
```bash
helm install audit-service-staging ./helm/audit-service \
  --namespace audit-service-staging \
  --create-namespace \
  -f helm/audit-service/values/values-staging.yaml \
  --set image.tag=staging
```

#### Production
```bash
helm install audit-service ./helm/audit-service \
  --namespace audit-service \
  --create-namespace \
  -f helm/audit-service/values/values-prod.yaml \
  --set image.tag=latest
```

## Configuration Options

### Image Configuration
```yaml
image:
  repository: gcr.io/PROJECT_ID/audit-service
  tag: latest
  pullPolicy: Always
  frontend:
    repository: gcr.io/PROJECT_ID/audit-service-frontend
    tag: latest
```

### Replica Configuration
```yaml
app:
  replicas:
    backend: 3
    frontend: 2
    worker: 2
```

### Resource Limits
```yaml
backend:
  resources:
    requests:
      cpu: 200m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi
```

### Ingress Configuration
```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: audit.example.com
      paths:
        - path: /
          pathType: Prefix
          service:
            name: audit-service-frontend
            port: 80
        - path: /api
          pathType: Prefix
          service:
            name: audit-service-backend
            port: 8000
```

## CI/CD Integration

### Automated Chart Packaging
- **Trigger**: Every commit and release
- **Process**: 
  1. Analyze changes to determine version bump
  2. Update Chart.yaml with new version
  3. Package chart as .tgz file
  4. Validate templates and lint chart
  5. Upload as workflow artifact

### Version Generation
The chart version is automatically generated based on:
- **Major**: Infrastructure or backend changes
- **Minor**: Frontend changes
- **Patch**: Documentation or minor updates

### Publishing
- **GitHub Packages**: OCI registry for internal use
- **Google Container Registry**: OCI registry for production
- **Artifacts**: Available for download in CI/CD

## Deployment Commands

### Install New Deployment
```bash
helm install <release-name> ./helm/audit-service-*.tgz \
  --namespace <namespace> \
  --create-namespace \
  -f values/values-<env>.yaml \
  --set image.tag=<commit-sha>
```

### Upgrade Existing Deployment
```bash
helm upgrade <release-name> ./helm/audit-service-*.tgz \
  --namespace <namespace> \
  -f values/values-<env>.yaml \
  --set image.tag=<commit-sha> \
  --wait --timeout=10m
```

### Rollback Deployment
```bash
helm rollback <release-name> <revision> --namespace <namespace>
```

### Uninstall Deployment
```bash
helm uninstall <release-name> --namespace <namespace>
kubectl delete namespace <namespace>
```

## Testing

### Local Testing
```bash
# Run comprehensive chart tests
python3 scripts/test-helm-chart.py

# Test with specific values
helm template test-release ./helm/audit-service \
  --values helm/audit-service/values/values-prod.yaml \
  --namespace audit-service > /tmp/rendered.yaml

# Validate rendered templates
kubectl apply --dry-run=client -f /tmp/rendered.yaml
```

### CI/CD Testing
The CI/CD pipeline includes:
- Chart linting
- Template validation
- Security best practices checks
- Integration testing with deployed services

## Troubleshooting

### Common Issues

1. **Chart Linting Errors**
   ```bash
   helm lint ./helm/audit-service
   ```

2. **Template Validation Errors**
   ```bash
   helm template test-release ./helm/audit-service \
     --values helm/audit-service/values/values-prod.yaml
   ```

3. **Deployment Issues**
   ```bash
   helm status <release-name> --namespace <namespace>
   helm get values <release-name> --namespace <namespace>
   ```

4. **Resource Issues**
   ```bash
   kubectl describe quota -n <namespace>
   kubectl describe limits -n <namespace>
   ```

### Debug Commands

```bash
# Check chart structure
tree helm/audit-service/

# Validate values
helm template test-release ./helm/audit-service \
  --values helm/audit-service/values/values-prod.yaml \
  --debug

# Check deployment status
kubectl get all -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
```

## Benefits

### 🎯 **Improved Deployment Management**
- Versioned releases with rollback capability
- Environment-specific configurations
- Automated deployment pipelines

### 🔧 **Better Configuration**
- Centralized configuration management
- Environment-specific overrides
- Secret management integration

### 📊 **Enhanced Monitoring**
- Built-in metrics endpoints
- Prometheus integration
- Custom alerting rules

### 🔒 **Security Improvements**
- Non-root containers
- Security contexts
- RBAC integration
- Network policies

### 🚀 **Scalability**
- Horizontal Pod Autoscaling
- Resource quotas and limits
- Rolling update strategies

## Migration Checklist

- [ ] Install Helm locally
- [ ] Test chart with local validation script
- [ ] Update CI/CD pipeline configuration
- [ ] Test deployment in development environment
- [ ] Validate all functionality works as expected
- [ ] Update documentation and runbooks
- [ ] Train team on new deployment process
- [ ] Plan production migration
- [ ] Execute production migration
- [ ] Monitor post-migration performance

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the Helm chart README
3. Run the local testing script
4. Check CI/CD logs for detailed error messages
5. Consult the Helm documentation: https://helm.sh/docs/

## Related Documentation

- [Helm Chart README](../helm/audit-service/README.md)
- [CI/CD Pipeline Documentation](./ci-change-analysis.md)
- [Deployment Guide](./deployment/deployment-guide.md)
- [Monitoring Documentation](./monitoring/monitoring.md)
