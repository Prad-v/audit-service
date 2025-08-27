package audit

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// Client represents the Audit Log Framework Go SDK client
type Client struct {
	baseURL      string
	apiKey       string
	tenantID     string
	httpClient   *http.Client
	maxRetries   int
	retryDelay   time.Duration
	accessToken  string
	refreshToken string
}

// ClientConfig represents configuration options for the client
type ClientConfig struct {
	BaseURL      string
	APIKey       string
	TenantID     string
	Timeout      time.Duration
	MaxRetries   int
	RetryDelay   time.Duration
	HTTPClient   *http.Client
}

// NewClient creates a new Audit Log Framework client
func NewClient(config ClientConfig) (*Client, error) {
	if config.BaseURL == "" {
		return nil, NewConfigurationError("base_url is required")
	}

	if config.APIKey != "" && config.TenantID == "" {
		return nil, NewConfigurationError("tenant_id is required when using api_key")
	}

	// Set defaults
	if config.Timeout == 0 {
		config.Timeout = 30 * time.Second
	}
	if config.MaxRetries == 0 {
		config.MaxRetries = 3
	}
	if config.RetryDelay == 0 {
		config.RetryDelay = time.Second
	}

	httpClient := config.HTTPClient
	if httpClient == nil {
		httpClient = &http.Client{
			Timeout: config.Timeout,
		}
	}

	return &Client{
		baseURL:    strings.TrimSuffix(config.BaseURL, "/"),
		apiKey:     config.APIKey,
		tenantID:   config.TenantID,
		httpClient: httpClient,
		maxRetries: config.MaxRetries,
		retryDelay: config.RetryDelay,
	}, nil
}

// NewClientWithAPIKey creates a new client with API key authentication
func NewClientWithAPIKey(baseURL, apiKey, tenantID string) (*Client, error) {
	return NewClient(ClientConfig{
		BaseURL:  baseURL,
		APIKey:   apiKey,
		TenantID: tenantID,
	})
}

// NewClientWithJWT creates a new client for JWT authentication
func NewClientWithJWT(baseURL string) (*Client, error) {
	return NewClient(ClientConfig{
		BaseURL: baseURL,
	})
}

// buildURL constructs the full URL for an endpoint
func (c *Client) buildURL(endpoint string, params map[string]string) string {
	u := fmt.Sprintf("%s%s", c.baseURL, endpoint)
	
	if len(params) > 0 {
		values := url.Values{}
		for key, value := range params {
			if value != "" {
				values.Add(key, value)
			}
		}
		if len(values) > 0 {
			u += "?" + values.Encode()
		}
	}
	
	return u
}

// getHeaders returns the appropriate headers for requests
func (c *Client) getHeaders() map[string]string {
	headers := map[string]string{
		"Content-Type": "application/json",
		"User-Agent":   "audit-log-sdk-go/1.0.0",
	}

	// Add authentication headers
	if c.accessToken != "" {
		headers["Authorization"] = fmt.Sprintf("Bearer %s", c.accessToken)
	} else if c.apiKey != "" {
		headers["X-API-Key"] = c.apiKey
		if c.tenantID != "" {
			headers["X-Tenant-ID"] = c.tenantID
		}
	}

	return headers
}

