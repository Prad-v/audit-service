# Audit Log Framework Go SDK

A comprehensive Go SDK for the Audit Log Framework API with robust error handling, retry logic, and comprehensive type safety.

## Features

- **Type Safety**: Full Go struct definitions for all API interactions
- **Comprehensive Authentication**: Support for JWT tokens and API keys
- **Multi-tenant Support**: Built-in tenant isolation and management
- **Retry Logic**: Automatic retry with exponential backoff for failed requests
- **Error Handling**: Comprehensive error types for different failure scenarios
- **Context Support**: Full context.Context support for cancellation and timeouts
- **Batch Operations**: Support for batch audit log creation for high-throughput scenarios

## Installation

```bash
go get github.com/yourcompany/audit-service/sdk
```

## Quick Start

### API Key Authentication

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    audit "github.com/yourcompany/audit-service/sdk"
)

func main() {
    // Create client with API key
    client, err := audit.NewClientWithAPIKey(
        "http://localhost:8000",
        "your-api-key",
        "your-tenant-id",
    )
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    // Create an audit log event
    event := &audit.AuditLogEventCreate{
        EventType:    audit.EventTypeUserAction,
        ResourceType: "user",
        Action:       "login",
        Severity:     audit.SeverityInfo,
        Description:  "User logged in successfully",
        UserID:       audit.StringPtr("user-123"),
        IPAddress:    audit.StringPtr("192.168.1.1"),
    }

    createdEvent, err := client.CreateEvent(ctx, event)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Created event: %s\n", createdEvent.ID)
}
```

### JWT Authentication

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    audit "github.com/yourcompany/audit-service/sdk"
)

func main() {
    // Create client for JWT authentication
    client, err := audit.NewClientWithJWT("http://localhost:8000")
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    // Login with credentials
    tokenResp, err := client.Login(ctx, "admin", "password", "tenant-123")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Access token: %s\n", tokenResp.AccessToken)

    // Now you can use the client with the JWT token
    events, err := client.QueryEvents(ctx, nil, 1, 50)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Found %d events\n", events.Total)
}
```

### Batch Operations

```go
package main

import (
    "context"
    "fmt"
    "log"

    audit "github.com/yourcompany/audit-service/sdk"
)

func main() {
    client, err := audit.NewClientWithAPIKey(
        "http://localhost:8000",
        "your-api-key",
        "your-tenant-id",
    )
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    // Create multiple events in batch
    events := []audit.AuditLogEventCreate{
        {
            EventType:     audit.EventTypeAPICall,
            ResourceType:  "api",
            Action:        "create_user",
            Severity:      audit.SeverityInfo,
            Description:   "API call to create user 1",
            CorrelationID: audit.StringPtr("req-001"),
        },
        {
            EventType:     audit.EventTypeAPICall,
            ResourceType:  "api",
            Action:        "create_user",
            Severity:      audit.SeverityInfo,
            Description:   "API call to create user 2",
            CorrelationID: audit.StringPtr("req-002"),
        },
    }

    batchResults, err := client.CreateEventsBatch(ctx, events)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Created %d events in batch\n", len(batchResults))
}
```

## API Reference

### Client Configuration

#### `ClientConfig`

```go
type ClientConfig struct {
    BaseURL      string        // Base URL of the Audit Log API
    APIKey       string        // API key for authentication (optional)
    TenantID     string        // Tenant ID (required when using API key)
    Timeout      time.Duration // Request timeout (default: 30s)
    MaxRetries   int          // Maximum retry attempts (default: 3)
    RetryDelay   time.Duration // Base delay between retries (default: 1s)
    HTTPClient   *http.Client  // Custom HTTP client (optional)
}
```

#### Creating Clients

```go
// With full configuration
client, err := audit.NewClient(audit.ClientConfig{
    BaseURL:    "http://localhost:8000",
    APIKey:     "your-api-key",
    TenantID:   "your-tenant-id",
    Timeout:    60 * time.Second,
    MaxRetries: 5,
    RetryDelay: 2 * time.Second,
})

// With API key (simplified)
client, err := audit.NewClientWithAPIKey(
    "http://localhost:8000",
    "your-api-key", 
    "your-tenant-id",
)

// For JWT authentication (simplified)
client, err := audit.NewClientWithJWT("http://localhost:8000")
```

