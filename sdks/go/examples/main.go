package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	audit "github.com/yourcompany/audit-service/sdk"
)

func main() {
	fmt.Println("Audit Log Framework Go SDK Examples")
	fmt.Println("===================================")

	// Run examples
	apiKeyExample()
	jwtExample()
	batchExample()
	queryExample()
	errorHandlingExample()
	exportExample()

	fmt.Println("\n===================================")
	fmt.Println("Examples completed!")
	fmt.Println("\nNote: These examples assume the Audit Log API is running at http://localhost:8000")
	fmt.Println("Make sure to replace 'your-api-key' and 'your-tenant-id' with actual values.")
}

func apiKeyExample() {
	fmt.Println("\n=== API Key Authentication Example ===")

	// Create client with API key
	client, err := audit.NewClientWithAPIKey(
		"http://localhost:8000",
		"your-api-key",
		"your-tenant-id",
	)
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	ctx := context.Background()

	// Create a single audit log event
	event := &audit.AuditLogEventCreate{
		EventType:     audit.EventTypeUserAction,
		ResourceType:  "user",
		Action:        "login",
		Severity:      audit.SeverityInfo,
		Description:   "User logged in successfully",
		UserID:        audit.StringPtr("user-123"),
		IPAddress:     audit.StringPtr("192.168.1.1"),
		UserAgent:     audit.StringPtr("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
		SessionID:     audit.StringPtr("session-456"),
		CorrelationID: audit.StringPtr("req-789"),
		Metadata: map[string]interface{}{
			"login_method": "password",
			"device_type":  "desktop",
		},
	}

	createdEvent, err := client.CreateEvent(ctx, event)
	if err != nil {
		fmt.Printf("✗ Failed to create event: %v\n", err)
		return
	}

	fmt.Printf("✓ Created event: %s\n", createdEvent.ID)

	// Get current user info
	user, err := client.GetCurrentUser(ctx)
	if err != nil {
		fmt.Printf("✗ Failed to get current user: %v\n", err)
		return
	}

	fmt.Printf("✓ Authenticated as: %s (%s)\n", user.Username, user.Email)
}

func jwtExample() {
	fmt.Println("\n=== JWT Authentication Example ===")

	// Create client for JWT authentication
	client, err := audit.NewClientWithJWT("http://localhost:8000")
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	ctx := context.Background()

	// Login with credentials
	tokenResp, err := client.Login(ctx, "admin", "password", "tenant-123")
	if err != nil {
		fmt.Printf("✗ Login failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Login successful, token type: %s\n", tokenResp.TokenType)

	// Now use the client with JWT token
	user, err := client.GetCurrentUser(ctx)
	if err != nil {
		fmt.Printf("✗ Failed to get current user: %v\n", err)
		return
	}

	fmt.Printf("✓ Authenticated as: %s\n", user.Username)

	// Logout
	err = client.Logout(ctx)
	if err != nil {
		fmt.Printf("✗ Logout failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Logged out successfully\n")
}

func batchExample() {
	fmt.Println("\n=== Batch Operations Example ===")

	client, err := audit.NewClientWithAPIKey(
		"http://localhost:8000",
		"your-api-key",
		"your-tenant-id",
	)
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
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
			Metadata: map[string]interface{}{
				"batch_id":   "batch-001",
				"user_count": 1,
			},
		},
		{
			EventType:     audit.EventTypeAPICall,
			ResourceType:  "api",
			Action:        "create_user",
			Severity:      audit.SeverityInfo,
			Description:   "API call to create user 2",
			CorrelationID: audit.StringPtr("req-002"),
			Metadata: map[string]interface{}{
				"batch_id":   "batch-001",
				"user_count": 2,
			},
		},
		{
			EventType:     audit.EventTypeAPICall,
			ResourceType:  "api",
			Action:        "create_user",
			Severity:      audit.SeverityInfo,
			Description:   "API call to create user 3",
			CorrelationID: audit.StringPtr("req-003"),
			Metadata: map[string]interface{}{
				"batch_id":   "batch-001",
				"user_count": 3,
			},
		},
	}

	batchResults, err := client.CreateEventsBatch(ctx, events)
	if err != nil {
		fmt.Printf("✗ Batch creation failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Created %d events in batch\n", len(batchResults))
}

func queryExample() {
	fmt.Println("\n=== Query Events Example ===")

	client, err := audit.NewClientWithAPIKey(
		"http://localhost:8000",
		"your-api-key",
		"your-tenant-id",
	)
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	ctx := context.Background()

	// Create query with filters
	query := &audit.AuditLogQuery{
		StartDate:     audit.TimePtr(time.Now().AddDate(0, 0, -7)), // Last 7 days
		EndDate:       audit.TimePtr(time.Now()),
		EventTypes:    []audit.EventType{audit.EventTypeUserAction, audit.EventTypeAPICall},
		Severities:    []audit.Severity{audit.SeverityInfo, audit.SeverityWarning, audit.SeverityError},
		ResourceTypes: []string{"user", "api"},
		SortBy:        audit.StringPtr("timestamp"),
		SortOrder:     audit.StringPtr("desc"),
	}

	// Query events with pagination
	results, err := client.QueryEvents(ctx, query, 1, 10)
	if err != nil {
		fmt.Printf("✗ Query failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Found %d total events (%d on this page)\n", results.Total, len(results.Items))

	// Get summary statistics
	summary, err := client.GetSummary(ctx, query)
	if err != nil {
		fmt.Printf("✗ Summary failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Summary: %d total events\n", summary.TotalCount)
	fmt.Printf("  Event types: %v\n", summary.EventTypes)
	fmt.Printf("  Severities: %v\n", summary.Severities)
}

func errorHandlingExample() {
	fmt.Println("\n=== Error Handling Example ===")

	// Create client with invalid API key
	client, err := audit.NewClientWithAPIKey(
		"http://localhost:8000",
		"invalid-key", // Intentionally invalid
		"test-tenant",
	)
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	ctx := context.Background()

	// This should fail with authentication error
	event := &audit.AuditLogEventCreate{
		EventType:   audit.EventTypeSystemEvent,
		ResourceType: "test",
		Action:      "test",
		Severity:    audit.SeverityDebug,
		Description: "Test event",
	}

	_, err = client.CreateEvent(ctx, event)
	if err != nil {
		switch {
		case audit.IsClientError(err):
			fmt.Printf("✓ Caught client error: %s\n", err.Error())
			fmt.Printf("  Error code: %s\n", audit.GetErrorCode(err))
			fmt.Printf("  Status code: %d\n", audit.GetStatusCode(err))

			// Handle specific error types
			if authErr, ok := err.(*audit.AuthenticationError); ok {
				fmt.Printf("  Authentication error details: %v\n", authErr.Details)
			}

		case audit.IsServerError(err):
			fmt.Printf("✓ Caught server error: %s\n", err.Error())
			fmt.Printf("  Status code: %d\n", audit.GetStatusCode(err))

		case audit.IsRetryableError(err):
			fmt.Printf("✓ Caught retryable error: %s\n", err.Error())
			fmt.Println("  This error can be retried")

		default:
			fmt.Printf("✗ Unexpected error: %s\n", err.Error())
		}
	}
}

func exportExample() {
	fmt.Println("\n=== Export Example ===")

	client, err := audit.NewClientWithAPIKey(
		"http://localhost:8000",
		"your-api-key",
		"your-tenant-id",
	)
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	ctx := context.Background()

	// Create query for export
	query := &audit.AuditLogQuery{
		StartDate:  audit.TimePtr(time.Now().AddDate(0, 0, -1)), // Last day
		EndDate:    audit.TimePtr(time.Now()),
		EventTypes: []audit.EventType{audit.EventTypeAPICall},
	}

	// Export events as JSON
	export, err := client.ExportEvents(ctx, query, "json")
	if err != nil {
		fmt.Printf("✗ Export failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Exported %d events\n", export.Count)
	fmt.Printf("  Format: %s\n", export.Format)
	fmt.Printf("  Generated at: %s\n", export.GeneratedAt.Format(time.RFC3339))

	// Save to file
	filename := "audit_logs_export.json"
	file, err := os.Create(filename)
	if err != nil {
		fmt.Printf("✗ Failed to create file: %v\n", err)
		return
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	if err := encoder.Encode(export.Data); err != nil {
		fmt.Printf("✗ Failed to write file: %v\n", err)
		return
	}

	fmt.Printf("✓ Saved export to %s\n", filename)
}

// Helper function to demonstrate context usage
func contextExample() {
	fmt.Println("\n=== Context Example ===")

	client, err := audit.NewClientWithAPIKey(
		"http://localhost:8000",
		"your-api-key",
		"your-tenant-id",
	)
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	event := &audit.AuditLogEventCreate{
		EventType:   audit.EventTypeUserAction,
		ResourceType: "user",
		Action:      "test",
		Severity:    audit.SeverityInfo,
		Description: "Test event with timeout",
	}

	_, err = client.CreateEvent(ctx, event)
	if err != nil {
		if err == context.DeadlineExceeded {
			fmt.Println("✓ Request timed out as expected")
		} else {
			fmt.Printf("✗ Unexpected error: %v\n", err)
		}
	} else {
		fmt.Println("✓ Event created successfully")
	}
}

// Helper function to demonstrate health check
func healthCheckExample() {
	fmt.Println("\n=== Health Check Example ===")

	client, err := audit.NewClientWithJWT("http://localhost:8000")
	if err != nil {
		fmt.Printf("✗ Failed to create client: %v\n", err)
		return
	}

	ctx := context.Background()

	health, err := client.HealthCheck(ctx)
	if err != nil {
		fmt.Printf("✗ Health check failed: %v\n", err)
		return
	}

	fmt.Printf("✓ Service: %s\n", health.Service)
	fmt.Printf("  Status: %s\n", health.Status)
	fmt.Printf("  Version: %s\n", health.Version)
	fmt.Printf("  Timestamp: %s\n", health.Timestamp)
}