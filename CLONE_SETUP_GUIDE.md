# Clone Setup Guide - Audit Service

This guide ensures that when you clone this repository to a different machine, all necessary files are included and the setup process works seamlessly.

## ✅ What's Fixed

### 1. **Gitignore Issues Resolved**
- **Frontend files**: Ensured `frontend/src/`, `frontend/package.json`, and other essential files are not ignored
- **Backend services**: All service files in `backend/services/` are included
- **Scripts and configs**: All setup scripts and configuration files are preserved
- **Documentation**: All docs are included in the repository

### 2. **Comprehensive Makefile Created**
- **Setup commands**: `make setup`, `make setup-env`, `make setup-db`
- **Docker commands**: `make build`, `make start`, `make stop`, `make restart`
- **Development commands**: `make dev`, `make logs`, `make health`
- **Testing commands**: `make test`, `make test-backend`, `make test-frontend`
- **Database commands**: `make migrate-db`, `make backup`, `make restore`
- **Help**: `make help` shows all available commands

### 3. **Database Setup Automation**
- **Automated script**: `scripts/setup-databases.sh` creates all databases and schemas
- **Schema creation**: All necessary tables and indexes are created automatically
- **User management**: Database users and permissions are set up correctly
- **Sample data**: Initial data is inserted for testing

### 4. **Environment Configuration**
- **Template file**: `.env.example` provides a template for environment variables
- **Auto-creation**: `make setup-env` creates `.env` file from template
- **Default values**: Safe defaults for all configuration options

## 🚀 Quick Setup on New Machine

### Option 1: One-Command Setup
```bash
# Clone the repository
git clone <repository-url>
cd audit-service

# Run complete setup
./quick-start.sh
```

### Option 2: Makefile Setup
```bash
# Clone the repository
git clone <repository-url>
cd audit-service

# Complete setup
make setup

# Start services
make start
```

### Option 3: Manual Setup
```bash
# Clone the repository
git clone <repository-url>
cd audit-service

# Setup environment
make setup-env

# Setup databases
make create-db
make setup-db

# Build and start
make build
make start
```

## 📋 Prerequisites Check

The setup scripts automatically check for:
- ✅ Docker (version 20.10+)
- ✅ Docker Compose (version 2.0+)
- ✅ Make
- ✅ Git

## 🗄️ Database Setup

The system creates three databases:

### 1. **audit_logs** (Primary Database)
- **User**: `audit_user`
- **Password**: `audit_password`
- **Tables**: `audit_logs`, `stackstorm_tests`, `test_executions`

### 2. **events_db** (Events Processing)
- **User**: `events_user`
- **Password**: `events_password`
- **Tables**: `events`, `event_processors`, `event_subscriptions`

### 3. **alerting_db** (Alert Management)
- **User**: `alerting_user`
- **Password**: `alerting_password`
- **Tables**: `alerts`, `alert_rules`, `alert_notifications`

## 🔧 Service Architecture

After setup, the following services will be running:

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3000 | React web interface |
| Backend API | 8000 | Main API service |
| StackStorm Tests | 8004 | Synthetic testing framework |
| Events Service | 8003 | Event processing |
| Alerting Service | 8001 | Alert management |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Caching |
| NATS | 4222 | Message queuing |

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. **Port Conflicts**
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :8000

# Stop conflicting services or change ports in docker-compose.yml
```

#### 2. **Database Connection Issues**
```bash
# Check database status
make logs-db

# Reset database
make reset-db
```

#### 3. **Frontend Build Issues**
```bash
# Clean and rebuild
make clean
make build
```

#### 4. **Permission Issues**
```bash
# Fix script permissions
chmod +x scripts/*.sh
chmod +x quick-start.sh
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
```

## 📁 File Structure

The repository now includes all necessary files:

```
audit-service/
├── backend/                    # ✅ All backend services included
│   ├── services/              # ✅ All service files preserved
│   │   ├── stackstorm-tests/  # ✅ StackStorm test framework
│   │   ├── audit-service/     # ✅ Audit service
│   │   └── ...                # ✅ All other services
│   ├── app/                   # ✅ Main application code
│   ├── requirements.txt       # ✅ Dependencies
│   └── Dockerfile            # ✅ Build configuration
├── frontend/                  # ✅ Complete frontend included
│   ├── src/                  # ✅ All source files
│   ├── public/               # ✅ Static assets
│   ├── package.json          # ✅ Dependencies
│   ├── vite.config.ts        # ✅ Build configuration
│   └── Dockerfile.dev        # ✅ Development build
├── scripts/                  # ✅ All setup scripts
│   ├── setup-databases.sh    # ✅ Database setup
│   ├── init-db.sql          # ✅ Database initialization
│   └── ...                  # ✅ Other utility scripts
├── helm/                     # ✅ Kubernetes deployment
├── docs/                     # ✅ Documentation
├── tests/                    # ✅ Test suites
├── docker-compose.yml        # ✅ Service orchestration
├── Makefile                  # ✅ Build and setup commands
├── quick-start.sh           # ✅ One-command setup
├── .env.example             # ✅ Environment template
├── SETUP.md                 # ✅ Detailed setup guide
└── CLONE_SETUP_GUIDE.md     # ✅ This file
```

## 🎯 Verification

After setup, verify everything is working:

1. **Check service health**:
   ```bash
   make health
   ```

2. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - StackStorm Tests: http://localhost:8004

3. **Test functionality**:
   - Create a StackStorm test
   - Execute the test
   - Check execution results

## 📚 Additional Resources

- **SETUP.md**: Detailed setup instructions
- **README.md**: Main project documentation
- **docs/**: Comprehensive documentation
- **Makefile**: All available commands (`make help`)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review service logs: `make logs`
3. Check service health: `make health`
4. Run diagnostics: `make troubleshoot`

The setup is now fully automated and should work seamlessly on any machine with the required prerequisites!