### Data Models

#### Event Types

```go
const (
    EventTypeAuthentication   = "authentication"
    EventTypeAuthorization    = "authorization"
    EventTypeDataAccess       = "data_access"
    EventTypeDataModification = "data_modification"
    EventTypeSystemEvent      = "system_event"
    EventTypeUserAction       = "user_action"
    EventTypeAPICall          = "api_call"
    EventTypeError            = "error"
)
```

#### Severity Levels

```go
const (
    SeverityCritical = "critical"
    SeverityError    = "error"
    SeverityWarning  = "warning"
    SeverityInfo     = "info"
    SeverityDebug    = "debug"
)
```

#### Creating Audit Events

```go
// Manual creation
event := &audit.AuditLogEventCreate{
    EventType:     audit.EventTypeUserAction,
    ResourceType:  "user",
    Action:        "login",
    Severity:      audit.SeverityInfo,
    Description:   "User logged in",
    UserID:        audit.StringPtr("user-123"),
    IPAddress:     audit.StringPtr("192.168.1.1"),
    UserAgent:     audit.StringPtr("Mozilla/5.0..."),
    SessionID:     audit.StringPtr("session-456"),
    CorrelationID: audit.StringPtr("req-789"),
    Metadata: map[string]interface{}{
        "login_method": "password",
        "device_type":  "desktop",
    },
}

// Using helper functions
userEvent := audit.NewUserActionEvent("login", "User logged in successfully")
apiEvent := audit.NewAPICallEvent("create_user", "API call to create user")
dataEvent := audit.NewDataAccessEvent("database", "select", "Database query executed")
errorEvent := audit.NewErrorEvent("api", "validation", "Request validation failed")
```

### Querying Events

```go
// Create query with filters
query := &audit.AuditLogQuery{
    StartDate:     audit.TimePtr(time.Now().AddDate(0, 0, -7)), // Last 7 days
    EndDate:       audit.TimePtr(time.Now()),
    EventTypes:    []audit.EventType{audit.EventTypeUserAction, audit.EventTypeAPICall},
    Severities:    []audit.Severity{audit.SeverityInfo, audit.SeverityWarning},
    ResourceTypes: []string{"user", "api"},
    Search:        audit.StringPtr("login"),
    SortBy:        audit.StringPtr("timestamp"),
    SortOrder:     audit.StringPtr("desc"),
}

// Query with pagination
results, err := client.QueryEvents(ctx, query, 1, 50) // page 1, 50 items
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Found %d total events, showing %d\n", results.Total, len(results.Items))
for _, event := range results.Items {
    fmt.Printf("Event: %s - %s\n", event.ID, event.Description)
}
```

### Error Handling

The SDK provides comprehensive error types for different scenarios:

```go
import (
    "errors"
    audit "github.com/yourcompany/audit-service/sdk"
)

event := &audit.AuditLogEventCreate{
    EventType:    audit.EventTypeUserAction,
    ResourceType: "user",
    Action:       "login",
    Severity:     audit.SeverityInfo,
    Description:  "User login attempt",
}

_, err := client.CreateEvent(ctx, event)
if err != nil {
    switch {
    case errors.As(err, &audit.AuthenticationError{}):
        fmt.Println("Authentication failed - check your credentials")
        
    case errors.As(err, &audit.ValidationError{}):
        fmt.Printf("Validation error: %s\n", err.Error())
        fmt.Printf("Details: %v\n", audit.GetErrorDetails(err))
        
    case errors.As(err, &audit.RateLimitError{}):
        rateLimitErr := err.(*audit.RateLimitError)
        fmt.Printf("Rate limited - retry after %d seconds\n", rateLimitErr.RetryAfter)
        
    case errors.As(err, &audit.ServerError{}):
        fmt.Println("Server error - try again later")
        
    case errors.As(err, &audit.NetworkError{}):
        fmt.Printf("Network error: %s\n", err.Error())
        
    default:
        fmt.Printf("Unexpected error: %s\n", err.Error())
    }
}
```

