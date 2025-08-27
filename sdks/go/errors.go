package audit

import (
	"fmt"
	"net/http"
)

// AuditError represents a base error for the audit SDK
type AuditError struct {
	Code       string                 `json:"code"`
	Message    string                 `json:"message"`
	Details    map[string]interface{} `json:"details,omitempty"`
	StatusCode int                    `json:"status_code,omitempty"`
	Err        error                  `json:"-"` // Original error, not serialized
}

func (e *AuditError) Error() string {
	if e.Code != "" {
		return fmt.Sprintf("%s: %s", e.Code, e.Message)
	}
	return e.Message
}

func (e *AuditError) Unwrap() error {
	return e.Err
}

// Specific error types
type AuthenticationError struct {
	*AuditError
}

type AuthorizationError struct {
	*AuditError
}

type ValidationError struct {
	*AuditError
}

type NotFoundError struct {
	*AuditError
}

type RateLimitError struct {
	*AuditError
	RetryAfter int `json:"retry_after,omitempty"`
}

type ServerError struct {
	*AuditError
}

type NetworkError struct {
	*AuditError
}

type TimeoutError struct {
	*AuditError
	TimeoutSeconds float64 `json:"timeout_seconds,omitempty"`
}

type ConfigurationError struct {
	*AuditError
}

// Error constructors
func NewAuditError(code, message string) *AuditError {
	return &AuditError{
		Code:    code,
		Message: message,
		Details: make(map[string]interface{}),
	}
}

func NewAuthenticationError(message string) *AuthenticationError {
	if message == "" {
		message = "Authentication failed"
	}
	return &AuthenticationError{
		AuditError: &AuditError{
			Code:       "authentication_error",
			Message:    message,
			StatusCode: http.StatusUnauthorized,
			Details:    make(map[string]interface{}),
		},
	}
}

func NewAuthorizationError(message string) *AuthorizationError {
	if message == "" {
		message = "Authorization failed"
	}
	return &AuthorizationError{
		AuditError: &AuditError{
			Code:       "authorization_error",
			Message:    message,
			StatusCode: http.StatusForbidden,
			Details:    make(map[string]interface{}),
		},
	}
}

func NewValidationError(message string) *ValidationError {
	if message == "" {
		message = "Validation failed"
	}
	return &ValidationError{
		AuditError: &AuditError{
			Code:       "validation_error",
			Message:    message,
			StatusCode: http.StatusBadRequest,
			Details:    make(map[string]interface{}),
		},
	}
}

func NewNotFoundError(message string) *NotFoundError {
	if message == "" {
		message = "Resource not found"
	}
	return &NotFoundError{
		AuditError: &AuditError{
			Code:       "not_found",
			Message:    message,
			StatusCode: http.StatusNotFound,
			Details:    make(map[string]interface{}),
		},
	}
}

func NewRateLimitError(message string, retryAfter int) *RateLimitError {
	if message == "" {
		message = "Rate limit exceeded"
	}
	return &RateLimitError{
		AuditError: &AuditError{
			Code:       "rate_limit_exceeded",
			Message:    message,
			StatusCode: http.StatusTooManyRequests,
			Details:    make(map[string]interface{}),
		},
		RetryAfter: retryAfter,
	}
}

func NewServerError(message string, statusCode int) *ServerError {
	if message == "" {
		message = "Internal server error"
	}
	if statusCode == 0 {
		statusCode = http.StatusInternalServerError
	}
	return &ServerError{
		AuditError: &AuditError{
			Code:       "server_error",
			Message:    message,
			StatusCode: statusCode,
			Details:    make(map[string]interface{}),
		},
	}
}

func NewNetworkError(message string, originalError error) *NetworkError {
	if message == "" {
		message = "Network error"
	}
	return &NetworkError{
		AuditError: &AuditError{
			Code:    "network_error",
			Message: message,
			Details: make(map[string]interface{}),
			Err:     originalError,
		},
	}
}

func NewTimeoutError(message string, timeoutSeconds float64) *TimeoutError {
	if message == "" {
		message = "Request timeout"
	}
	return &TimeoutError{
		AuditError: &AuditError{
			Code:       "timeout_error",
			Message:    message,
			StatusCode: http.StatusRequestTimeout,
			Details:    make(map[string]interface{}),
		},
		TimeoutSeconds: timeoutSeconds,
	}
}

