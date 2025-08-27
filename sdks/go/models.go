package audit

import (
	"time"
)

// EventType represents the type of audit event
type EventType string

const (
	EventTypeAuthentication   EventType = "authentication"
	EventTypeAuthorization    EventType = "authorization"
	EventTypeDataAccess       EventType = "data_access"
	EventTypeDataModification EventType = "data_modification"
	EventTypeSystemEvent      EventType = "system_event"
	EventTypeUserAction       EventType = "user_action"
	EventTypeAPICall          EventType = "api_call"
	EventTypeError            EventType = "error"
)

// Severity represents the severity level of an audit event
type Severity string

const (
	SeverityCritical Severity = "critical"
	SeverityError    Severity = "error"
	SeverityWarning  Severity = "warning"
	SeverityInfo     Severity = "info"
	SeverityDebug    Severity = "debug"
)

// UserRole represents user roles in the system
type UserRole string

const (
	UserRoleSystemAdmin  UserRole = "system_admin"
	UserRoleTenantAdmin  UserRole = "tenant_admin"
	UserRoleAuditManager UserRole = "audit_manager"
	UserRoleAuditViewer  UserRole = "audit_viewer"
	UserRoleAPIUser      UserRole = "api_user"
)

// AuditLogEvent represents a complete audit log event
type AuditLogEvent struct {
	ID            string                 `json:"id"`
	TenantID      string                 `json:"tenant_id"`
	EventType     EventType              `json:"event_type"`
	ResourceType  string                 `json:"resource_type"`
	Action        string                 `json:"action"`
	Severity      Severity               `json:"severity"`
	Description   string                 `json:"description"`
	Timestamp     time.Time              `json:"timestamp"`
	CreatedAt     time.Time              `json:"created_at"`
	UserID        *string                `json:"user_id,omitempty"`
	ResourceID    *string                `json:"resource_id,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
	IPAddress     *string                `json:"ip_address,omitempty"`
	UserAgent     *string                `json:"user_agent,omitempty"`
	SessionID     *string                `json:"session_id,omitempty"`
	CorrelationID *string                `json:"correlation_id,omitempty"`
}

// AuditLogEventCreate represents the data needed to create an audit log event
type AuditLogEventCreate struct {
	EventType     EventType              `json:"event_type"`
	ResourceType  string                 `json:"resource_type"`
	Action        string                 `json:"action"`
	Severity      Severity               `json:"severity"`
	Description   string                 `json:"description"`
	ResourceID    *string                `json:"resource_id,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
	IPAddress     *string                `json:"ip_address,omitempty"`
	UserAgent     *string                `json:"user_agent,omitempty"`
	SessionID     *string                `json:"session_id,omitempty"`
	CorrelationID *string                `json:"correlation_id,omitempty"`
	Timestamp     *time.Time             `json:"timestamp,omitempty"`
}

// AuditLogQuery represents query parameters for filtering audit logs
type AuditLogQuery struct {
	StartDate      *time.Time  `json:"start_date,omitempty"`
	EndDate        *time.Time  `json:"end_date,omitempty"`
	EventTypes     []EventType `json:"event_types,omitempty"`
	ResourceTypes  []string    `json:"resource_types,omitempty"`
	ResourceIDs    []string    `json:"resource_ids,omitempty"`
	Actions        []string    `json:"actions,omitempty"`
	Severities     []Severity  `json:"severities,omitempty"`
	UserIDs        []string    `json:"user_ids,omitempty"`
	IPAddresses    []string    `json:"ip_addresses,omitempty"`
	SessionIDs     []string    `json:"session_ids,omitempty"`
	CorrelationIDs []string    `json:"correlation_ids,omitempty"`
	Search         *string     `json:"search,omitempty"`
	SortBy         *string     `json:"sort_by,omitempty"`
	SortOrder      *string     `json:"sort_order,omitempty"`
}

// PaginatedAuditLogs represents a paginated response of audit logs
type PaginatedAuditLogs struct {
	Items []AuditLogEvent `json:"items"`
	Total int             `json:"total"`
	Page  int             `json:"page"`
	Size  int             `json:"size"`
	Pages int             `json:"pages"`
}

// AuditLogSummary represents summary statistics for audit logs
type AuditLogSummary struct {
	TotalCount    int                    `json:"total_count"`
	EventTypes    map[string]int         `json:"event_types"`
	Severities    map[string]int         `json:"severities"`
	ResourceTypes map[string]int         `json:"resource_types"`
	DateRange     map[string]*time.Time  `json:"date_range"`
}

