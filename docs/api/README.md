# Audit Service API Documentation

## Overview

The Audit Service API provides comprehensive audit logging capabilities with support for creating, querying, and exporting audit events. The API includes advanced filtering, dynamic field querying, and multi-tenant support.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

## Authentication

All API endpoints require authentication using JWT tokens or API keys.

### Headers
```
Authorization: Bearer <your-jwt-token>
Content-Type: application/json
```

## Endpoints

### Create Audit Event

**POST** `/api/v1/audit/events`

Create a single audit log event.

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

Create multiple audit log events in a single request.

**Request Body:**
```json
{
  "events": [
    {
      "event_type": "user_login",
      "action": "login",
      "status": "success",
      "user_id": "user_123"
    },
    {
      "event_type": "data_access",
      "action": "read",
      "status": "success",
      "user_id": "user_456"
    }
  ]
}
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

#### Standard Query Parameters

- `page` (int): Page number (default: 1)
- `size` (int): Page size (default: 50, max: 1000)
- `start_date` (datetime): Start date filter (ISO 8601 format)
- `end_date` (datetime): End date filter (ISO 8601 format)
- `event_types` (string): Comma-separated list of event types
- `resource_types` (string): Comma-separated list of resource types
- `resource_ids` (string): Comma-separated list of resource IDs
- `actions` (string): Comma-separated list of actions
- `severities` (string): Comma-separated list of severities
- `user_ids` (string): Comma-separated list of user IDs
- `ip_addresses` (string): Comma-separated list of IP addresses
- `session_ids` (string): Comma-separated list of session IDs
- `correlation_ids` (string): Comma-separated list of correlation IDs
- `sort_by` (string): Sort field (timestamp, created_at, event_type)
- `sort_order` (string): Sort order (asc, desc)

#### Dynamic Filtering Parameters

- `dynamic_filters` (string): JSON string of dynamic filters
- `filter_groups` (string): JSON string of filter groups

**Example Request with Standard Filters:**
```
GET /api/v1/audit/events?page=1&size=10&event_types=user_login,data_access&status=success&start_time=2024-01-01T00:00:00Z&end_time=2024-01-15T23:59:59Z&sort_by=timestamp&sort_order=desc
```

**Example Request with Dynamic Filters:**
```
GET /api/v1/audit/events?dynamic_filters=[{"field":"event_type","operator":"eq","value":"user_login"},{"field":"metadata.user_id","operator":"contains","value":"admin"}]&filter_groups=[{"filters":[{"field":"status","operator":"ne","value":"success"},{"field":"ip_address","operator":"starts_with","value":"192.168"}],"operator":"AND"}]
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
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 50,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false
}
```

### Get Filter Information

**GET** `/api/v1/audit/filters/info`

Get information about available fields and operators for dynamic filtering.

**Response:**
```json
{
  "available_fields": [
    "audit_id",
    "timestamp",
    "event_type",
    "action",
    "status",
    "tenant_id",
    "service_name",
    "user_id",
    "resource_type",
    "resource_id",
    "correlation_id",
    "session_id",
    "ip_address",
    "user_agent",
    "created_at",
    "updated_at",
    "request_data",
    "response_data",
    "metadata",
    "request_data.method",
    "request_data.path",
    "request_data.headers",
    "response_data.status_code",
    "response_data.body",
    "metadata.user_id",
    "metadata.session_id",
    "metadata.login_method"
  ],
  "supported_operators": [
    "eq",
    "ne",
    "gt",
    "gte",
    "lt",
    "lte",
    "in",
    "not_in",
    "contains",
    "not_contains",
    "starts_with",
    "ends_with",
    "is_null",
    "is_not_null",
    "regex"
  ],
  "examples": [
    {
      "field": "event_type",
      "operator": "eq",
      "value": "user_login",
      "description": "Find all user login events"
    },
    {
      "field": "status",
      "operator": "ne",
      "value": "success",
      "description": "Find all non-success events"
    },
    {
      "field": "timestamp",
      "operator": "gte",
      "value": "2024-01-01T00:00:00Z",
      "description": "Find events from 2024 onwards"
    },
    {
      "field": "metadata.user_id",
      "operator": "contains",
      "value": "admin",
      "description": "Find events with admin in user_id metadata"
    },
    {
      "field": "request_data.method",
      "operator": "in",
      "value": ["POST", "PUT", "DELETE"],
      "description": "Find events with write operations"
    },
    {
      "field": "ip_address",
      "operator": "starts_with",
      "value": "192.168",
      "description": "Find events from internal network"
    },
    {
      "field": "response_data.status_code",
      "operator": "gte",
      "value": 400,
      "description": "Find events with error status codes"
    }
  ],
  "field_mappings": {
    "standard_fields": [
      "audit_id",
      "timestamp",
      "event_type",
      "action",
      "status",
      "tenant_id",
      "service_name",
      "user_id",
      "resource_type",
      "resource_id",
      "correlation_id",
      "session_id",
      "ip_address",
      "user_agent",
      "created_at",
      "updated_at"
    ],
    "json_fields": [
      "request_data",
      "response_data",
      "metadata"
    ],
    "nested_json_examples": [
      "request_data.method",
      "request_data.path",
      "request_data.headers",
      "response_data.status_code",
      "response_data.body",
      "metadata.user_id",
      "metadata.session_id",
      "metadata.login_method"
    ]
  }
}
```

## Dynamic Filtering

The API supports dynamic filtering on any field with flexible operators. This allows you to query audit events using complex conditions without predefined filter parameters.

### Dynamic Filter Structure

```json
{
  "field": "string",           // Field name to filter on
  "operator": "string",        // Filter operator
  "value": "any",              // Filter value (not required for is_null/is_not_null)
  "case_sensitive": "boolean"  // Case sensitive matching (default: true)
}
```

### Supported Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `{"field": "event_type", "operator": "eq", "value": "user_login"}` |
| `ne` | Not equals | `{"field": "status", "operator": "ne", "value": "success"}` |
| `gt` | Greater than | `{"field": "timestamp", "operator": "gt", "value": "2024-01-01T00:00:00Z"}` |
| `gte` | Greater than or equal | `{"field": "response_data.status_code", "operator": "gte", "value": 400}` |
| `lt` | Less than | `{"field": "timestamp", "operator": "lt", "value": "2024-01-15T23:59:59Z"}` |
| `lte` | Less than or equal | `{"field": "response_data.status_code", "operator": "lte", "value": 299}` |
| `in` | In list | `{"field": "event_type", "operator": "in", "value": ["user_login", "user_logout"]}` |
| `not_in` | Not in list | `{"field": "event_type", "operator": "not_in", "value": ["system_event"]}` |
| `contains` | Contains substring | `{"field": "metadata.user_id", "operator": "contains", "value": "admin"}` |
| `not_contains` | Does not contain | `{"field": "user_agent", "operator": "not_contains", "value": "bot"}` |
| `starts_with` | Starts with | `{"field": "ip_address", "operator": "starts_with", "value": "192.168"}` |
| `ends_with` | Ends with | `{"field": "user_id", "operator": "ends_with", "value": "admin"}` |
| `is_null` | Is null | `{"field": "correlation_id", "operator": "is_null"}` |
| `is_not_null` | Is not null | `{"field": "session_id", "operator": "is_not_null"}` |
| `regex` | Regular expression | `{"field": "ip_address", "operator": "regex", "value": "^192\\.168\\."}` |

### Filter Groups

You can group multiple filters with logical operators (AND/OR):

```json
{
  "filters": [
    {
      "field": "event_type",
      "operator": "eq",
      "value": "user_login"
    },
    {
      "field": "status",
      "operator": "eq",
      "value": "failed"
    }
  ],
  "operator": "AND"
}
```

### Nested JSON Field Access

You can filter on nested JSON fields using dot notation:

```json
{
  "field": "request_data.method",
  "operator": "in",
  "value": ["POST", "PUT", "DELETE"]
}
```

```json
{
  "field": "metadata.user_id",
  "operator": "contains",
  "value": "admin"
}
```

### Complex Filter Examples

#### Find failed login attempts from internal network
```json
[
  {
    "field": "event_type",
    "operator": "eq",
    "value": "user_login"
  },
  {
    "field": "status",
    "operator": "eq",
    "value": "failed"
  },
  {
    "field": "ip_address",
    "operator": "starts_with",
    "value": "192.168"
  }
]
```

#### Find events with error status codes
```json
[
  {
    "field": "response_data.status_code",
    "operator": "gte",
    "value": 400
  }
]
```

#### Find admin user activities
```json
[
  {
    "field": "metadata.user_id",
    "operator": "contains",
    "value": "admin"
  }
]
```

#### Find events with missing correlation IDs
```json
[
  {
    "field": "correlation_id",
    "operator": "is_null"
  }
]
```

#### Complex filter group (OR condition)
```json
[
  {
    "filters": [
      {
        "field": "event_type",
        "operator": "eq",
        "value": "user_login"
      },
      {
        "field": "event_type",
        "operator": "eq",
        "value": "user_logout"
      }
    ],
    "operator": "OR"
  }
]
```

## Export Audit Events

**GET** `/api/v1/audit/events/export`

Export audit events in CSV or JSON format with the same filtering capabilities as the query endpoint.

**Query Parameters:**
- `format` (string): Export format - "json" or "csv" (default: "json")
- All standard and dynamic filtering parameters supported

**Example Request:**
```
GET /api/v1/audit/events/export?format=csv&start_date=2024-01-01T00:00:00Z&end_date=2024-01-15T23:59:59Z&dynamic_filters=[{"field":"event_type","operator":"eq","value":"user_login"}]
```

## Error Responses

### Validation Error (400)
```json
{
  "detail": "Invalid dynamic_filters JSON: Expecting ',' delimiter"
}
```

### Authorization Error (403)
```json
{
  "detail": "Insufficient permissions"
}
```

### Not Found Error (404)
```json
{
  "detail": "Audit event not found"
}
```

### Internal Server Error (500)
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

- **Create events**: 1000 requests per minute
- **Query events**: 300 requests per minute
- **Export events**: 10 requests per minute
- **Get single event**: 500 requests per minute

## SDK Examples

### Python SDK
```python
from audit_log_sdk import AuditLogClient

