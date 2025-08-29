# Developer Onboarding Guide

Welcome to the Audit Log Framework development team! This guide will help you get up and running quickly with our high-performance, multi-tenant audit logging system.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Environment Setup](#development-environment-setup)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Testing Guidelines](#testing-guidelines)
7. [Debugging and Troubleshooting](#debugging-and-troubleshooting)
8. [Contributing Guidelines](#contributing-guidelines)
9. [Resources and References](#resources-and-references)

## Project Overview

### What We're Building

The Audit Log Framework is a production-ready, high-performance audit logging system designed to handle 1M+ transactions per day with the following key features:

- **Multi-tenant Architecture**: Complete tenant isolation with RBAC
- **High Performance**: Async processing, caching, and optimized database operations
- **Scalable**: Horizontal scaling with load balancing and message queuing
- **Observable**: Comprehensive monitoring, logging, and alerting
- **Secure**: JWT authentication, API keys, and security hardening
- **Cloud-Ready**: Local development with GCP migration path

### Technology Stack

#### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **Python 3.11+**: Latest Python with async/await support
- **SQLAlchemy**: ORM with async support and connection pooling
- **PostgreSQL**: Primary database (local) → BigQuery (production)
- **Redis**: Caching and session storage
- **NATS**: Message streaming and async processing
- **Prometheus**: Metrics collection and monitoring

#### Frontend
- **Backstage.io**: Developer portal and service catalog
- **React**: Component-based UI framework
- **TypeScript**: Type-safe JavaScript development
- **Material-UI**: Component library for consistent design

#### Infrastructure
- **Docker**: Containerization for all services
- **Docker Compose**: Local development orchestration
- **Grafana**: Monitoring dashboards and visualization
- **AlertManager**: Alert routing and notifications

### Key Metrics and Goals

- **Performance**: < 100ms API response time (95th percentile)
- **Throughput**: 1M+ audit events per day
- **Availability**: 99.9% uptime
- **Scalability**: Horizontal scaling to handle growth
- **Security**: Zero security incidents, complete audit trail

## Development Environment Setup

### Prerequisites

Before you begin, ensure you have the following installed:

#### Required Software
```bash
# Check versions
docker --version          # 20.10+
docker-compose --version  # 2.0+
python --version          # 3.11+
node --version            # 18+
git --version             # 2.30+
```

#### Development Tools
```bash
# Python development
pip install poetry        # Dependency management
pip install pre-commit    # Git hooks

# Code quality tools
pip install black         # Code formatting
pip install isort         # Import sorting
pip install flake8       # Linting
pip install mypy          # Type checking

# Database tools
pip install pgcli         # PostgreSQL CLI
```

### Quick Start (5 Minutes)

1. **Clone the Repository**
```bash
git clone <repository-url>
cd audit-service
```

2. **Set Up Environment**
```bash
# Copy environment template
cp .env.example .env

# Install pre-commit hooks
pre-commit install
```

3. **Start Development Environment**
```bash
# Start all services
./scripts/deploy.sh development

# Verify installation
curl http://localhost:8000/health
```

4. **Access Services**
- **API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090

### Detailed Setup

#### 1. Python Environment
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
cd backend
poetry install

# Install development dependencies
poetry install --with dev
```

#### 2. Database Setup
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
cd backend
python -m alembic upgrade head

# Create test data (optional)
python -m app.scripts.seed_data
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

#### 4. IDE Configuration

**VS Code Settings** (`.vscode/settings.json`)
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

**PyCharm Configuration**
- Set Python interpreter to `./venv/bin/python`
- Enable Black formatter
- Configure isort with Black profile
- Set up run configurations for FastAPI

## Architecture Deep Dive

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │───▶│   API Gateway   │───▶│   FastAPI App   │
│   (nginx/ALB)   │    │  (Rate Limit)   │    │  (Multi-tenant) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Message Queue │◀───│   Background    │───▶│   Database      │
│   (NATS/Pub/Sub)│    │   Workers       │    │ (PostgreSQL/BQ) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Monitoring    │    │   Cache Layer   │    │   Frontend      │
│ (Prometheus/    │    │   (Redis)       │    │ (Backstage.io)  │
│  Grafana)       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Code Organization

```
audit-service/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core functionality (auth, config)
│   │   ├── db/             # Database models and migrations
│   │   ├── services/       # Business logic services
│   │   ├── utils/          # Utility functions
│   │   └── worker/         # Background workers
│   ├── tests/              # Test suites
│   └── alembic/            # Database migrations
├── frontend/               # Backstage.io application
│   ├── packages/
│   │   └── audit-plugin/   # Custom audit log plugin
│   └── app-config.yaml     # Backstage configuration
├── monitoring/             # Monitoring configuration
│   ├── grafana/           # Dashboards and provisioning
│   └── prometheus/        # Metrics and alerts
├── scripts/               # Deployment and utility scripts
└── docs/                  # Documentation
```

### Key Components

#### 1. API Layer (`backend/app/api/`)
- **Authentication**: JWT and API key validation
- **Rate Limiting**: Per-tenant and global limits
- **Validation**: Request/response validation with Pydantic
- **Error Handling**: Structured error responses
- **Middleware**: Logging, metrics, tenant isolation

#### 2. Service Layer (`backend/app/services/`)
- **AuditService**: Core audit log operations
- **AuthService**: User and tenant management
- **CacheService**: Redis caching operations
- **NATSService**: Message queue operations

#### 3. Database Layer (`backend/app/db/`)
- **Models**: SQLAlchemy ORM models
- **Schemas**: Pydantic schemas for validation
- **Migrations**: Alembic database migrations
- **Managers**: Database connection and session management

#### 4. Worker Layer (`backend/app/worker/`)
- **BatchProcessor**: High-throughput batch processing
- **EventProcessor**: Real-time event processing
- **MaintenanceWorker**: Cleanup and maintenance tasks

## Development Workflow

### Daily Development Process

1. **Start Your Day**
```bash
# Pull latest changes
git pull origin main

# Start development environment
./scripts/deploy.sh development

# Check service health
curl http://localhost:8000/health
```

2. **Feature Development**
```bash
# Create feature branch
git checkout -b feature/audit-log-filtering

# Make changes
# ... code changes ...

# Run tests
make test

# Run code quality checks
make lint
make type-check
```

3. **Testing Your Changes**
```bash
# Unit tests
pytest backend/tests/unit/

# Integration tests
pytest backend/tests/integration/

# Load testing (if needed)
python tests/load/run_load_tests.py

# Manual testing
curl -X POST http://localhost:8000/api/v1/audit/logs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"event_type": "user_login", "user_id": "test-user"}'
```

4. **Code Review Process**
```bash
# Commit changes
git add .
git commit -m "feat: add audit log filtering by date range"

# Push branch
git push origin feature/audit-log-filtering

# Create pull request
# Use GitHub/GitLab interface
```

### Branch Strategy

We use **Git Flow** with the following branches:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Feature development branches
- **hotfix/***: Critical bug fixes
- **release/***: Release preparation branches

### Commit Message Format

We follow **Conventional Commits**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(api): add audit log filtering by date range
fix(auth): resolve JWT token expiration issue
docs(readme): update installation instructions
test(audit): add unit tests for batch processing
```

## Code Standards

### Python Code Style

We follow **PEP 8** with some modifications:

#### Formatting
```python
# Use Black formatter (line length: 88)
# Use isort for import sorting

# Good
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.database import get_session
from app.services.audit_service import AuditService

logger = structlog.get_logger(__name__)
```

#### Type Hints
```python
# Always use type hints
from typing import List, Optional, Dict, Any

async def create_audit_log(
    audit_data: AuditLogCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> AuditLogResponse:
    """Create a new audit log entry."""
    pass
```

#### Error Handling
```python
# Use structured error handling
from app.core.exceptions import AuditLogException

try:
    result = await audit_service.create_log(audit_data)
except ValueError as e:
    logger.error("Invalid audit data", error=str(e))
    raise HTTPException(status_code=400, detail="Invalid audit data")
except Exception as e:
    logger.error("Unexpected error", error=str(e))
    raise AuditLogException("Failed to create audit log")
```

#### Logging
```python
# Use structured logging
import structlog

logger = structlog.get_logger(__name__)

# Good
logger.info(
    "Audit log created",
    tenant_id=tenant_id,
    user_id=user_id,
    event_type=event_type,
    correlation_id=correlation_id
)

# Bad
logger.info(f"Audit log created for {user_id}")
```

### API Design Standards

#### RESTful Endpoints
```python
# Follow REST conventions
GET    /api/v1/audit/logs           # List audit logs
POST   /api/v1/audit/logs           # Create audit log
GET    /api/v1/audit/logs/{id}      # Get specific audit log
PUT    /api/v1/audit/logs/{id}      # Update audit log
DELETE /api/v1/audit/logs/{id}      # Delete audit log

# Batch operations
POST   /api/v1/audit/logs/batch     # Create multiple logs
```

#### Request/Response Format
```python
# Use Pydantic models for validation
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AuditLogCreate(BaseModel):
    event_type: str = Field(..., description="Type of event")
    user_id: Optional[str] = Field(None, description="User ID")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional data")

class AuditLogResponse(BaseModel):
    id: str
    tenant_id: str
    event_type: str
    user_id: Optional[str]
    resource_id: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True
```

#### Error Responses
```python
# Consistent error format
{
    "error": "validation_error",
    "message": "Invalid request data",
    "details": {
        "field": "event_type",
        "issue": "This field is required"
    },
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Database Standards

#### Model Definition
```python
# Use SQLAlchemy with async support
from sqlalchemy import Column, String, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_audit_logs_tenant_created', 'tenant_id', 'created_at'),
        Index('idx_audit_logs_tenant_event_created', 'tenant_id', 'event_type', 'created_at'),
    )
```

#### Migration Standards
```python
# Use descriptive migration names
# alembic revision --autogenerate -m "add_audit_log_metadata_index"

# Include both upgrade and downgrade
def upgrade() -> None:
    op.create_index(
        'idx_audit_logs_metadata_gin',
        'audit_logs',
        ['metadata'],
        postgresql_using='gin'
    )

def downgrade() -> None:
    op.drop_index('idx_audit_logs_metadata_gin', table_name='audit_logs')
```

## Testing Guidelines

### Test Structure

```
backend/tests/
├── unit/                   # Unit tests
│   ├── test_auth_service.py
│   ├── test_audit_service.py
│   └── test_utils.py
├── integration/            # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_messaging.py
├── load/                   # Load tests
│   ├── locustfile.py
│   └── run_load_tests.py
└── conftest.py            # Test configuration
```

### Unit Testing

```python
# Use pytest with async support
import pytest
from unittest.mock import AsyncMock, patch
from app.services.audit_service import AuditService

@pytest.mark.asyncio
async def test_create_audit_log_success():
    """Test successful audit log creation."""
    # Arrange
    mock_session = AsyncMock()
    audit_service = AuditService(mock_session)
    audit_data = AuditLogCreate(
        event_type="user_login",
        user_id="test-user"
    )
    
    # Act
    result = await audit_service.create_log(audit_data, tenant_id="test-tenant")
    
    # Assert
    assert result.event_type == "user_login"
    assert result.user_id == "test-user"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
```

### Integration Testing

```python
# Test API endpoints
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_audit_log_endpoint():
    """Test audit log creation endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/audit/logs",
            json={
                "event_type": "user_login",
                "user_id": "test-user"
            },
            headers={"Authorization": "Bearer test-token"}
        )
    
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "user_login"
```

### Load Testing

```python
# Use Locust for load testing
from locust import HttpUser, task, between

class AuditLogUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login and get token."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def create_audit_log(self):
        """Create audit log."""
        self.client.post(
            "/api/v1/audit/logs",
            json={
                "event_type": "user_action",
                "user_id": f"user-{self.user_id}"
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def list_audit_logs(self):
        """List audit logs."""
        self.client.get(
            "/api/v1/audit/logs",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

### Test Data Management

```python
# Use factories for test data
import factory
from app.db.schemas import User, Tenant

class TenantFactory(factory.Factory):
    class Meta:
        model = Tenant
    
    id = factory.Faker('uuid4')
    name = factory.Faker('company')
    is_active = True

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    id = factory.Faker('uuid4')
    email = factory.Faker('email')
    full_name = factory.Faker('name')
    tenant_id = factory.SubFactory(TenantFactory)
```

## Debugging and Troubleshooting

### Local Debugging

#### VS Code Debug Configuration
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "FastAPI Debug",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/backend/app/main.py",
            "console": "integratedTerminal",
            "env": {
                "DATABASE_URL": "postgresql+asyncpg://audit_user:audit_password@localhost:5432/audit_logs"
            }
        }
    ]
}
```

#### Debugging Tips

1. **Use Correlation IDs**
```python
# Track requests across services
correlation_id = request.headers.get("X-Correlation-ID")
logger.info("Processing request", correlation_id=correlation_id)
```

2. **Database Query Debugging**
```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Use EXPLAIN for slow queries
result = await session.execute(text("EXPLAIN ANALYZE SELECT * FROM audit_logs"))
```

3. **Performance Profiling**
```python
# Use cProfile for performance analysis
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... your code ...
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Production Debugging

#### Log Analysis
```bash
# Find errors in logs
docker-compose logs api | grep -i error | tail -20

# Track specific request
docker-compose logs api | grep "correlation_id=550e8400"

# Analyze performance
docker-compose logs api | grep "duration_ms" | awk '{print $NF}' | sort -n
```

#### Monitoring Queries
```bash
# Check Prometheus metrics
curl -s http://localhost:9090/api/v1/query?query=audit_api_requests_total

# Check Grafana dashboards
# Navigate to http://localhost:3001

# Check application health
curl -s http://localhost:8000/api/v1/metrics/health | jq '.'
```

## Contributing Guidelines

### Pull Request Process

1. **Before Starting**
   - Check existing issues and PRs
   - Discuss major changes in issues first
   - Ensure you have the latest code

2. **Development**
   - Create feature branch from `develop`
   - Follow coding standards
   - Write tests for new functionality
   - Update documentation

3. **Before Submitting**
   - Run full test suite: `make test`
   - Run code quality checks: `make lint`
   - Update CHANGELOG.md
   - Rebase on latest develop

4. **Pull Request**
   - Use descriptive title and description
   - Link related issues
   - Add screenshots for UI changes
   - Request review from team members

### Code Review Checklist

#### Functionality
- [ ] Code works as intended
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] Performance considerations addressed

#### Code Quality
- [ ] Follows coding standards
- [ ] No code duplication
- [ ] Functions are focused and small
- [ ] Variable names are descriptive

#### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Test coverage maintained
- [ ] Manual testing performed

#### Documentation
- [ ] Code is self-documenting
- [ ] Complex logic is commented
- [ ] API documentation updated
- [ ] README updated if needed

#### Security
- [ ] No sensitive data exposed
- [ ] Input validation implemented
- [ ] Authentication/authorization correct
- [ ] SQL injection prevention

## Resources and References

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Documentation](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Backstage.io Documentation](https://backstage.io/docs/)

### Internal Resources
- [API Documentation](http://localhost:8000/docs) (when running locally)
- [Architecture Documentation](./architecture.md)
- [Deployment Guide](./deployment.md)
- [Monitoring Guide](./monitoring.md)
- [Troubleshooting Guide](./troubleshooting.md)

### Development Tools
- [Poetry](https://python-poetry.org/) - Dependency management
- [Black](https://black.readthedocs.io/) - Code formatting
- [isort](https://pycqa.github.io/isort/) - Import sorting
- [mypy](https://mypy.readthedocs.io/) - Type checking
- [pytest](https://docs.pytest.org/) - Testing framework

### Useful Commands

```bash
# Development
make dev                    # Start development environment
make test                   # Run all tests
make lint                   # Run linting
make format                 # Format code
make type-check            # Run type checking

# Database
make db-migrate            # Run database migrations
make db-reset              # Reset database
make db-seed               # Seed test data

# Docker
make docker-build          # Build Docker images
make docker-clean          # Clean Docker resources
make logs                  # View logs

# Monitoring
make metrics               # View metrics
make health                # Check health
```

### Getting Help

1. **Documentation**: Check this guide and other docs first
2. **Issues**: Search existing GitHub issues
3. **Team Chat**: Ask in the development channel
4. **Code Review**: Request help in PR comments
5. **Pair Programming**: Schedule sessions with team members

### Next Steps

Now that you're set up, here are some good first tasks:

1. **Explore the Codebase**
   - Read through the main API endpoints
   - Understand the database models
   - Review the test structure

2. **Make a Small Change**
   - Fix a typo in documentation
   - Add a small feature
   - Improve error messages

3. **Run the Full Test Suite**
   - Understand how tests work
   - Add a simple test
   - Run load tests

4. **Review Recent PRs**
   - See how others structure changes
   - Understand the review process
   - Learn from feedback

Welcome to the team! We're excited to have you contribute to building a world-class audit logging system. Don't hesitate to ask questions and seek help when needed.