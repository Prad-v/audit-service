# Audit Service Helm Chart

A comprehensive Helm chart for deploying the Audit Service to Kubernetes clusters.

## Overview

This Helm chart deploys a complete audit logging service with the following components:

- **Backend API**: FastAPI-based REST API for audit event ingestion and retrieval
- **Frontend**: React-based web interface for audit log management
- **Worker**: Background processing for audit event processing
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Security**: RBAC, network policies, and security contexts

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Ingress controller (nginx, istio, etc.)
- Cert-manager (for TLS certificates)
- Prometheus Operator (for monitoring)

## Quick Start

### 1. Add the Helm repository

```bash
helm repo add audit-service https://your-helm-repo.com
helm repo update
```

### 2. Install the chart

```bash
# Development
helm install audit-service-dev audit-service/audit-service \
  --namespace audit-service-dev \
  --create-namespace \
  -f values/values-dev.yaml

# Staging
helm install audit-service-staging audit-service/audit-service \
  --namespace audit-service-staging \
  --create-namespace \
  -f values/values-staging.yaml

# Production
helm install audit-service audit-service/audit-service \
  --namespace audit-service \
  --create-namespace \
  -f values/values-prod.yaml
```

### 3. Configure secrets

Create a secret with your sensitive configuration:

```bash
kubectl create secret generic audit-service-secret \
  --from-literal=DATABASE_URL="your-database-url" \
  --from-literal=JWT_SECRET_KEY="your-jwt-secret" \
  --from-literal=REDIS_URL="your-redis-url" \
  --from-literal=NATS_URL="your-nats-url" \
  --from-file=GOOGLE_CREDENTIALS=path/to/credentials.json
```

## Configuration

### Values Files

The chart includes environment-specific values files:

- `values.yaml` - Default values
- `values/values-dev.yaml` - Development environment
- `values/values-staging.yaml` - Staging environment
- `values/values-prod.yaml` - Production environment

### Key Configuration Options

#### Image Configuration

```yaml
image:
  repository: gcr.io/PROJECT_ID/audit-service
  tag: latest
  pullPolicy: Always
  frontend:
    repository: gcr.io/PROJECT_ID/audit-service-frontend
    tag: latest
```

#### Replica Configuration

```yaml
app:
  replicas:
    backend: 3
    frontend: 2
    worker: 2
```

#### Resource Limits

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

#### Ingress Configuration

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

#### Monitoring Configuration

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    path: /metrics
    port: metrics
```

## Architecture

### Components

1. **Backend Deployment**
   - FastAPI application
   - REST API endpoints
   - Database integration
   - Authentication/Authorization

2. **Frontend Deployment**
   - React application
   - Nginx web server
   - Static file serving
   - API proxy

3. **Worker Deployment**
   - Background processing
   - Event processing
   - Batch operations

4. **Services**
   - Backend service (ClusterIP)
   - Frontend service (ClusterIP)
   - Metrics endpoints

5. **Ingress**
   - SSL termination
   - Path-based routing
   - Rate limiting

6. **HPA (Horizontal Pod Autoscaler)**
   - CPU-based scaling
   - Memory-based scaling
   - Configurable limits

### Security Features

- **Pod Security Contexts**: Non-root containers
- **RBAC**: Role-based access control
- **Network Policies**: Pod-to-pod communication
- **Secrets Management**: Secure credential storage
- **TLS**: End-to-end encryption

## Deployment

### Development

```bash
helm install audit-service-dev audit-service/audit-service \
  --namespace audit-service-dev \
  --create-namespace \
  -f values/values-dev.yaml \
  --set image.tag=dev \
  --set backend.replicas=1 \
  --set frontend.replicas=1
```

### Staging

```bash
helm install audit-service-staging audit-service/audit-service \
  --namespace audit-service-staging \
  --create-namespace \
  -f values/values-staging.yaml \
  --set image.tag=staging
```

### Production

```bash
helm install audit-service audit-service/audit-service \
  --namespace audit-service \
  --create-namespace \
  -f values/values-prod.yaml \
  --set image.tag=latest
```

## Upgrading

```bash
# Upgrade to a new version
helm upgrade audit-service audit-service/audit-service \
  --namespace audit-service \
  -f values/values-prod.yaml \
  --set image.tag=new-version

# Rollback if needed
helm rollback audit-service 1 --namespace audit-service
```

## Uninstalling

```bash
helm uninstall audit-service --namespace audit-service
kubectl delete namespace audit-service
```

## Monitoring

### Metrics

The application exposes Prometheus metrics at `/metrics`:

- HTTP request metrics
- Database connection metrics
- Application-specific metrics
- Custom business metrics

### Alerts

Configured Prometheus rules for:

- High error rates
- Service availability
- Resource utilization
- Custom business alerts

### Dashboards

Grafana dashboards are automatically provisioned for:

- Application performance
- Infrastructure metrics
- Business metrics
- Custom visualizations

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```bash
   kubectl describe pod -n audit-service
   kubectl logs -n audit-service deployment/audit-service-backend
   ```

2. **Database Connection Issues**
   ```bash
   kubectl exec -n audit-service deployment/audit-service-backend -- env | grep DATABASE
   ```

3. **Ingress Issues**
   ```bash
   kubectl describe ingress -n audit-service
   kubectl get events -n audit-service
   ```

### Debug Commands

```bash
# Check pod status
kubectl get pods -n audit-service

# Check service endpoints
kubectl get endpoints -n audit-service

# Check ingress status
kubectl get ingress -n audit-service

# Check HPA status
kubectl get hpa -n audit-service

# View logs
kubectl logs -n audit-service deployment/audit-service-backend
kubectl logs -n audit-service deployment/audit-service-frontend
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with different environments
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
