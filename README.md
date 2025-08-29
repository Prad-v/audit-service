# Audit Log Framework

A comprehensive audit logging system built with FastAPI backend and React frontend, designed for tracking and monitoring application events.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Using Docker (Recommended)

1. **Start the entire stack:**
   ```bash
   ./scripts/start.sh start
   ```

2. **Start in development mode (with hot reload):**
   ```bash
   ./scripts/start.sh dev
   ```

3. **View logs:**
   ```bash
   ./scripts/start.sh logs
   ```

4. **Stop services:**
   ```bash
   ./scripts/start.sh stop
   ```

### Manual Docker Commands

**Production mode:**
```bash
docker-compose up --build -d
```

**Development mode:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

## 📋 Service URLs

Once started, the following services will be available:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| API | http://localhost:8000 | FastAPI backend |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Health Check | http://localhost:8000/health | Service health status |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |
| NATS | localhost:4222 | Message broker |

## 🏗️ Architecture

### Frontend (React + Vite)
- **Technology**: React 18, TypeScript, Vite, Tailwind CSS
- **Features**: 
  - Dashboard with statistics
  - Audit log browsing and filtering
  - Event creation and management
  - Responsive design
  - Real-time updates with React Query

### Backend (FastAPI)
- **Technology**: FastAPI, SQLAlchemy, PostgreSQL, Redis, NATS
- **Features**:
  - RESTful API for audit events
  - Batch event processing
  - Advanced filtering and pagination
  - RBAC authentication/authorization (can be disabled)
  - Health monitoring
  - Comprehensive logging

### Infrastructure
- **Database**: PostgreSQL 15 with partitioning
- **Cache**: Redis 7
- **Message Broker**: NATS with JetStream
- **Container Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx (production)

## 🛠️ Development

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd audit-service
   ```

2. **Start in development mode:**
   ```bash
   ./scripts/start.sh dev
   ```

3. **Frontend development:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Backend development:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Environment Variables

#### Frontend
- `VITE_API_URL`: Backend API URL (default: http://localhost:8000)

#### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `NATS_URL`: NATS connection string
- `DEBUG`: Enable debug mode (true/false)
- `RBAC_AUTHENTICATION_DISABLED`: Disable RBAC authentication (true/false)
- `RBAC_AUTHORIZATION_DISABLED`: Disable RBAC authorization (true/false)

## 📊 API Endpoints

### Audit Events
- `GET /api/v1/audit/events` - List audit events with filtering
- `GET /api/v1/audit/events/{id}` - Get specific audit event
- `POST /api/v1/audit/events` - Create single audit event
- `POST /api/v1/audit/events/batch` - Create multiple audit events

### Health & Monitoring
- `GET /api/v1/audit/health` - Service health check
- `GET /health` - Basic health endpoint

## 🔧 Configuration

### Docker Compose Files

- `docker-compose.yml` - Main production configuration
- `docker-compose.dev.yml` - Development overrides (hot reload, volumes)

### Frontend Configuration

- `frontend/vite.config.ts` - Vite build configuration
- `frontend/tailwind.config.js` - Tailwind CSS configuration
- `frontend/nginx.conf` - Nginx production configuration

### Backend Configuration

- `backend/app/config.py` - Application settings
- `backend/Dockerfile` - Backend container configuration

## 🧪 Testing

### Quick Start
```bash
# Run all tests
python3 run_tests.py

# Run specific test types
python3 run_tests.py --unit
python3 run_tests.py --integration
python3 run_tests.py --e2e
python3 run_tests.py --manual

# Advanced options
python3 run_tests.py --continue-on-fail
python3 run_tests.py --verbose
python3 run_tests.py --ci
```

### Test Categories
- **Unit Tests**: Individual functions and classes
- **Integration Tests**: API endpoints and service interactions
- **E2E Tests**: Complete user workflows
- **Manual Scripts**: Debugging and performance testing

### Individual Test Types
```bash
# Frontend tests
cd frontend && npm run test

# Backend tests
cd backend && pytest

# Integration tests (requires services running)
./scripts/start.sh start
python3 run_tests.py --integration
```

### CI/CD Integration
The test suite is integrated with GitHub Actions and runs automatically on:
- Push to main/develop branches
- Pull requests
- Manual triggering with custom parameters

For detailed testing information, see [tests/README.md](tests/README.md).

## 📦 Deployment

### Docker Compose (Local/Development)

#### Production Build
```bash
# Build production images
docker-compose build

# Start production services
docker-compose up -d
```

#### Docker Images
- Frontend: Nginx serving built React app
- Backend: Python FastAPI application
- Database: PostgreSQL with audit log partitioning
- Cache: Redis for session and data caching
- Message Broker: NATS for event streaming

### Helm Chart (Production/Kubernetes)

The Audit Service includes a comprehensive Helm chart for Kubernetes deployment with automated CI/CD integration.

#### Quick Start with Helm

```bash
# Test the chart locally
python3 scripts/test-helm-chart.py

