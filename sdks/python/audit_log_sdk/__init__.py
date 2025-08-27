"""
Audit Log Framework Python SDK

A comprehensive Python SDK for the Audit Log Framework API with async support,
authentication, and comprehensive error handling.
"""

from .client import AuditLogClient, AsyncAuditLogClient
from .models import (
    AuditLogEvent,
    AuditLogQuery,
    AuditLogSummary,
    PaginatedAuditLogs,
    EventType,
    Severity,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)
from .exceptions import (
    AuditLogSDKError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
)

__version__ = "1.0.0"
__author__ = "Audit Log Framework Team"
__email__ = "support@yourcompany.com"

__all__ = [
    # Clients
    "AuditLogClient",
    "AsyncAuditLogClient",
    
    # Models
    "AuditLogEvent",
    "AuditLogQuery", 
    "AuditLogSummary",
    "PaginatedAuditLogs",
    "EventType",
    "Severity",
    "LoginRequest",
    "TokenResponse",
    "UserCreate",
    "UserResponse",
    
    # Exceptions
    "AuditLogSDKError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]