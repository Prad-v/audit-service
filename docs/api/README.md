# Audit Service API Documentation

## Overview

The Audit Service API provides a comprehensive audit logging system with RESTful endpoints for creating, retrieving, and querying audit events. The API is built with FastAPI and provides automatic OpenAPI documentation.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

The API supports multiple authentication methods:

### 1. JWT Tokens
```bash
Authorization: Bearer <your-jwt-token>
```

### 2. API Keys
```bash
X-API-Key: <your-api-key>
```

### 3. RBAC Disabled (Development)
For development and testing, RBAC can be disabled using environment variables:
- `RBAC_AUTHENTICATION_DISABLED=true`
- `RBAC_AUTHORIZATION_DISABLED=true`

## Health Check

### GET /health/

Check the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "nats": "healthy"
  }
}
```

## Audit Events

### Create Audit Event

**POST** `/api/v1/audit/events`

Create a single audit event.

**Request Body:**
```json
{
  "event_type": "user_login",
  "action": "login",
  "status": "success",
  "tenant_id": "tenant_123",
  "service_name": "auth_service",
  "user_id": "user_456",
  "resource_type": "user",
  "resource_id": "user_456",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "request_data": {
    "method": "POST",
    "path": "/login",
    "headers": {}
  },
  "response_data": {
    "status_code": 200,
    "body": {}
  },
  "metadata": {
    "session_id": "sess_789",
    "login_method": "password"
  }
}
```

**Response:**
```json
{
  "audit_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "user_login",
  "action": "login",
  "status": "success",
  "tenant_id": "tenant_123",
  "service_name": "auth_service",
  "user_id": "user_456",
  "resource_type": "user",
  "resource_id": "user_456",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "request_data": {
    "method": "POST",
    "path": "/login",
    "headers": {}
  },
  "response_data": {
    "status_code": 200,
    "body": {}
  },
  "metadata": {
    "session_id": "sess_789",
    "login_method": "password"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Create Batch Audit Events

**POST** `/api/v1/audit/events/batch`

Create multiple audit events in a single request.

**Request Body:**
```json
{
  "events": [
    {
      "event_type": "user_login",
      "action": "login",
      "status": "success",
      "tenant_id": "tenant_123",
      "service_name": "auth_service",
      "user_id": "user_456"
    },
    {
      "event_type": "data_access",
      "action": "read",
      "status": "success",
      "tenant_id": "tenant_123",
      "service_name": "data_service",
      "user_id": "user_456",
      "resource_type": "document",
      "resource_id": "doc_789"
    }
  ]
}
```

**Response:**
```json
[
  {
    "audit_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "user_login",
    "action": "login",
    "status": "success",
    "tenant_id": "tenant_123",
    "service_name": "auth_service",
    "user_id": "user_456",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  {
    "audit_id": "550e8400-e29b-41d4-a716-446655440001",
    "event_type": "data_access",
    "action": "read",
    "status": "success",
    "tenant_id": "tenant_123",
    "service_name": "data_service",
    "user_id": "user_456",
    "resource_type": "document",
    "resource_id": "doc_789",
    "timestamp": "2024-01-15T10:30:01Z"
  }
]
```

### Get Audit Event

**GET** `/api/v1/audit/events/{audit_id}`

Retrieve a specific audit event by ID.

**Response:**
```json
{
  "audit_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "user_login",
  "action": "login",
  "status": "success",
  "tenant_id": "tenant_123",
  "service_name": "auth_service",
  "user_id": "user_456",
  "resource_type": "user",
  "resource_id": "user_456",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "request_data": {
    "method": "POST",
    "path": "/login",
    "headers": {}
  },
  "response_data": {
    "status_code": 200,
    "body": {}
  },
  "metadata": {
    "session_id": "sess_789",
    "login_method": "password"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Query Audit Events

**GET** `/api/v1/audit/events`

Query audit events with filtering, sorting, and pagination.

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `size` (int): Page size (default: 50, max: 1000)
- `event_types` (string): Comma-separated list of event types
- `status` (string): Event status (success, failure, warning)
- `tenant_id` (string): Tenant ID filter
- `service_name` (string): Service name filter
- `user_id` (string): User ID filter
- `resource_type` (string): Resource type filter
- `resource_id` (string): Resource ID filter
- `start_time` (string): Start time (ISO 8601 format)
- `end_time` (string): End time (ISO 8601 format)
- `sort_by` (string): Sort field (timestamp, created_at, event_type)
- `sort_order` (string): Sort order (asc, desc)

**Example Request:**
```
GET /api/v1/audit/events?page=1&size=10&event_types=user_login,data_access&status=success&start_time=2024-01-01T00:00:00Z&end_time=2024-01-15T23:59:59Z&sort_by=timestamp&sort_order=desc
```

**Response:**
```json
{
  "items": [
    {
      "audit_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "user_login",
      "action": "login",
      "status": "success",
      "tenant_id": "tenant_123",
      "service_name": "auth_service",
      "user_id": "user_456",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 150,
  "page": 1,
  "page_size": 10,
  "total_pages": 15,
  "has_next": true,
  "has_previous": false
}
```

### Export Audit Events

**GET** `/api/v1/audit/events/export`

Export audit events in various formats.

**Query Parameters:**
- Same as query endpoint
- `format` (string): Export format (json, csv, xlsx)

**Response:**
- JSON: Same as query endpoint
- CSV: Comma-separated values file
- XLSX: Excel file

### Get Audit Summary

**GET** `/api/v1/audit/summary`

Get summary statistics for audit events.

**Query Parameters:**
- Same as query endpoint (except pagination)

**Response:**
```json
{
  "total_events": 1500,
  "events_by_type": {
    "user_login": 500,
    "data_access": 300,
    "system_event": 200
  },
  "events_by_status": {
    "success": 1400,
    "failure": 80,
    "warning": 20
  },
  "events_by_service": {
    "auth_service": 500,
    "data_service": 300,
    "system_service": 200
  },
  "time_range": {
    "start_time": "2024-01-01T00:00:00Z",
    "end_time": "2024-01-15T23:59:59Z"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "event_type",
        "message": "Field is required"
      }
    ]
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Request validation failed
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `INTERNAL_ERROR`: Server error

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user
- **Headers**: Rate limit information is included in response headers

## WebSocket Events

### Audit Event Stream

**WebSocket** `/ws/audit/events`

Subscribe to real-time audit events.

**Message Format:**
```json
{
  "type": "audit_event",
  "data": {
    "audit_id": "550e8400-e29b-41d4-a716-446655440000",
    "event_type": "user_login",
    "action": "login",
    "status": "success",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## SDKs and Libraries

### Python
```bash
pip install audit-service-sdk
```

```python
from audit_service import AuditClient

client = AuditClient(api_key="your-api-key")
event = client.create_event(
    event_type="user_login",
    action="login",
    status="success",
    user_id="user_123"
)
```

### JavaScript/TypeScript
```bash
npm install @audit-service/sdk
```

```javascript
import { AuditClient } from '@audit-service/sdk';

const client = new AuditClient({ apiKey: 'your-api-key' });
const event = await client.createEvent({
  eventType: 'user_login',
  action: 'login',
  status: 'success',
  userId: 'user_123'
});
```

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

## Support

For API support and questions:
- **Documentation**: [docs.audit-service.com](https://docs.audit-service.com)
- **GitHub Issues**: [github.com/audit-service/issues](https://github.com/audit-service/issues)
- **Email**: api-support@audit-service.com
