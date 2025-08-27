# Project Structure

```
audit-log-framework/
├── README.md
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── PROJECT_STRUCTURE.md
│
├── backend/                          # Python FastAPI Backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry point
│   │   ├── config.py                 # Configuration management
│   │   ├── dependencies.py           # Dependency injection
│   │   │
│   │   ├── api/                      # API routes
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── audit.py          # Audit log endpoints
│   │   │   │   ├── auth.py           # Authentication endpoints
│   │   │   │   └── health.py         # Health check endpoints
│   │   │   └── middleware.py         # Custom middleware
│   │   │
│   │   ├── core/                     # Core business logic
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Authentication logic
│   │   │   ├── security.py           # Security utilities
│   │   │   ├── permissions.py        # RBAC implementation
│   │   │   └── exceptions.py         # Custom exceptions
│   │   │
│   │   ├── models/                   # Data models
│   │   │   ├── __init__.py
│   │   │   ├── audit.py              # Audit log models
│   │   │   ├── auth.py               # Authentication models
│   │   │   └── base.py               # Base model classes
│   │   │
│   │   ├── services/                 # Business services
│   │   │   ├── __init__.py
│   │   │   ├── audit_service.py      # Audit log service
│   │   │   ├── bigquery_service.py   # BigQuery operations
│   │   │   ├── cache_service.py      # Redis cache service
│   │   │   ├── pubsub_service.py     # Pub/Sub operations
│   │   │   └── retention_service.py  # Data retention service
│   │   │
│   │   ├── db/                       # Database operations
│   │   │   ├── __init__.py
│   │   │   ├── bigquery.py           # BigQuery client
│   │   │   ├── schemas.py            # BigQuery schemas
│   │   │   └── migrations/           # Schema migrations
│   │   │       ├── __init__.py
│   │   │       └── 001_initial.py
│   │   │
│   │   └── utils/                    # Utility functions
│   │       ├── __init__.py
│   │       ├── logging.py            # Logging configuration
│   │       ├── metrics.py            # Prometheus metrics
│   │       └── validators.py         # Data validation
│   │
│   ├── tests/                        # Test suite
│   │   ├── __init__.py
│   │   ├── conftest.py               # Test configuration
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_utils/
│   │
│   └── scripts/                      # Utility scripts
│       ├── setup_bigquery.py         # BigQuery setup
│       ├── load_test_data.py         # Test data loader
│       └── migrate.py                # Migration runner
│
├── frontend/                         # Backstage Frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── yarn.lock
│   ├── app-config.yaml               # Backstage configuration
│   ├── catalog-info.yaml             # Service catalog
│   │
│   ├── packages/
│   │   └── app/                      # Main Backstage app
│   │       ├── package.json
│   │       ├── src/
│   │       │   ├── App.tsx
│   │       │   ├── index.tsx
│   │       │   └── components/
│   │       │       ├── AuditLogViewer/
│   │       │       ├── AuditLogSearch/
│   │       │       ├── AuditLogExport/
│   │       │       └── Dashboard/
│   │       └── public/
│   │
│   └── plugins/                      # Custom Backstage plugins
│       └── audit-log/
│           ├── package.json
│           ├── src/
│           │   ├── index.ts
│           │   ├── plugin.ts
│           │   ├── components/
│           │   ├── api/
│           │   └── routes.ts
│           └── dev/
│
├── sdks/                             # Client SDKs
│   ├── python/                       # Python SDK
│   │   ├── setup.py
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── audit_log_client/
│   │   │   ├── __init__.py
│   │   │   ├── client.py             # Main client class
│   │   │   ├── models.py             # Data models
│   │   │   ├── exceptions.py         # SDK exceptions
│   │   │   └── utils.py              # Utility functions
│   │   ├── tests/
│   │   └── examples/
│   │       ├── basic_usage.py
│   │       ├── batch_operations.py
│   │       └── async_operations.py
│   │
│   └── go/                           # Go SDK
│       ├── go.mod
│       ├── go.sum
│       ├── README.md
│       ├── client.go                 # Main client
│       ├── models.go                 # Data models
│       ├── errors.go                 # Error handling
│       ├── auth.go                   # Authentication
│       ├── examples/
│       │   ├── basic/main.go
│       │   ├── batch/main.go
│       │   └── advanced/main.go
│       └── tests/
│           ├── client_test.go
│           └── integration_test.go
│
├── tools/                            # Development tools
│   ├── sdk-generator/                # SDK generation scripts
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── generate.py               # Main generator script
│   │   ├── templates/
│   │   │   ├── python/
│   │   │   └── go/
│   │   └── config/
│   │       ├── python-config.yaml
│   │       └── go-config.yaml
│   │
│   └── load-testing/                 # Load testing tools
│       ├── locustfile.py
│       ├── k6-script.js
│       └── requirements.txt
│
├── deployment/                       # Deployment configurations
│   ├── kubernetes/                   # K8s manifests
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   ├── backend/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── ingress.yaml
│   │   ├── frontend/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── ingress.yaml
│   │   ├── redis/
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   └── monitoring/
│   │       ├── prometheus.yaml
│   │       ├── grafana.yaml
│   │       └── alertmanager.yaml
│   │
│   ├── terraform/                    # Infrastructure as Code
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── modules/
│   │   │   ├── bigquery/
│   │   │   ├── gke/
│   │   │   ├── pubsub/
│   │   │   └── monitoring/
│   │   └── environments/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   │
│   ├── helm/                         # Helm charts
│   │   ├── audit-log-framework/
│   │   │   ├── Chart.yaml
│   │   │   ├── values.yaml
│   │   │   ├── values-dev.yaml
│   │   │   ├── values-staging.yaml
│   │   │   ├── values-prod.yaml
│   │   │   └── templates/
│   │   └── dependencies/
│   │
│   └── docker/                       # Docker configurations
│       ├── backend.Dockerfile
│       ├── frontend.Dockerfile
│       ├── sdk-generator.Dockerfile
│       └── nginx.conf
│
├── docs/                             # Documentation
│   ├── api/                          # API documentation
│   │   ├── openapi.yaml              # OpenAPI specification
│   │   ├── swagger-ui/               # Swagger UI assets
│   │   └── postman/                  # Postman collections
│   │
│   ├── sdk/                          # SDK documentation
│   │   ├── python.md
│   │   ├── go.md
│   │   └── examples/
│   │
│   ├── deployment/                   # Deployment guides
│   │   ├── local-development.md
│   │   ├── kubernetes.md
│   │   ├── gcp-setup.md
│   │   └── monitoring.md
│   │
│   └── architecture/                 # Architecture documentation
│       ├── system-design.md
│       ├── data-model.md
│       ├── security.md
│       └── performance.md
│
├── monitoring/                       # Monitoring configurations
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   ├── rules/
│   │   └── alerts/
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── api-metrics.json
│   │   │   ├── bigquery-metrics.json
│   │   │   └── system-overview.json
│   │   └── provisioning/
│   └── alertmanager/
│       └── alertmanager.yml
│
├── scripts/                          # Automation scripts
│   ├── setup-dev-env.sh              # Development environment setup
│   ├── build-all.sh                  # Build all components
│   ├── deploy.sh                     # Deployment script
│   ├── test-all.sh                   # Run all tests
│   └── cleanup.sh                    # Cleanup resources
│
└── .github/                          # GitHub workflows
    └── workflows/
        ├── ci.yml                    # Continuous Integration
        ├── cd.yml                    # Continuous Deployment
        ├── security-scan.yml         # Security scanning
        └── sdk-release.yml           # SDK release automation
```

## Key Design Decisions

### Backend Architecture
- **FastAPI**: High-performance async Python framework
- **Modular Structure**: Clear separation of concerns
- **Dependency Injection**: Easy testing and configuration
- **Async/Await**: Non-blocking I/O for high throughput

### Frontend Architecture
- **Backstage.io**: Enterprise-grade developer portal
- **Plugin Architecture**: Modular and extensible
- **Material-UI + Tailwind**: Consistent design system
- **TypeScript**: Type safety and better developer experience

### SDK Architecture
- **Language-Specific**: Native patterns for each language
- **Auto-Generated**: Consistent with OpenAPI specification
- **Async Support**: Non-blocking operations where applicable
- **Comprehensive Examples**: Easy adoption and integration

### Infrastructure Architecture
- **Container-First**: Docker for consistent environments
- **Kubernetes-Native**: Cloud-native deployment patterns
- **Infrastructure as Code**: Terraform for reproducible infrastructure
- **GitOps**: Version-controlled deployment configurations

### Development Workflow
- **Monorepo**: Single repository for all components
- **Make-based**: Simple command interface
- **Docker Compose**: Local development environment
- **Automated Testing**: Comprehensive test coverage
- **CI/CD Pipeline**: Automated build, test, and deployment