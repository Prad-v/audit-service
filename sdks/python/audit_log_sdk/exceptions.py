"""
Exception classes for the Audit Log Framework Python SDK.

This module defines all custom exceptions that can be raised by the SDK,
providing clear error handling and debugging information.
"""

from typing import Any, Dict, Optional


class AuditLogSDKError(Exception):
    """Base exception for all Audit Log SDK errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
    
    def __str__(self) -> str:
        if self.error_code:
            return f"{self.error_code}: {self.message}"
        return self.message
    
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message='{self.message}', "
            f"error_code='{self.error_code}', "
            f"status_code={self.status_code})"
        )


class AuthenticationError(AuditLogSDKError):
    """Raised when authentication fails."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        error_code: str = "authentication_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=401,
        )


class AuthorizationError(AuditLogSDKError):
    """Raised when authorization fails (insufficient permissions)."""
    
    def __init__(
        self,
        message: str = "Authorization failed",
        error_code: str = "authorization_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=403,
        )


class ValidationError(AuditLogSDKError):
    """Raised when request validation fails."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "validation_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=400,
        )


class NotFoundError(AuditLogSDKError):
    """Raised when a requested resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "not_found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=404,
        )


class RateLimitError(AuditLogSDKError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        error_code: str = "rate_limit_exceeded",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=429,
        )
        self.retry_after = retry_after


class ServerError(AuditLogSDKError):
    """Raised when the server encounters an internal error."""
    
    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "server_error",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=status_code,
        )


class NetworkError(AuditLogSDKError):
    """Raised when network communication fails."""
    
    def __init__(
        self,
        message: str = "Network error",
        error_code: str = "network_error",
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=None,
        )
        self.original_error = original_error


class TimeoutError(AuditLogSDKError):
    """Raised when a request times out."""
    
    def __init__(
        self,
        message: str = "Request timeout",
        error_code: str = "timeout_error",
        details: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[float] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=408,
        )
        self.timeout_seconds = timeout_seconds


class ConfigurationError(AuditLogSDKError):
    """Raised when SDK configuration is invalid."""
    
    def __init__(
        self,
        message: str = "Configuration error",
        error_code: str = "configuration_error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            details=details,
            status_code=None,
        )


def create_exception_from_response(
    status_code: int,
    error_data: Dict[str, Any],
) -> AuditLogSDKError:
    """Create appropriate exception from HTTP response."""
    
    message = error_data.get("message", "Unknown error")
    error_code = error_data.get("error", "unknown_error")
    details = error_data.get("details", {})
    
    # Map status codes to exception types
    exception_map = {
        400: ValidationError,
        401: AuthenticationError,
        403: AuthorizationError,
        404: NotFoundError,
        408: TimeoutError,
        429: RateLimitError,
        500: ServerError,
        502: ServerError,
        503: ServerError,
        504: ServerError,
    }
    
    exception_class = exception_map.get(status_code, AuditLogSDKError)
    
    # Handle special cases
    if status_code == 429:
        retry_after = error_data.get("retry_after")
        return RateLimitError(
            message=message,
            error_code=error_code,
            details=details,
            retry_after=retry_after,
        )
    
    return exception_class(
        message=message,
        error_code=error_code,
        details=details,
    )


# Exception hierarchy for easy catching
class ClientError(AuditLogSDKError):
    """Base class for 4xx client errors."""
    pass


class ServerErrorBase(AuditLogSDKError):
    """Base class for 5xx server errors."""
    pass


# Update specific exceptions to inherit from appropriate base classes
AuthenticationError.__bases__ = (ClientError,)
AuthorizationError.__bases__ = (ClientError,)
ValidationError.__bases__ = (ClientError,)
NotFoundError.__bases__ = (ClientError,)
RateLimitError.__bases__ = (ClientError,)
ServerError.__bases__ = (ServerErrorBase,)