func NewConfigurationError(message string) *ConfigurationError {
	if message == "" {
		message = "Configuration error"
	}
	return &ConfigurationError{
		AuditError: &AuditError{
			Code:    "configuration_error",
			Message: message,
			Details: make(map[string]interface{}),
		},
	}
}

// CreateErrorFromResponse creates an appropriate error from HTTP response
func CreateErrorFromResponse(statusCode int, errorResponse *ErrorResponse) error {
	message := errorResponse.Message
	if message == "" {
		message = "Unknown error"
	}

	code := errorResponse.Error
	if code == "" {
		code = "unknown_error"
	}

	details := errorResponse.Details
	if details == nil {
		details = make(map[string]interface{})
	}

	baseError := &AuditError{
		Code:       code,
		Message:    message,
		Details:    details,
		StatusCode: statusCode,
	}

	switch statusCode {
	case http.StatusBadRequest:
		return &ValidationError{AuditError: baseError}
	case http.StatusUnauthorized:
		return &AuthenticationError{AuditError: baseError}
	case http.StatusForbidden:
		return &AuthorizationError{AuditError: baseError}
	case http.StatusNotFound:
		return &NotFoundError{AuditError: baseError}
	case http.StatusRequestTimeout:
		return &TimeoutError{AuditError: baseError}
	case http.StatusTooManyRequests:
		// Try to extract retry_after from details
		retryAfter := 0
		if ra, ok := details["retry_after"].(float64); ok {
			retryAfter = int(ra)
		}
		return &RateLimitError{
			AuditError: baseError,
			RetryAfter: retryAfter,
		}
	case http.StatusInternalServerError, http.StatusBadGateway, http.StatusServiceUnavailable, http.StatusGatewayTimeout:
		return &ServerError{AuditError: baseError}
	default:
		return baseError
	}
}

// IsRetryableError checks if an error is retryable
func IsRetryableError(err error) bool {
	switch err.(type) {
	case *NetworkError, *TimeoutError, *ServerError:
		return true
	case *AuditError:
		auditErr := err.(*AuditError)
		return auditErr.StatusCode >= 500
	default:
		return false
	}
}

// IsClientError checks if an error is a client error (4xx)
func IsClientError(err error) bool {
	switch e := err.(type) {
	case *AuthenticationError, *AuthorizationError, *ValidationError, *NotFoundError, *RateLimitError:
		return true
	case *AuditError:
		return e.StatusCode >= 400 && e.StatusCode < 500
	default:
		return false
	}
}

// IsServerError checks if an error is a server error (5xx)
func IsServerError(err error) bool {
	switch e := err.(type) {
	case *ServerError:
		return true
	case *AuditError:
		return e.StatusCode >= 500
	default:
		return false
	}
}

// GetStatusCode extracts the HTTP status code from an error
func GetStatusCode(err error) int {
	switch e := err.(type) {
	case *AuthenticationError, *AuthorizationError, *ValidationError, *NotFoundError, *RateLimitError, *TimeoutError, *ServerError:
		return e.AuditError.StatusCode
	case *AuditError:
		return e.StatusCode
	default:
		return 0
	}
}

// GetErrorCode extracts the error code from an error
func GetErrorCode(err error) string {
	switch e := err.(type) {
	case *AuthenticationError, *AuthorizationError, *ValidationError, *NotFoundError, *RateLimitError, *TimeoutError, *ServerError, *NetworkError, *ConfigurationError:
		return e.AuditError.Code
	case *AuditError:
		return e.Code
	default:
		return "unknown_error"
	}
}

// GetErrorDetails extracts the error details from an error
func GetErrorDetails(err error) map[string]interface{} {
	switch e := err.(type) {
	case *AuthenticationError, *AuthorizationError, *ValidationError, *NotFoundError, *RateLimitError, *TimeoutError, *ServerError, *NetworkError, *ConfigurationError:
		return e.AuditError.Details
	case *AuditError:
		return e.Details
	default:
		return nil
	}
}