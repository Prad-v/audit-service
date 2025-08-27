.PHONY: help dev-up dev-down dev-restart build clean test lint format migrate logs shell-api shell-db install-deps

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Environment
dev-up: ## Start all development services
	docker-compose up -d
	@echo "Services starting... Use 'make logs' to view logs"
	@echo "API will be available at: http://localhost:8000"
	@echo "Frontend will be available at: http://localhost:3000"
	@echo "Grafana will be available at: http://localhost:3001 (admin/admin)"
	@echo "NATS monitoring at: http://localhost:8222"

dev-down: ## Stop all development services
	docker-compose down

dev-restart: ## Restart all development services
	docker-compose restart

dev-rebuild: ## Rebuild and restart all services
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Build Commands
build: ## Build all Docker images
	docker-compose build

build-api: ## Build only the API image
	docker-compose build api

build-frontend: ## Build only the frontend image
	docker-compose build frontend

# Database Commands
migrate: ## Run database migrations
	docker-compose exec api python -m alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="description")
	docker-compose exec api python -m alembic revision --autogenerate -m "$(MESSAGE)"

migrate-downgrade: ## Downgrade database by one migration
	docker-compose exec api python -m alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	$(MAKE) migrate

# Development Commands
dev-api: ## Run API server in development mode (outside Docker)
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## Run background worker in development mode (outside Docker)
	cd backend && python -m app.worker

dev-frontend: ## Run frontend in development mode (outside Docker)
	cd frontend && npm run dev

# Testing
test: ## Run all tests
	docker-compose exec api python -m pytest tests/ -v

test-unit: ## Run unit tests only
	docker-compose exec api python -m pytest tests/unit/ -v

test-integration: ## Run integration tests only
	docker-compose exec api python -m pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	docker-compose exec api python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

test-load: ## Run load tests
	cd tools/load-testing && python -m locust --host=http://localhost:8000

# Code Quality
lint: ## Run linting
	docker-compose exec api python -m flake8 app/
	docker-compose exec api python -m mypy app/
	docker-compose exec api python -m bandit -r app/

format: ## Format code
	docker-compose exec api python -m black app/ tests/
	docker-compose exec api python -m isort app/ tests/

format-check: ## Check code formatting
	docker-compose exec api python -m black --check app/ tests/
	docker-compose exec api python -m isort --check-only app/ tests/

# Utility Commands
logs: ## View logs from all services
	docker-compose logs -f

logs-api: ## View API logs only
	docker-compose logs -f api

logs-worker: ## View worker logs only
	docker-compose logs -f worker

logs-db: ## View database logs only
	docker-compose logs -f postgres

shell-api: ## Open shell in API container
	docker-compose exec api bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U audit_user -d audit_logs

shell-redis: ## Open Redis CLI
	docker-compose exec redis redis-cli

# Monitoring
monitor: ## Open monitoring dashboards
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "NATS Monitoring: http://localhost:8222"

# Cleanup
clean: ## Clean up Docker resources
	docker-compose down -v --remove-orphans
	docker system prune -f
	docker volume prune -f

clean-all: ## Clean up everything including images
	docker-compose down -v --remove-orphans --rmi all
	docker system prune -af
	docker volume prune -f

# Installation
install-deps: ## Install local development dependencies
	cd backend && pip install -r requirements-dev.txt
	cd frontend && npm install

# SDK Commands
generate-sdk: ## Generate client SDKs
	docker-compose exec api python -m app.scripts.generate_openapi
	cd tools/sdk-generator && python generate.py

# Data Management
seed-data: ## Load test data
	docker-compose exec api python -m app.scripts.load_test_data

init-auth: ## Initialize authentication data (default tenant and admin user)
	docker-compose exec api python /app/scripts/init-auth.py

backup-db: ## Backup database
	docker-compose exec postgres pg_dump -U audit_user audit_logs > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database (usage: make restore-db FILE=backup.sql)
	docker-compose exec -T postgres psql -U audit_user -d audit_logs < $(FILE)

# Security
security-scan: ## Run security scans
	docker-compose exec api python -m bandit -r app/
	docker-compose exec api python -m safety check

# Performance
benchmark: ## Run performance benchmarks
	cd tools/load-testing && k6 run k6-script.js

# Documentation
docs: ## Generate documentation
	cd backend && python -m sphinx.cmd.build docs docs/_build

docs-serve: ## Serve documentation locally
	cd backend/docs/_build && python -m http.server 8080

# Environment Setup
setup-dev: ## Complete development environment setup
	@echo "Setting up development environment..."
	$(MAKE) install-deps
	$(MAKE) dev-up
	@echo "Waiting for services to start..."
	sleep 30
	$(MAKE) migrate
	$(MAKE) init-auth
	$(MAKE) seed-data
	@echo "Development environment ready!"
	@echo "API: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"
	@echo "Monitoring: http://localhost:3001"
	@echo "Default login: admin / admin123"

# Production-like testing
prod-test: ## Test with production-like settings
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	sleep 30
	$(MAKE) test
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down