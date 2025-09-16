# Audit Service - Setup Guide

This guide will help you set up the Audit Service on a new machine from scratch.

## Prerequisites

Before starting, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Make** (for using the Makefile commands)
- **Git** (for cloning the repository)

### Installing Prerequisites

#### Docker and Docker Compose
```bash
# On Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose make git

# On macOS (using Homebrew)
brew install docker docker-compose make git

# On Windows
# Download Docker Desktop from https://www.docker.com/products/docker-desktop
```

## Quick Setup

The fastest way to get started:

```bash
# Clone the repository
git clone <repository-url>
cd audit-service

# Run the complete setup
make setup

# Start all services
make start
```

The application will be available at http://localhost:3000

## Detailed Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd audit-service
```

### 2. Environment Setup

```bash
# Create environment files
make setup-env
```

This creates a `.env` file with default configuration. You can modify it as needed.

### 3. Database Setup

```bash
# Create databases and users
make create-db

# Setup database schemas
make setup-db
```

Or run the comprehensive database setup script:

```bash
./scripts/setup-databases.sh
```

### 4. Install Dependencies

```bash
# Install frontend dependencies
make setup-frontend

# Install backend dependencies
make setup-backend
```

### 5. Start Services

```bash
# Build and start all services
make build
make start
```

## Available Make Commands

### Setup Commands
- `make setup` - Complete setup for new machine
- `make setup-env` - Create environment files
- `make setup-db` - Setup database schemas
- `make setup-frontend` - Install frontend dependencies
- `make setup-backend` - Install backend dependencies

### Docker Commands
- `make build` - Build all Docker images
- `make start` - Start all services
- `make stop` - Stop all services
- `make restart` - Restart all services
- `make clean` - Clean up Docker resources

### Development Commands
- `make dev` - Start in development mode
- `make logs` - Show all service logs
- `make logs-backend` - Show backend logs
- `make logs-frontend` - Show frontend logs
- `make logs-db` - Show database logs

### Testing Commands
- `make test` - Run all tests
- `make test-backend` - Run backend tests
- `make test-frontend` - Run frontend tests
- `make test-e2e` - Run end-to-end tests

### Code Quality Commands
- `make lint` - Run linting
- `make format` - Format code
- `make health` - Check service health

### Database Commands
- `make migrate-db` - Run database migrations
- `make reset-db` - Reset database (WARNING: deletes all data)
- `make backup` - Backup database
- `make restore` - Restore database from backup

## Service Architecture

The Audit Service consists of the following components:

### Backend Services
- **API Gateway** (port 8000) - Main API service
- **Events Service** (port 8003) - Event processing
- **StackStorm Tests** (port 8004) - Synthetic testing framework
- **Alerting Service** (port 8001) - Alert management

### Frontend
- **React Application** (port 3000) - Web interface

### Infrastructure
- **PostgreSQL** (port 5432) - Primary database
- **Redis** (port 6379) - Caching and sessions
- **NATS** (port 4222) - Message queuing

## Database Schema

The system uses three main databases:

### audit_logs
- Stores audit logs and system events
- Contains StackStorm test configurations and executions
- User: `audit_user`

### events_db
- Stores event processing data
- Event processors and subscriptions
- User: `events_user`

### alerting_db
- Stores alert rules and notifications
- Alert management data
- User: `alerting_user`

## Configuration

### Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://audit_user:audit_password@localhost:5432/audit_logs

# Redis
REDIS_URL=redis://localhost:6379

# NATS
NATS_URL=nats://localhost:4222

# StackStorm
STACKSTORM_USERNAME=st2admin
STACKSTORM_PASSWORD=st2admin

# Logging
LOG_LEVEL=INFO
```

### Docker Compose

The system uses Docker Compose for orchestration. Key files:

- `docker-compose.yml` - Main configuration
- `docker-compose.dev.yml` - Development overrides
- `docker-compose.prod.yml` - Production overrides

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using the ports
   lsof -i :3000
   lsof -i :8000
   
   # Stop conflicting services or change ports in docker-compose.yml
   ```

2. **Database connection issues**
   ```bash
   # Check database status
   make logs-db
   
   # Reset database
   make reset-db
   ```

3. **Frontend build issues**
   ```bash
   # Clean and rebuild
   make clean
   make build
   ```

4. **Permission issues**
   ```bash
   # Fix script permissions
   chmod +x scripts/*.sh
   ```

### Health Checks

```bash
# Check all services
make health

# Check specific service
curl -f http://localhost:3000  # Frontend
curl -f http://localhost:8000/health  # Backend API
curl -f http://localhost:8004/health  # StackStorm Tests
```

### Logs

```bash
# View all logs
make logs

# View specific service logs
make logs-backend
make logs-frontend
make logs-db

# Follow logs in real-time
docker-compose logs -f
```

## Development

### Adding New Services

1. Create service directory in `backend/services/`
2. Add Dockerfile and requirements.txt
3. Update docker-compose.yml
4. Add to Makefile if needed

### Frontend Development

```bash
# Start in development mode
make dev

# Run frontend tests
make test-frontend

# Format frontend code
cd frontend && npm run format
```

### Backend Development

```bash
# Run backend tests
make test-backend

# Format backend code
cd backend && black app/ tests/
```

## Production Deployment

### Using Helm Charts

```bash
# Deploy to Kubernetes
helm install audit-service helm/audit-service/

# Update deployment
helm upgrade audit-service helm/audit-service/
```

### Using Docker Compose

```bash
# Deploy to production
make deploy-prod
```

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review service logs: `make logs`
3. Check service health: `make health`
4. Run diagnostics: `make troubleshoot`

## File Structure

```
audit-service/
├── backend/                 # Backend services
│   ├── services/           # Individual services
│   ├── alembic/           # Database migrations
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   └── package.json      # Node dependencies
├── scripts/              # Setup and utility scripts
├── helm/                 # Kubernetes Helm charts
├── docs/                 # Documentation
├── tests/                # Test suites
├── docker-compose.yml    # Main Docker Compose config
├── Makefile             # Build and setup commands
└── SETUP.md             # This file
```
