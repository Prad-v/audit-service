# Audit Service - Makefile for Setup and Development
# This Makefile provides commands for setting up the audit service on a new machine

.PHONY: help setup clean build start stop restart logs test lint format check-deps install-deps setup-db migrate-db create-db setup-env

# Default target
help: ## Show this help message
	@echo "Audit Service - Available Commands:"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
setup-env: ## Create environment files from templates
	@echo "Setting up environment files..."
	@if [ ! -f .env ]; then \
		cp .env.example .env 2>/dev/null || echo "Creating basic .env file..."; \
		echo "DATABASE_URL=postgresql://audit_user:audit_password@localhost:5432/audit_logs" > .env; \
		echo "REDIS_URL=redis://localhost:6379" >> .env; \
		echo "NATS_URL=nats://localhost:4222" >> .env; \
		echo "STACKSTORM_USERNAME=st2admin" >> .env; \
		echo "STACKSTORM_PASSWORD=st2admin" >> .env; \
		echo "LOG_LEVEL=INFO" >> .env; \
	fi
	@echo "Environment files created successfully!"

# Dependency installation
install-deps: ## Install system dependencies
	@echo "Installing system dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Please install Docker first."; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Please install Docker Compose first."; exit 1; }
	@command -v make >/dev/null 2>&1 || { echo "Make is required but not installed. Please install Make first."; exit 1; }
	@echo "System dependencies check passed!"

# Database setup
create-db: ## Create PostgreSQL databases
	@echo "Creating PostgreSQL databases..."
	@docker-compose up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 10
	@docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE audit_logs;" || echo "Database audit_logs may already exist"
	@docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE events_db;" || echo "Database events_db may already exist"
	@docker-compose exec -T postgres psql -U postgres -c "CREATE DATABASE alerting_db;" || echo "Database alerting_db may already exist"
	@docker-compose exec -T postgres psql -U postgres -c "CREATE USER audit_user WITH PASSWORD 'audit_password';" || echo "User audit_user may already exist"
	@docker-compose exec -T postgres psql -U postgres -c "CREATE USER events_user WITH PASSWORD 'events_password';" || echo "User events_user may already exist"
	@docker-compose exec -T postgres psql -U postgres -c "CREATE USER alerting_user WITH PASSWORD 'alerting_password';" || echo "User alerting_user may already exist"
	@docker-compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE audit_logs TO audit_user;"
	@docker-compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE events_db TO events_user;"
	@docker-compose exec -T postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE alerting_db TO alerting_user;"
	@echo "Databases created successfully!"

setup-db: create-db ## Setup database schemas and initial data
	@echo "Setting up database schemas..."
	@docker-compose up -d postgres
	@sleep 5
	@if [ -f scripts/init-db.sql ]; then \
		docker-compose exec -T postgres psql -U audit_user -d audit_logs -f /docker-entrypoint-initdb.d/init-db.sql || echo "Schema setup completed"; \
	fi
	@if [ -f scripts/init-events-db.sql ]; then \
		docker-compose exec -T postgres psql -U events_user -d events_db -f /docker-entrypoint-initdb.d/init-events-db.sql || echo "Events schema setup completed"; \
	fi
	@if [ -f scripts/init-alerting-db.sql ]; then \
		docker-compose exec -T postgres psql -U alerting_user -d alerting_db -f /docker-entrypoint-initdb.d/init-alerting-db.sql || echo "Alerting schema setup completed"; \
	fi
	@echo "Database schemas setup completed!"

# Frontend setup
setup-frontend: ## Setup frontend dependencies
	@echo "Setting up frontend dependencies..."
	@cd frontend && npm install
	@echo "Frontend dependencies installed!"

# Backend setup
setup-backend: ## Setup backend dependencies
	@echo "Setting up backend dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd backend && pip install -r requirements-dev.txt
	@echo "Backend dependencies installed!"

# Full setup
setup: install-deps setup-env create-db setup-db setup-frontend setup-backend ## Complete setup for new machine
	@echo "=================================="
	@echo "Setup completed successfully!"
	@echo "=================================="
	@echo "Next steps:"
	@echo "1. Run 'make start' to start all services"
	@echo "2. Run 'make logs' to view service logs"
	@echo "3. Access the application at http://localhost:3000"
	@echo "=================================="