// makeRequest performs an HTTP request with retry logic
func (c *Client) makeRequest(ctx context.Context, method, endpoint string, body interface{}, params map[string]string) (*http.Response, error) {
	url := c.buildURL(endpoint, params)
	
	var bodyReader io.Reader
	if body != nil {
		jsonBody, err := json.Marshal(body)
		if err != nil {
			return nil, NewValidationError(fmt.Sprintf("failed to marshal request body: %v", err))
		}
		bodyReader = bytes.NewReader(jsonBody)
	}

	var lastErr error
	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		// Reset body reader for retries
		if body != nil {
			jsonBody, _ := json.Marshal(body)
			bodyReader = bytes.NewReader(jsonBody)
		}

		req, err := http.NewRequestWithContext(ctx, method, url, bodyReader)
		if err != nil {
			return nil, NewNetworkError(fmt.Sprintf("failed to create request: %v", err), err)
		}

		// Set headers
		for key, value := range c.getHeaders() {
			req.Header.Set(key, value)
		}

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = NewNetworkError(fmt.Sprintf("request failed: %v", err), err)
			
			// Check if we should retry
			if attempt < c.maxRetries && IsRetryableError(lastErr) {
				time.Sleep(c.retryDelay * time.Duration(1<<attempt)) // Exponential backoff
				continue
			}
			return nil, lastErr
		}

		// Check for successful response
		if resp.StatusCode >= 200 && resp.StatusCode < 300 {
			return resp, nil
		}

		// Handle error response
		errorResp := &ErrorResponse{}
		if err := json.NewDecoder(resp.Body).Decode(errorResp); err != nil {
			errorResp = &ErrorResponse{
				Error:   "http_error",
				Message: fmt.Sprintf("HTTP %d: %s", resp.StatusCode, resp.Status),
			}
		}
		resp.Body.Close()

		lastErr = CreateErrorFromResponse(resp.StatusCode, errorResp)

		// Check if we should retry
		if attempt < c.maxRetries && IsRetryableError(lastErr) {
			time.Sleep(c.retryDelay * time.Duration(1<<attempt)) // Exponential backoff
			continue
		}

		return nil, lastErr
	}

	return nil, lastErr
}

// parseResponse parses the response body into the target struct
func (c *Client) parseResponse(resp *http.Response, target interface{}) error {
	defer resp.Body.Close()
	
	if target == nil {
		return nil
	}

	return json.NewDecoder(resp.Body).Decode(target)
}

// Authentication methods

// Login authenticates with username and password
func (c *Client) Login(ctx context.Context, username, password, tenantID string) (*TokenResponse, error) {
	loginReq := LoginRequest{
		Username: username,
		Password: password,
		TenantID: tenantID,
	}

	resp, err := c.makeRequest(ctx, "POST", "/api/v1/auth/login", loginReq, nil)
	if err != nil {
		return nil, err
	}

	var tokenResp TokenResponse
	if err := c.parseResponse(resp, &tokenResp); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse token response: %v", err))
	}

	// Store tokens
	c.accessToken = tokenResp.AccessToken
	c.refreshToken = tokenResp.RefreshToken

	return &tokenResp, nil
}

// RefreshToken refreshes the access token using the refresh token
func (c *Client) RefreshToken(ctx context.Context) (*TokenResponse, error) {
	if c.refreshToken == "" {
		return nil, NewAuthenticationError("no refresh token available")
	}

	refreshReq := RefreshTokenRequest{
		RefreshToken: c.refreshToken,
	}

	resp, err := c.makeRequest(ctx, "POST", "/api/v1/auth/refresh", refreshReq, nil)
	if err != nil {
		return nil, err
	}

	var tokenResp TokenResponse
	if err := c.parseResponse(resp, &tokenResp); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse token response: %v", err))
	}

	// Update tokens
	c.accessToken = tokenResp.AccessToken
	if tokenResp.RefreshToken != "" {
		c.refreshToken = tokenResp.RefreshToken
	}

	return &tokenResp, nil
}

// Logout logs out the user and clears tokens
func (c *Client) Logout(ctx context.Context) error {
	_, err := c.makeRequest(ctx, "POST", "/api/v1/auth/logout", nil, nil)
	
	// Clear tokens regardless of response
	c.accessToken = ""
	c.refreshToken = ""
	
	return err
}

// GetCurrentUser gets the current authenticated user information
func (c *Client) GetCurrentUser(ctx context.Context) (*UserResponse, error) {
	resp, err := c.makeRequest(ctx, "GET", "/api/v1/auth/me", nil, nil)
	if err != nil {
		return nil, err
	}

	var user UserResponse
	if err := c.parseResponse(resp, &user); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse user response: %v", err))
	}

	return &user, nil
}

