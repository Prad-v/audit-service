# Quick Start Guide

## Overview

This guide will help you get started with the Audit Service in minutes. You'll learn how to set up the service, create your first audit event, and integrate it into your application.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for development)
- Node.js 18+ (for frontend development)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/audit-service.git
cd audit-service
```

### 2. Start the Services

```bash
# Start all services
./scripts/start.sh start

# Or start in development mode
./scripts/start.sh dev
```

### 3. Verify Installation

Check that all services are running:

```bash
# Check service status
./scripts/start.sh status

# Test API health
curl http://localhost:8000/health/

# Access the frontend
open http://localhost:3000
```

## Your First Audit Event

### Using the API

```bash
# Create an audit event
curl -X POST http://localhost:8000/api/v1/audit/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "user_login",
    "action": "login",
    "status": "success",
    "tenant_id": "demo_tenant",
    "service_name": "demo_service",
    "user_id": "user_123",
    "resource_type": "user",
    "resource_id": "user_123"
  }'
```

### Using the Frontend

1. Open http://localhost:3000
2. Navigate to "Create Event"
3. Fill in the event details
4. Click "Create Event"

### Using Python SDK

```python
import requests

# Create an audit event
response = requests.post(
    "http://localhost:8000/api/v1/audit/events",
    json={
        "event_type": "user_login",
        "action": "login",
        "status": "success",
        "tenant_id": "demo_tenant",
        "service_name": "demo_service",
        "user_id": "user_123"
    }
)

print(f"Event created: {response.json()['audit_id']}")
```

## Querying Audit Events

### Get All Events

```bash
curl "http://localhost:8000/api/v1/audit/events?page=1&size=10"
```

### Filter Events

```bash
# Filter by event type
curl "http://localhost:8000/api/v1/audit/events?event_types=user_login"

# Filter by status
curl "http://localhost:8000/api/v1/audit/events?status=success"

# Filter by time range
curl "http://localhost:8000/api/v1/audit/events?start_time=2024-01-01T00:00:00Z&end_time=2024-01-31T23:59:59Z"
```

### Get Specific Event

```bash
# Replace with actual audit_id
curl "http://localhost:8000/api/v1/audit/events/550e8400-e29b-41d4-a716-446655440000"
```

## Integration Examples

### Express.js Application

```javascript
const express = require('express');
const axios = require('axios');

const app = express();

// Middleware to log all requests
app.use(async (req, res, next) => {
  const startTime = Date.now();
  
  // Call next middleware
  next();
  
  // Log the request
  try {
    await axios.post('http://localhost:8000/api/v1/audit/events', {
      event_type: 'http_request',
      action: req.method,
      status: res.statusCode < 400 ? 'success' : 'failure',
      tenant_id: req.headers['x-tenant-id'] || 'default',
      service_name: 'express_app',
      user_id: req.headers['x-user-id'] || 'anonymous',
      resource_type: 'http_endpoint',
      resource_id: req.path,
      ip_address: req.ip,
      user_agent: req.get('User-Agent'),
      request_data: {
        method: req.method,
        path: req.path,
        headers: req.headers
      },
      response_data: {
        status_code: res.statusCode,
        response_time: Date.now() - startTime
      }
    });
  } catch (error) {
    console.error('Failed to log audit event:', error);
  }
});

app.listen(3001, () => {
  console.log('Express app running on port 3001');
});
```

### Python Flask Application

```python
from flask import Flask, request, g
import requests
import time

app = Flask(__name__)

@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    try:
        requests.post('http://localhost:8000/api/v1/audit/events', json={
            'event_type': 'http_request',
            'action': request.method,
            'status': 'success' if response.status_code < 400 else 'failure',
            'tenant_id': request.headers.get('X-Tenant-ID', 'default'),
            'service_name': 'flask_app',
            'user_id': request.headers.get('X-User-ID', 'anonymous'),
            'resource_type': 'http_endpoint',
            'resource_id': request.path,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string,
            'request_data': {
                'method': request.method,
                'path': request.path,
                'headers': dict(request.headers)
            },
            'response_data': {
                'status_code': response.status_code,
                'response_time': time.time() - g.start_time
            }
        })
    except Exception as e:
        print(f'Failed to log audit event: {e}')
    
    return response

@app.route('/')
def hello():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(port=5000)
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/audit_db

# Redis
REDIS_URL=redis://localhost:6379/0

# NATS
NATS_URL=nats://localhost:4222

# RBAC (for development)
RBAC_AUTHENTICATION_DISABLED=true
RBAC_AUTHORIZATION_DISABLED=true

# API Settings
DEBUG=true
LOG_LEVEL=INFO
```

### Docker Compose Configuration

```yaml
version: '3.8'
services:
  api:
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/audit_db
      - REDIS_URL=redis://redis:6379/0
      - NATS_URL=nats://nats:4222
      - RBAC_AUTHENTICATION_DISABLED=true
      - RBAC_AUTHORIZATION_DISABLED=true
```

## Testing

### Run the Test Suite

```bash
# Run all tests
python3 run_tests.py

# Run specific test types
python3 run_tests.py --unit
python3 run_tests.py --integration
python3 run_tests.py --e2e

# Run with continue on fail
python3 run_tests.py --continue-on-fail
```

### Manual Testing

```bash
# Test API health
curl http://localhost:8000/health/

# Test creating an event
curl -X POST http://localhost:8000/api/v1/audit/events \
  -H "Content-Type: application/json" \
  -d '{"event_type": "test", "action": "test", "status": "success", "service_name": "test"}'

# Test querying events
curl "http://localhost:8000/api/v1/audit/events?page=1&size=5"
```

## Next Steps

1. **Explore the API Documentation**: Visit http://localhost:8000/docs
2. **Check the Frontend**: Visit http://localhost:3000
3. **Read the Full Documentation**: See the [docs/](docs/) directory
4. **Run the Test Suite**: `python3 run_tests.py`
5. **Deploy to Production**: See [deployment guide](deployment/production.md)

## Troubleshooting

### Common Issues

1. **Services not starting**:
   ```bash
   # Check Docker status
   docker ps
   
   # Check logs
   docker-compose logs
   ```

2. **Database connection issues**:
   ```bash
   # Check database logs
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

3. **API not responding**:
   ```bash
   # Check API logs
   docker-compose logs api
   
   # Restart API
   docker-compose restart api
   ```

### Getting Help

- **Documentation**: [docs/](docs/) directory
- **API Docs**: http://localhost:8000/docs
- **GitHub Issues**: [Create an issue](https://github.com/your-org/audit-service/issues)
- **Community**: [Join our Discord](https://discord.gg/audit-service)