### Error Helper Functions

```go
// Check error types
if audit.IsRetryableError(err) {
    // Retry the operation
}

if audit.IsClientError(err) {
    // Handle client errors (4xx)
}

if audit.IsServerError(err) {
    // Handle server errors (5xx)
}

// Get error information
statusCode := audit.GetStatusCode(err)
errorCode := audit.GetErrorCode(err)
details := audit.GetErrorDetails(err)
```

### Export Functionality

```go
// Export events as JSON
export, err := client.ExportEvents(ctx, query, "json")
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Exported %d events\n", export.Count)
fmt.Printf("Generated at: %s\n", export.GeneratedAt)

// Save to file
file, err := os.Create("audit_logs.json")
if err != nil {
    log.Fatal(err)
}
defer file.Close()

encoder := json.NewEncoder(file)
encoder.SetIndent("", "  ")
if err := encoder.Encode(export.Data); err != nil {
    log.Fatal(err)
}
```

### Summary Statistics

```go
// Get summary statistics
summary, err := client.GetSummary(ctx, query)
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Total events: %d\n", summary.TotalCount)
fmt.Printf("Event types: %v\n", summary.EventTypes)
fmt.Printf("Severities: %v\n", summary.Severities)
fmt.Printf("Resource types: %v\n", summary.ResourceTypes)
```

### User Management

```go
// Create a new user (admin only)
newUser := &audit.UserCreate{
    Username: "newuser",
    Email:    "newuser@example.com",
    FullName: "New User",
    Password: "securepassword",
    Roles:    []audit.UserRole{audit.UserRoleAuditViewer},
    IsActive: true,
}

createdUser, err := client.CreateUser(ctx, newUser)
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Created user: %s (%s)\n", createdUser.Username, createdUser.Email)

// Get current user
currentUser, err := client.GetCurrentUser(ctx)
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Current user: %s\n", currentUser.Username)
```

### Context and Timeouts

```go
// Create context with timeout
ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
defer cancel()

// Create context with cancellation
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Use context in API calls
event, err := client.CreateEvent(ctx, auditEvent)
if err != nil {
    if errors.Is(err, context.DeadlineExceeded) {
        fmt.Println("Request timed out")
    } else if errors.Is(err, context.Canceled) {
        fmt.Println("Request was canceled")
    }
}
```

## Advanced Usage

### Custom HTTP Client

```go
import (
    "crypto/tls"
    "net/http"
    "time"
)

// Create custom HTTP client with custom settings
httpClient := &http.Client{
    Timeout: 60 * time.Second,
    Transport: &http.Transport{
        TLSClientConfig: &tls.Config{
            InsecureSkipVerify: true, // Only for development
        },
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
    },
}

client, err := audit.NewClient(audit.ClientConfig{
    BaseURL:    "https://api.yourcompany.com",
    APIKey:     "your-api-key",
    TenantID:   "your-tenant-id",
    HTTPClient: httpClient,
})
```

### Retry Configuration

```go
client, err := audit.NewClient(audit.ClientConfig{
    BaseURL:    "http://localhost:8000",
    APIKey:     "your-api-key",
    TenantID:   "your-tenant-id",
    MaxRetries: 5,                    // Retry up to 5 times
    RetryDelay: 2 * time.Second,      // Base delay of 2 seconds
    Timeout:    60 * time.Second,     // 60 second timeout
})
```

### Health Checks

```go
// Check API health
health, err := client.HealthCheck(ctx)
if err != nil {
    log.Fatal(err)
}

fmt.Printf("Service: %s\n", health.Service)
fmt.Printf("Status: %s\n", health.Status)
fmt.Printf("Version: %s\n", health.Version)
```

## Testing

```bash
# Run tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run tests with race detection
go test -race ./...

# Run benchmarks
go test -bench=. ./...
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`go test ./...`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please contact support@yourcompany.com or create an issue on GitHub.