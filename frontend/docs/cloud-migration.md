# Cloud Migration Guide

This guide provides comprehensive instructions for migrating the Audit Service from local development to Google Cloud Platform (GCP) production deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Service Configuration](#service-configuration)
4. [Deployment Process](#deployment-process)
5. [Migration Verification](#migration-verification)
6. [Rollback Procedures](#rollback-procedures)
7. [Post-Migration Tasks](#post-migration-tasks)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

```bash
# Install required CLI tools
gcloud components install kubectl
gcloud components install terraform
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### GCP Project Setup

```bash
# Set up GCP project
export PROJECT_ID="your-audit-service-project"
export REGION="us-central1"
export ZONE="us-central1-a"

gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
```

### Service Account Setup

```bash
# Create service account for Terraform
gcloud iam service-accounts create terraform-sa \
    --display-name="Terraform Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:terraform-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountAdmin"

# Create and download key
gcloud iam service-accounts keys create terraform-key.json \
    --iam-account=terraform-sa@$PROJECT_ID.iam.gserviceaccount.com

export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform-key.json"
```

## Infrastructure Setup

### 1. Terraform Configuration

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
project_id = "$PROJECT_ID"
region = "$REGION"
zone = "$ZONE"
environment = "production"

# Network configuration
vpc_cidr = "10.0.0.0/16"
subnet_cidr = "10.0.1.0/24"
pod_cidr = "10.1.0.0/16"
service_cidr = "10.2.0.0/16"

# Database configuration
db_instance_tier = "db-custom-2-4096"
db_disk_size = 100
db_backup_enabled = true
db_point_in_time_recovery = true

# Redis configuration
redis_memory_size_gb = 4
redis_tier = "STANDARD_HA"

# GKE configuration
gke_node_count = 3
gke_node_machine_type = "e2-standard-4"
gke_node_disk_size = 100
gke_node_preemptible = false

# BigQuery configuration
bigquery_location = "US"
bigquery_partition_expiration_days = 365
bigquery_clustering_fields = ["tenant_id", "event_type"]

# Monitoring configuration
enable_monitoring = true
enable_logging = true
log_retention_days = 30
EOF

# Plan and apply infrastructure
terraform plan
terraform apply
```

### 2. GKE Cluster Setup

```bash
# Get GKE credentials
gcloud container clusters get-credentials audit-service-cluster \
    --region=$REGION --project=$PROJECT_ID

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### 3. Install Monitoring Stack

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Install Prometheus
helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --set grafana.adminPassword=admin123 \
    --set prometheus.prometheusSpec.retention=30d \
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi

# Install additional monitoring components
kubectl apply -f monitoring/prometheus/
kubectl apply -f monitoring/grafana/
kubectl apply -f monitoring/alertmanager/
```

## Service Configuration

### 1. Update Configuration Files

```bash
# Update Kubernetes manifests with actual values
sed -i "s/PROJECT_ID/$PROJECT_ID/g" k8s/*.yaml
sed -i "s/REGION/$REGION/g" k8s/*.yaml

# Get Terraform outputs
export DB_CONNECTION_NAME=$(terraform output -raw db_connection_name)
export REDIS_HOST=$(terraform output -raw redis_host)
export BIGQUERY_DATASET=$(terraform output -raw bigquery_dataset_id)

# Update secrets with actual values
kubectl create secret generic audit-service-secrets \
    --namespace=audit-service \
    --from-literal=JWT_SECRET_KEY="$(openssl rand -base64 32)" \
    --from-literal=DATABASE_URL="postgresql://audit_user:$(terraform output -raw db_password)@$DB_CONNECTION_NAME/audit_db" \
    --from-literal=GCP_PROJECT_ID="$PROJECT_ID" \
    --from-literal=GCP_REGION="$REGION" \
    --from-literal=REDIS_HOST="$REDIS_HOST" \
    --from-literal=BIGQUERY_DATASET="$BIGQUERY_DATASET" \
    --from-file=GOOGLE_APPLICATION_CREDENTIALS_JSON=service-account-key.json
```

### 2. Build and Push Container Images

```bash
# Build backend image
cd backend
docker build -t gcr.io/$PROJECT_ID/audit-service-backend:latest .

# Push to Google Container Registry
docker push gcr.io/$PROJECT_ID/audit-service-backend:latest

# Build frontend image (if needed)
cd ../frontend
docker build -t gcr.io/$PROJECT_ID/audit-service-frontend:latest .
docker push gcr.io/$PROJECT_ID/audit-service-frontend:latest
```

## Deployment Process

### 1. Deploy Kubernetes Resources

```bash
# Apply Kubernetes manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=300s deployment/audit-service-backend -n audit-service
kubectl wait --for=condition=available --timeout=300s deployment/audit-service-worker -n audit-service
```

### 2. Database Migration

```bash
# Run database migrations
kubectl exec -it deployment/audit-service-backend -n audit-service -- alembic upgrade head

# Verify database schema
kubectl exec -it deployment/audit-service-backend -n audit-service -- python -c "
from app.db.database import get_database
from app.models.audit import AuditLog
import asyncio

async def check_db():
    db = get_database()
    async with db.get_session() as session:
        result = await session.execute('SELECT version();')
        print('Database version:', result.scalar())

asyncio.run(check_db())
"
```

### 3. BigQuery Setup

```bash
# Create BigQuery dataset and table
bq mk --dataset --location=US $PROJECT_ID:audit_logs

bq mk --table \
    --schema='id:STRING,tenant_id:STRING,user_id:STRING,event_type:STRING,resource_type:STRING,resource_id:STRING,action:STRING,timestamp:TIMESTAMP,ip_address:STRING,user_agent:STRING,metadata:JSON,created_at:TIMESTAMP' \
    --time_partitioning_field=timestamp \
    --time_partitioning_type=DAY \
    --clustering_fields=tenant_id,event_type \
    $PROJECT_ID:audit_logs.audit_events
```

### 4. Pub/Sub Setup

```bash
# Create Pub/Sub topic and subscription
gcloud pubsub topics create audit-events
gcloud pubsub subscriptions create audit-processor \
    --topic=audit-events \
    --ack-deadline=60 \
    --message-retention-duration=7d
```

## Migration Verification

### 1. Health Checks

```bash
# Check pod status
kubectl get pods -n audit-service

# Check service endpoints
kubectl get svc -n audit-service

# Test health endpoint
kubectl port-forward svc/audit-service-backend 8080:80 -n audit-service &
curl http://localhost:8080/health

# Test API endpoints
curl -H "Authorization: Bearer <token>" http://localhost:8080/api/v1/audit/logs
```

### 2. Performance Testing

```bash
# Run load tests
cd tests/load
pip install locust
locust -f locustfile.py --host=https://api.audit-service.example.com

# Monitor metrics
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring &
# Open http://localhost:9090 in browser

kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring &
# Open http://localhost:3000 in browser (admin/admin123)
```

### 3. Data Validation

```bash
# Test BigQuery integration
kubectl exec -it deployment/audit-service-backend -n audit-service -- python -c "
from app.services.bigquery_service import get_bigquery_service
import asyncio

async def test_bigquery():
    service = get_bigquery_service()
    status = service.get_status()
    print('BigQuery status:', status)
    
    # Test data insertion
    test_data = {
        'tenant_id': 'test-tenant',
        'user_id': 'test-user',
        'event_type': 'test_event',
        'resource_type': 'test_resource',
        'resource_id': 'test-123',
        'action': 'create',
        'metadata': {'test': True}
    }
    
    result = await service.create_audit_log(test_data)
    print('Test insertion result:', result)

asyncio.run(test_bigquery())
"

# Verify data in BigQuery
bq query --use_legacy_sql=false "
SELECT COUNT(*) as total_events, 
       MIN(timestamp) as earliest_event,
       MAX(timestamp) as latest_event
FROM \`$PROJECT_ID.audit_logs.audit_events\`
WHERE DATE(timestamp) = CURRENT_DATE()
"
```

## Rollback Procedures

### 1. Application Rollback

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/audit-service-backend -n audit-service
kubectl rollout undo deployment/audit-service-worker -n audit-service

# Check rollback status
kubectl rollout status deployment/audit-service-backend -n audit-service
kubectl rollout status deployment/audit-service-worker -n audit-service
```

### 2. Database Rollback

```bash
# Rollback database migrations
kubectl exec -it deployment/audit-service-backend -n audit-service -- alembic downgrade -1

# Verify database state
kubectl exec -it deployment/audit-service-backend -n audit-service -- alembic current
```

### 3. Infrastructure Rollback

```bash
# Rollback Terraform changes
cd terraform
terraform plan -destroy
terraform apply -destroy  # Only if complete rollback is needed
```

## Post-Migration Tasks

### 1. DNS Configuration

```bash
# Get ingress IP
kubectl get ingress audit-service-ingress -n audit-service

# Update DNS records to point to the ingress IP
# api.audit-service.example.com -> <INGRESS_IP>
```

### 2. SSL Certificate

```bash
# Verify managed certificate status
kubectl describe managedcertificate audit-service-ssl-cert -n audit-service

# Check certificate provisioning
gcloud compute ssl-certificates list
```

### 3. Monitoring Setup

```bash
# Import Grafana dashboards
kubectl apply -f monitoring/grafana/dashboards/

# Configure alerting rules
kubectl apply -f monitoring/prometheus/alerts.yml

# Test alerting
kubectl scale deployment audit-service-backend --replicas=0 -n audit-service
# Wait for alerts to fire, then scale back up
kubectl scale deployment audit-service-backend --replicas=3 -n audit-service
```

### 4. Backup Configuration

```bash
# Set up automated backups
gcloud sql backups create --instance=audit-service-db

# Configure backup retention
gcloud sql instances patch audit-service-db \
    --backup-start-time=02:00 \
    --retained-backups-count=30
```

## Troubleshooting

### Common Issues

#### 1. Pod Startup Issues

```bash
# Check pod logs
kubectl logs -f deployment/audit-service-backend -n audit-service

# Check pod events
kubectl describe pod <pod-name> -n audit-service

# Check resource constraints
kubectl top pods -n audit-service
```

#### 2. Database Connection Issues

```bash
# Test database connectivity
kubectl exec -it deployment/audit-service-backend -n audit-service -- \
    python -c "
import asyncpg
import asyncio

async def test_db():
    try:
        conn = await asyncpg.connect('$DATABASE_URL')
        result = await conn.fetchval('SELECT version()')
        print('Database connected:', result)
        await conn.close()
    except Exception as e:
        print('Database error:', e)

asyncio.run(test_db())
"
```

#### 3. BigQuery Issues

```bash
# Check BigQuery permissions
gcloud projects get-iam-policy $PROJECT_ID

# Test BigQuery connectivity
kubectl exec -it deployment/audit-service-backend -n audit-service -- \
    python -c "
from google.cloud import bigquery
client = bigquery.Client()
datasets = list(client.list_datasets())
print('Available datasets:', [d.dataset_id for d in datasets])
"
```

#### 4. Pub/Sub Issues

```bash
# Check Pub/Sub topics and subscriptions
gcloud pubsub topics list
gcloud pubsub subscriptions list

# Test message publishing
gcloud pubsub topics publish audit-events --message='{"test": "message"}'

# Check subscription backlog
gcloud pubsub subscriptions describe audit-processor
```

### Performance Optimization

#### 1. Resource Tuning

```bash
# Monitor resource usage
kubectl top pods -n audit-service
kubectl top nodes

# Adjust resource requests/limits
kubectl patch deployment audit-service-backend -n audit-service -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "backend",
            "resources": {
              "requests": {"cpu": "500m", "memory": "512Mi"},
              "limits": {"cpu": "2000m", "memory": "2Gi"}
            }
          }
        ]
      }
    }
  }
}'
```

#### 2. Scaling Configuration

```bash
# Adjust HPA settings
kubectl patch hpa audit-service-backend-hpa -n audit-service -p '
{
  "spec": {
    "maxReplicas": 50,
    "metrics": [
      {
        "type": "Resource",
        "resource": {
          "name": "cpu",
          "target": {
            "type": "Utilization",
            "averageUtilization": 60
          }
        }
      }
    ]
  }
}'
```

### Monitoring and Alerting

#### 1. Key Metrics to Monitor

- **Application Metrics**:
  - Request rate and latency
  - Error rate
  - Database connection pool usage
  - Cache hit rate

- **Infrastructure Metrics**:
  - CPU and memory usage
  - Disk I/O and network traffic
  - Pod restart count
  - Node resource utilization

- **Business Metrics**:
  - Audit log ingestion rate
  - Data processing latency
  - Storage usage growth
  - API usage by tenant

#### 2. Alert Configuration

```yaml
# Example alert rules
groups:
- name: audit-service
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      
  - alert: DatabaseConnectionPoolExhausted
    expr: db_connection_pool_active / db_connection_pool_max > 0.9
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: Database connection pool nearly exhausted
```

This migration guide provides a comprehensive approach to moving from local development to GCP production deployment, ensuring reliability, scalability, and maintainability of the audit service.