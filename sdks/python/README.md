# Audit Log Framework Python SDK

A comprehensive Python SDK for the Audit Log Framework API with async support, authentication, and comprehensive error handling.

## Features

- **Synchronous and Asynchronous Clients**: Both sync and async clients for different use cases
- **Comprehensive Authentication**: Support for JWT tokens and API keys
- **Multi-tenant Support**: Built-in tenant isolation and management
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **Type Safety**: Full type hints and dataclass models for all API interactions
- **Error Handling**: Comprehensive exception hierarchy for different error types
- **Batch Operations**: Support for batch audit log creation for high-throughput scenarios

## Installation

```bash
pip install audit-log-sdk
```

For development dependencies:

```bash
pip install audit-log-sdk[dev]
```

## Quick Start

### Synchronous Client

```python
from audit_log_sdk import AuditLogClient, AuditLogEventCreate, EventType, Severity

# Initialize client with API key
client = AuditLogClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",
    tenant_id="your-tenant-id"
)

# Create an audit log event
event = AuditLogEventCreate(
    event_type=EventType.USER_ACTION,
    resource_type="user",
    action="login",
    severity=Severity.INFO,
    description="User logged in successfully",
    user_id="user-123",
    ip_address="192.168.1.1"
)

# Send the event
created_event = client.create_event(event)
print(f"Created event: {created_event.id}")

# Query events
from audit_log_sdk import AuditLogQuery
from datetime import datetime, timedelta

query = AuditLogQuery(
    start_date=datetime.now() - timedelta(days=7),
    event_types=[EventType.USER_ACTION],
    severities=[Severity.INFO, Severity.WARNING]
)

results = client.query_events(query, page=1, size=50)
print(f"Found {results.total} events")

# Close the client
client.close()
```

### Asynchronous Client

```python
import asyncio
from audit_log_sdk import AsyncAuditLogClient, AuditLogEventCreate, EventType, Severity

async def main():
    # Initialize async client
    async with AsyncAuditLogClient(
        base_url="http://localhost:8000",
        api_key="your-api-key",
        tenant_id="your-tenant-id"
    ) as client:
        
        # Create an audit log event
        event = AuditLogEventCreate(
            event_type=EventType.API_CALL,
            resource_type="api",
            action="create_user",
            severity=Severity.INFO,
            description="API call to create user",
            correlation_id="req-456"
        )
        
        # Send the event asynchronously
        created_event = await client.create_event(event)
        print(f"Created event: {created_event.id}")
        
        # Batch create events
        events = [
            AuditLogEventCreate(
                event_type=EventType.DATA_ACCESS,
                resource_type="database",
                action="select",
                severity=Severity.DEBUG,
                description=f"Database query {i}",
            )
            for i in range(10)
        ]
        
        batch_results = await client.create_events_batch(events)
        print(f"Created {len(batch_results)} events in batch")

# Run the async example
asyncio.run(main())
```

### Authentication with Username/Password

```python
from audit_log_sdk import AuditLogClient

client = AuditLogClient(base_url="http://localhost:8000")

# Login with credentials
token_response = client.login(
    username="admin",
    password="password",
    tenant_id="tenant-123"
)

print(f"Access token: {token_response.access_token}")

# Now you can use the client with the JWT token
events = client.query_events()
```

## API Reference

### Client Classes

#### `AuditLogClient`

Synchronous client for the Audit Log Framework API.

**Constructor Parameters:**
- `base_url` (str): Base URL of the Audit Log API
- `api_key` (str, optional): API key for authentication
- `tenant_id` (str, optional): Tenant ID (required when using API key)
- `timeout` (float): Request timeout in seconds (default: 30.0)
- `max_retries` (int): Maximum number of retry attempts (default: 3)
- `retry_delay` (float): Delay between retries in seconds (default: 1.0)

#### `AsyncAuditLogClient`

Asynchronous client with the same interface as `AuditLogClient` but with async methods.

### Data Models

#### `AuditLogEventCreate`

Model for creating audit log events.

```python
@dataclass
class AuditLogEventCreate:
    event_type: EventType
    resource_type: str
    action: str
    severity: Severity
    description: str
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    timestamp: Optional[datetime] = None
```

#### `AuditLogQuery`

Query parameters for filtering audit logs.

```python
@dataclass
class AuditLogQuery:
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[EventType]] = None
    resource_types: Optional[List[str]] = None
    resource_ids: Optional[List[str]] = None
    actions: Optional[List[str]] = None
    severities: Optional[List[Severity]] = None
    user_ids: Optional[List[str]] = None
    ip_addresses: Optional[List[str]] = None
    session_ids: Optional[List[str]] = None
    correlation_ids: Optional[List[str]] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "timestamp"
    sort_order: Optional[str] = "desc"
```

### Enums

#### `EventType`

```python
class EventType(str, Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_EVENT = "system_event"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    ERROR = "error"
```

#### `Severity`

```python
class Severity(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
```

### Exception Hierarchy

All SDK exceptions inherit from `AuditLogSDKError`:

- `AuthenticationError` (401): Authentication failed
- `AuthorizationError` (403): Insufficient permissions
- `ValidationError` (400): Request validation failed
- `NotFoundError` (404): Resource not found
- `RateLimitError` (429): Rate limit exceeded
- `ServerError` (5xx): Server-side errors
- `NetworkError`: Network communication issues
- `TimeoutError`: Request timeout
- `ConfigurationError`: SDK configuration issues

## Advanced Usage

### Custom Retry Configuration

```python
client = AuditLogClient(
    base_url="http://localhost:8000",
    api_key="your-api-key",
    tenant_id="your-tenant-id",
    max_retries=5,
    retry_delay=2.0,  # 2 seconds base delay
    timeout=60.0      # 60 seconds timeout
)
```

### Error Handling

```python
from audit_log_sdk.exceptions import (
    AuthenticationError,
    ValidationError,
    RateLimitError,
    ServerError
)

try:
    event = client.create_event(audit_event)
except AuthenticationError:
    print("Authentication failed - check your credentials")
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Details: {e.details}")
except RateLimitError as e:
    print(f"Rate limited - retry after {e.retry_after} seconds")
except ServerError:
    print("Server error - try again later")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Export Functionality

```python
# Export events as JSON
export_result = client.export_events(
    query=AuditLogQuery(
        start_date=datetime.now() - timedelta(days=30),
        event_types=[EventType.USER_ACTION]
    ),
    format="json"
)

print(f"Exported {export_result.count} events")
print(f"Generated at: {export_result.generated_at}")

# Save to file
import json
with open("audit_logs.json", "w") as f:
    json.dump(export_result.data, f, indent=2)
```

### Summary Statistics

```python
# Get summary statistics
summary = client.get_summary(
    query=AuditLogQuery(
        start_date=datetime.now() - timedelta(days=7)
    )
)

print(f"Total events: {summary.total_count}")
print(f"Event types: {summary.event_types}")
print(f"Severities: {summary.severities}")
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourcompany/audit-service.git
cd audit-service/sdks/python

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Run linting
black audit_log_sdk/
isort audit_log_sdk/
flake8 audit_log_sdk/

# Type checking
mypy audit_log_sdk/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=audit_log_sdk --cov-report=html

# Run only async tests
pytest -k "async"

# Run with verbose output
pytest -v
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact support@yourcompany.com or create an issue on GitHub.