// AuditLogExport represents an export response
type AuditLogExport struct {
	Data        []map[string]interface{} `json:"data"`
	Format      string                   `json:"format"`
	Count       int                      `json:"count"`
	GeneratedAt time.Time                `json:"generated_at"`
}

// BatchAuditLogCreate represents a batch creation request
type BatchAuditLogCreate struct {
	AuditLogs []AuditLogEventCreate `json:"audit_logs"`
}

// LoginRequest represents a login request
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
	TenantID string `json:"tenant_id"`
}

// TokenResponse represents an authentication token response
type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
	TokenType    string `json:"token_type"`
}

// RefreshTokenRequest represents a refresh token request
type RefreshTokenRequest struct {
	RefreshToken string `json:"refresh_token"`
}

// UserCreate represents user creation data
type UserCreate struct {
	Username string     `json:"username"`
	Email    string     `json:"email"`
	FullName string     `json:"full_name"`
	Password string     `json:"password"`
	Roles    []UserRole `json:"roles"`
	IsActive bool       `json:"is_active"`
}

// UserUpdate represents user update data
type UserUpdate struct {
	Email    *string     `json:"email,omitempty"`
	FullName *string     `json:"full_name,omitempty"`
	Password *string     `json:"password,omitempty"`
	Roles    *[]UserRole `json:"roles,omitempty"`
	IsActive *bool       `json:"is_active,omitempty"`
}

// UserResponse represents a user response
type UserResponse struct {
	ID          string     `json:"id"`
	TenantID    string     `json:"tenant_id"`
	Username    string     `json:"username"`
	Email       string     `json:"email"`
	FullName    string     `json:"full_name"`
	Roles       []UserRole `json:"roles"`
	IsActive    bool       `json:"is_active"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
	LastLoginAt *time.Time `json:"last_login_at,omitempty"`
}

// APIKeyCreate represents API key creation data
type APIKeyCreate struct {
	Name        string     `json:"name"`
	Permissions []string   `json:"permissions"`
	ExpiresAt   *time.Time `json:"expires_at,omitempty"`
}

// APIKeyResponse represents an API key response
type APIKeyResponse struct {
	ID          string     `json:"id"`
	TenantID    string     `json:"tenant_id"`
	UserID      string     `json:"user_id"`
	Name        string     `json:"name"`
	Permissions []string   `json:"permissions"`
	ExpiresAt   *time.Time `json:"expires_at,omitempty"`
	IsActive    bool       `json:"is_active"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
	Key         *string    `json:"key,omitempty"` // Only included when creating
}

// ErrorResponse represents an API error response
type ErrorResponse struct {
	Error   string                 `json:"error"`
	Message string                 `json:"message"`
	Details map[string]interface{} `json:"details,omitempty"`
}

// HealthResponse represents a health check response
type HealthResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version"`
}

// QueryParams represents query parameters for API requests
type QueryParams struct {
	Page int `json:"page,omitempty"`
	Size int `json:"size,omitempty"`
}

// Helper functions for pointer types
func StringPtr(s string) *string {
	return &s
}

func TimePtr(t time.Time) *time.Time {
	return &t
}

func BoolPtr(b bool) *bool {
	return &b
}

func IntPtr(i int) *int {
	return &i
}

// Helper functions for creating common audit events
func NewUserActionEvent(action, description string) *AuditLogEventCreate {
	return &AuditLogEventCreate{
		EventType:   EventTypeUserAction,
		ResourceType: "user",
		Action:      action,
		Severity:    SeverityInfo,
		Description: description,
	}
}

func NewAPICallEvent(action, description string) *AuditLogEventCreate {
	return &AuditLogEventCreate{
		EventType:   EventTypeAPICall,
		ResourceType: "api",
		Action:      action,
		Severity:    SeverityInfo,
		Description: description,
	}
}

func NewDataAccessEvent(resourceType, action, description string) *AuditLogEventCreate {
	return &AuditLogEventCreate{
		EventType:   EventTypeDataAccess,
		ResourceType: resourceType,
		Action:      action,
		Severity:    SeverityInfo,
		Description: description,
	}
}

func NewErrorEvent(resourceType, action, description string) *AuditLogEventCreate {
	return &AuditLogEventCreate{
		EventType:   EventTypeError,
		ResourceType: resourceType,
		Action:      action,
		Severity:    SeverityError,
		Description: description,
	}
}