# Install in development
helm install audit-service-dev ./helm/audit-service \
  --namespace audit-service-dev \
  --create-namespace \
  -f helm/audit-service/values/values-dev.yaml

# Install in staging
helm install audit-service-staging ./helm/audit-service \
  --namespace audit-service-staging \
  --create-namespace \
  -f helm/audit-service/values/values-staging.yaml

# Install in production
helm install audit-service ./helm/audit-service \
  --namespace audit-service \
  --create-namespace \
  -f helm/audit-service/values/values-prod.yaml
```

#### Helm Chart Features

- **🔧 Configuration Management**: Centralized configuration with environment-specific overrides
- **🚀 Deployment Features**: Rolling updates, health checks, resource quotas
- **🔒 Security**: Non-root containers, RBAC, security contexts
- **📊 Monitoring**: Prometheus metrics, Grafana dashboards, custom alerts
- **🔄 CI/CD Integration**: Automated packaging, versioning, and publishing

#### Chart Structure
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

#### Key Configuration Options

##### Image Configuration
```yaml
image:
  repository: gcr.io/PROJECT_ID/audit-service
  tag: latest
  pullPolicy: Always
  frontend:
    repository: gcr.io/PROJECT_ID/audit-service-frontend
    tag: latest
```

##### Replica Configuration
```yaml
app:
  replicas:
    backend: 3
    frontend: 2
    worker: 2
```

##### Resource Limits
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

##### Ingress Configuration
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

#### CI/CD Integration

The Helm chart is automatically packaged and published through the CI/CD pipeline:

- **Automated Packaging**: Every commit triggers chart packaging
- **Intelligent Versioning**: Version bumps based on change types
- **OCI Publishing**: Charts published to GitHub Packages and Google Container Registry
- **Helm Deployments**: Automated deployments to staging and production

#### Environment-Specific Values

##### Development (`values-dev.yaml`)
- Single replica deployments
- Debug logging enabled
- Resource limits relaxed
- Monitoring disabled
- No ingress (port-forward access)

##### Staging (`values-staging.yaml`)
- 2 replicas per service
- Production-like configuration
- Monitoring enabled
- Ingress with staging hostname
- Resource quotas enabled

##### Production (`values-prod.yaml`)
- 3+ replicas per service
- Full production configuration
- Comprehensive monitoring
- Production ingress with SSL
- Strict resource quotas

#### Deployment Commands

##### Install New Deployment
```bash
helm install <release-name> ./helm/audit-service-*.tgz \
  --namespace <namespace> \
  --create-namespace \
  -f values/values-<env>.yaml \
  --set image.tag=<commit-sha>
```

##### Upgrade Existing Deployment
```bash
helm upgrade <release-name> ./helm/audit-service-*.tgz \
  --namespace <namespace> \
  -f values/values-<env>.yaml \
  --set image.tag=<commit-sha> \
  --wait --timeout=10m
```

##### Rollback Deployment
```bash
helm rollback <release-name> <revision> --namespace <namespace>
```

##### Uninstall Deployment
```bash
helm uninstall <release-name> --namespace <namespace>
kubectl delete namespace <namespace>
```

#### Monitoring & Observability

##### Prometheus Metrics
- HTTP request metrics
- Database connection metrics
- Application-specific metrics
- Custom business metrics

##### Grafana Dashboards
- Application performance dashboards
- Infrastructure metrics
- Business metrics
- Custom visualizations

##### Alerts
- High error rates
- Service availability
- Resource utilization
- Custom business alerts

For detailed Helm chart documentation, see [helm/audit-service/README.md](helm/audit-service/README.md) and [docs/helm-chart-migration.md](docs/helm-chart-migration.md).

## 🔍 Monitoring

### Health Checks
All services include health checks:
- API: HTTP health endpoint
- Frontend: Nginx health endpoint
- Database: PostgreSQL connection check
- Redis: Ping command
- NATS: HTTP health endpoint

### Logging
- Structured logging with correlation IDs
- Log aggregation via Docker Compose
- Separate log volumes for persistence

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts:**
   ```bash
   # Check what's using the ports
   lsof -i :3000
   lsof -i :8000
   ```

2. **Database connection issues:**
   ```bash
   # Check database logs
   docker-compose logs postgres
   ```

3. **Frontend not loading:**
   ```bash
   # Check frontend logs
   docker-compose logs frontend
   ```

4. **API not responding:**
   ```bash
   # Check API logs
   docker-compose logs api
   ```

### Reset Everything
```bash
# Stop and clean everything
./scripts/start.sh clean

# Start fresh
./scripts/start.sh start
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation at http://localhost:8000/docs