// Audit log methods

// CreateEvent creates a single audit log event
func (c *Client) CreateEvent(ctx context.Context, event *AuditLogEventCreate) (*AuditLogEvent, error) {
	resp, err := c.makeRequest(ctx, "POST", "/api/v1/audit/events", event, nil)
	if err != nil {
		return nil, err
	}

	var createdEvent AuditLogEvent
	if err := c.parseResponse(resp, &createdEvent); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse event response: %v", err))
	}

	return &createdEvent, nil
}

// CreateEventsBatch creates multiple audit log events in batch
func (c *Client) CreateEventsBatch(ctx context.Context, events []AuditLogEventCreate) ([]AuditLogEvent, error) {
	batchReq := BatchAuditLogCreate{
		AuditLogs: events,
	}

	resp, err := c.makeRequest(ctx, "POST", "/api/v1/audit/events/batch", batchReq, nil)
	if err != nil {
		return nil, err
	}

	var createdEvents []AuditLogEvent
	if err := c.parseResponse(resp, &createdEvents); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse batch response: %v", err))
	}

	return createdEvents, nil
}

// GetEvent gets a single audit log event by ID
func (c *Client) GetEvent(ctx context.Context, eventID string) (*AuditLogEvent, error) {
	endpoint := fmt.Sprintf("/api/v1/audit/events/%s", eventID)
	
	resp, err := c.makeRequest(ctx, "GET", endpoint, nil, nil)
	if err != nil {
		return nil, err
	}

	var event AuditLogEvent
	if err := c.parseResponse(resp, &event); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse event response: %v", err))
	}

	return &event, nil
}

// QueryEvents queries audit log events with filtering and pagination
func (c *Client) QueryEvents(ctx context.Context, query *AuditLogQuery, page, size int) (*PaginatedAuditLogs, error) {
	params := map[string]string{
		"page": strconv.Itoa(page),
		"size": strconv.Itoa(size),
	}

	// Add query parameters
	if query != nil {
		if query.StartDate != nil {
			params["start_date"] = query.StartDate.Format(time.RFC3339)
		}
		if query.EndDate != nil {
			params["end_date"] = query.EndDate.Format(time.RFC3339)
		}
		if len(query.EventTypes) > 0 {
			eventTypes := make([]string, len(query.EventTypes))
			for i, et := range query.EventTypes {
				eventTypes[i] = string(et)
			}
			params["event_types"] = strings.Join(eventTypes, ",")
		}
		if len(query.ResourceTypes) > 0 {
			params["resource_types"] = strings.Join(query.ResourceTypes, ",")
		}
		if len(query.Severities) > 0 {
			severities := make([]string, len(query.Severities))
			for i, s := range query.Severities {
				severities[i] = string(s)
			}
			params["severities"] = strings.Join(severities, ",")
		}
		if query.Search != nil {
			params["search"] = *query.Search
		}
		if query.SortBy != nil {
			params["sort_by"] = *query.SortBy
		}
		if query.SortOrder != nil {
			params["sort_order"] = *query.SortOrder
		}
	}

	resp, err := c.makeRequest(ctx, "GET", "/api/v1/audit/events", nil, params)
	if err != nil {
		return nil, err
	}

	var results PaginatedAuditLogs
	if err := c.parseResponse(resp, &results); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse query response: %v", err))
	}

	return &results, nil
}

// GetSummary gets audit log summary statistics
func (c *Client) GetSummary(ctx context.Context, query *AuditLogQuery) (*AuditLogSummary, error) {
	params := make(map[string]string)

	if query != nil {
		if query.StartDate != nil {
			params["start_date"] = query.StartDate.Format(time.RFC3339)
		}
		if query.EndDate != nil {
			params["end_date"] = query.EndDate.Format(time.RFC3339)
		}
	}

	resp, err := c.makeRequest(ctx, "GET", "/api/v1/audit/summary", nil, params)
	if err != nil {
		return nil, err
	}

	var summary AuditLogSummary
	if err := c.parseResponse(resp, &summary); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse summary response: %v", err))
	}

	return &summary, nil
}

