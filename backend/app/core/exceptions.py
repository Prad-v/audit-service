"""
Custom exceptions for the audit log framework.

This module defines all custom exceptions used throughout the application
with proper error codes and HTTP status codes.
"""

from typing import Any, Dict, Optional


class AuditLogException(Exception):
    """Base exception for audit log framework."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "audit_log_error",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AuditLogException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="validation_error",
            status_code=400,
            details=details,
        )


class AuthenticationError(AuditLogException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="authentication_error",
            status_code=401,
        )


class AuthorizationError(AuditLogException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            error_code="authorization_error",
            status_code=403,
        )


class NotFoundError(AuditLogException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            error_code="not_found",
            status_code=404,
        )


class ConflictError(AuditLogException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(
            message=message,
            error_code="conflict",
            status_code=409,
        )


class RateLimitError(AuditLogException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            error_code="rate_limit_exceeded",
            status_code=429,
        )


class DatabaseError(AuditLogException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            error_code="database_error",
            status_code=500,
        )


class CacheError(AuditLogException):
    """Raised when cache operations fail."""
    
    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(
            message=message,
            error_code="cache_error",
            status_code=500,
        )


class MessageQueueError(AuditLogException):
    """Raised when message queue operations fail."""
    
    def __init__(self, message: str = "Message queue operation failed"):
        super().__init__(
            message=message,
            error_code="message_queue_error",
            status_code=500,
        )


class ExportError(AuditLogException):
    """Raised when export operations fail."""
    
    def __init__(self, message: str = "Export operation failed"):
        super().__init__(
            message=message,
            error_code="export_error",
            status_code=500,
        )


class ConfigurationError(AuditLogException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration error"):
        super().__init__(
            message=message,
            error_code="configuration_error",
            status_code=500,
        )