client = AuditLogClient(base_url="http://localhost:8000", api_key="your-api-key")

# Query with dynamic filters
filters = [
    {"field": "event_type", "operator": "eq", "value": "user_login"},
    {"field": "status", "operator": "ne", "value": "success"}
]

results = client.query_events(
    dynamic_filters=filters,
    page=1,
    size=10
)
```

### Go SDK
```go
import "github.com/your-org/audit-log-sdk"

client := auditlog.NewClient("http://localhost:8000", "your-api-key")

// Query with dynamic filters
filters := []auditlog.DynamicFilter{
    {Field: "event_type", Operator: "eq", Value: "user_login"},
    {Field: "status", Operator: "ne", Value: "success"},
}

results, err := client.QueryEvents(context.Background(), &auditlog.QueryOptions{
    DynamicFilters: filters,
    Page: 1,
    Size: 10,
})
```

## Best Practices

1. **Use standard filters** for common queries (event_type, status, user_id, etc.)
2. **Use dynamic filters** for complex or ad-hoc queries
3. **Combine filters efficiently** using filter groups for OR conditions
4. **Use case-insensitive matching** for user input fields
5. **Validate filter syntax** before sending requests
6. **Use pagination** for large result sets
7. **Cache filter information** using the `/filters/info` endpoint
8. **Monitor query performance** and optimize complex filters