// ExportEvents exports audit log events in various formats
func (c *Client) ExportEvents(ctx context.Context, query *AuditLogQuery, format string) (*AuditLogExport, error) {
	params := map[string]string{
		"format": format,
	}

	if query != nil {
		if query.StartDate != nil {
			params["start_date"] = query.StartDate.Format(time.RFC3339)
		}
		if query.EndDate != nil {
			params["end_date"] = query.EndDate.Format(time.RFC3339)
		}
	}

	resp, err := c.makeRequest(ctx, "GET", "/api/v1/audit/events/export", nil, params)
	if err != nil {
		return nil, err
	}

	var export AuditLogExport
	if err := c.parseResponse(resp, &export); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse export response: %v", err))
	}

	return &export, nil
}

// User management methods

// CreateUser creates a new user (admin only)
func (c *Client) CreateUser(ctx context.Context, user *UserCreate) (*UserResponse, error) {
	resp, err := c.makeRequest(ctx, "POST", "/api/v1/auth/users", user, nil)
	if err != nil {
		return nil, err
	}

	var createdUser UserResponse
	if err := c.parseResponse(resp, &createdUser); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse user response: %v", err))
	}

	return &createdUser, nil
}

// GetUser gets user by ID
func (c *Client) GetUser(ctx context.Context, userID string) (*UserResponse, error) {
	endpoint := fmt.Sprintf("/api/v1/auth/users/%s", userID)
	
	resp, err := c.makeRequest(ctx, "GET", endpoint, nil, nil)
	if err != nil {
		return nil, err
	}

	var user UserResponse
	if err := c.parseResponse(resp, &user); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse user response: %v", err))
	}

	return &user, nil
}

// UpdateUser updates user information
func (c *Client) UpdateUser(ctx context.Context, userID string, userUpdate *UserUpdate) (*UserResponse, error) {
	endpoint := fmt.Sprintf("/api/v1/auth/users/%s", userID)
	
	resp, err := c.makeRequest(ctx, "PUT", endpoint, userUpdate, nil)
	if err != nil {
		return nil, err
	}

	var updatedUser UserResponse
	if err := c.parseResponse(resp, &updatedUser); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse user response: %v", err))
	}

	return &updatedUser, nil
}

// DeactivateUser deactivates a user account
func (c *Client) DeactivateUser(ctx context.Context, userID string) (*UserResponse, error) {
	endpoint := fmt.Sprintf("/api/v1/auth/users/%s", userID)
	
	resp, err := c.makeRequest(ctx, "DELETE", endpoint, nil, nil)
	if err != nil {
		return nil, err
	}

	var deactivatedUser UserResponse
	if err := c.parseResponse(resp, &deactivatedUser); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse user response: %v", err))
	}

	return &deactivatedUser, nil
}

// CreateAPIKey creates a new API key
func (c *Client) CreateAPIKey(ctx context.Context, apiKey *APIKeyCreate) (*APIKeyResponse, error) {
	resp, err := c.makeRequest(ctx, "POST", "/api/v1/auth/api-keys", apiKey, nil)
	if err != nil {
		return nil, err
	}

	var createdAPIKey APIKeyResponse
	if err := c.parseResponse(resp, &createdAPIKey); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse API key response: %v", err))
	}

	return &createdAPIKey, nil
}

// Health check

// HealthCheck performs a health check on the API service
func (c *Client) HealthCheck(ctx context.Context) (*HealthResponse, error) {
	resp, err := c.makeRequest(ctx, "GET", "/api/v1/health", nil, nil)
	if err != nil {
		return nil, err
	}

	var health HealthResponse
	if err := c.parseResponse(resp, &health); err != nil {
		return nil, NewValidationError(fmt.Sprintf("failed to parse health response: %v", err))
	}

	return &health, nil
}