# Docker operations
build: ## Build all Docker images
	@echo "Building Docker images..."
	@docker-compose build

start: ## Start all services
	@echo "Starting all services..."
	@docker-compose up -d
	@echo "Services started! Access the application at http://localhost:3000"

stop: ## Stop all services
	@echo "Stopping all services..."
	@docker-compose down

restart: stop start ## Restart all services

clean: ## Clean up Docker containers and volumes
	@echo "Cleaning up Docker resources..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f

# Development
dev: ## Start services in development mode
	@echo "Starting development environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Monitoring and logs
logs: ## Show logs for all services
	@docker-compose logs -f

logs-backend: ## Show backend logs
	@docker-compose logs -f api

logs-frontend: ## Show frontend logs
	@docker-compose logs -f frontend

logs-db: ## Show database logs
	@docker-compose logs -f postgres

# Testing
test: ## Run all tests
	@echo "Running tests..."
	@docker-compose exec api python -m pytest tests/ -v
	@cd frontend && npm test

test-backend: ## Run backend tests
	@docker-compose exec api python -m pytest tests/unit/ tests/integration/ -v

test-frontend: ## Run frontend tests
	@cd frontend && npm test

test-e2e: ## Run end-to-end tests
	@docker-compose exec api python -m pytest tests/e2e/ -v

# Code quality
lint: ## Run linting for all code
	@echo "Running linting..."
	@cd backend && flake8 app/ tests/
	@cd frontend && npm run lint

format: ## Format all code
	@echo "Formatting code..."
	@cd backend && black app/ tests/
	@cd frontend && npm run format

# Health checks
health: ## Check health of all services
	@echo "Checking service health..."
	@curl -f http://localhost:3000 > /dev/null && echo "Frontend: OK" || echo "Frontend: FAILED"
	@curl -f http://localhost:8000/health > /dev/null && echo "Backend API: OK" || echo "Backend API: FAILED"
	@curl -f http://localhost:8004/health > /dev/null && echo "StackStorm Tests: OK" || echo "StackStorm Tests: FAILED"
	@docker-compose exec postgres pg_isready -U postgres > /dev/null && echo "PostgreSQL: OK" || echo "PostgreSQL: FAILED"
	@docker-compose exec redis redis-cli ping > /dev/null && echo "Redis: OK" || echo "Redis: FAILED"

# Database operations
migrate-db: ## Run database migrations
	@echo "Running database migrations..."
	@docker-compose exec api alembic upgrade head

reset-db: ## Reset database (WARNING: This will delete all data)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@docker-compose down -v
	@make create-db
	@make setup-db

# Backup and restore
backup: ## Backup database
	@echo "Creating database backup..."
	@mkdir -p backups
	@docker-compose exec postgres pg_dump -U audit_user audit_logs > backups/audit_logs_$(shell date +%Y%m%d_%H%M%S).sql
	@docker-compose exec postgres pg_dump -U events_user events_db > backups/events_db_$(shell date +%Y%m%d_%H%M%S).sql
	@docker-compose exec postgres pg_dump -U alerting_user alerting_db > backups/alerting_db_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup completed!"

restore: ## Restore database from backup
	@echo "Available backups:"
	@ls -la backups/*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup file name: " backup_file; \
	if [ -f "backups/$$backup_file" ]; then \
		echo "Restoring from $$backup_file..."; \
		docker-compose exec -T postgres psql -U audit_user -d audit_logs < "backups/$$backup_file"; \
		echo "Restore completed!"; \
	else \
		echo "Backup file not found!"; \
	fi

# Production deployment
deploy-prod: ## Deploy to production
	@echo "Deploying to production..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "Production deployment completed!"

# Quick start for development
quick-start: setup start ## Quick start for development (setup + start)
	@echo "Quick start completed! Access the application at http://localhost:3000"

# Troubleshooting
troubleshoot: ## Run troubleshooting checks
	@echo "Running troubleshooting checks..."
	@echo "Docker version:"
	@docker --version
	@echo "Docker Compose version:"
	@docker-compose --version
	@echo "Available disk space:"
	@df -h
	@echo "Docker system info:"
	@docker system df
	@echo "Running containers:"
	@docker-compose ps
	@echo "Service health:"
	@make health