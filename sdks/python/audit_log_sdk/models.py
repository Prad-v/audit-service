"""
Data models for the Audit Log Framework Python SDK.

This module contains all the data models used by the SDK, including
request/response models and enums.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


class EventType(str, Enum):
    """Audit event types."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_EVENT = "system_event"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    ERROR = "error"


class Severity(str, Enum):
    """Audit event severity levels."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class UserRole(str, Enum):
    """User roles in the system."""
    SYSTEM_ADMIN = "system_admin"
    TENANT_ADMIN = "tenant_admin"
    AUDIT_MANAGER = "audit_manager"
    AUDIT_VIEWER = "audit_viewer"
    API_USER = "api_user"


@dataclass_json
@dataclass
class AuditLogEvent:
    """Audit log event model."""
    id: str
    tenant_id: str
    event_type: EventType
    resource_type: str
    action: str
    severity: Severity
    description: str
    timestamp: datetime
    created_at: datetime
    user_id: Optional[str] = None
    resource_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass_json
@dataclass
class AuditLogEventCreate:
    """Model for creating audit log events."""
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


@dataclass_json
@dataclass
class AuditLogQuery:
    """Query parameters for filtering audit logs."""
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


@dataclass_json
@dataclass
class PaginatedAuditLogs:
    """Paginated audit logs response."""
    items: List[AuditLogEvent]
    total: int
    page: int
    size: int
    pages: int


@dataclass_json
@dataclass
class AuditLogSummary:
    """Audit log summary statistics."""
    total_count: int
    event_types: Dict[str, int]
    severities: Dict[str, int]
    resource_types: Dict[str, int]
    date_range: Dict[str, Optional[str]]


@dataclass_json
@dataclass
class AuditLogExport:
    """Audit log export response."""
    data: List[Dict[str, Any]]
    format: str
    count: int
    generated_at: datetime


@dataclass_json
@dataclass
class LoginRequest:
    """Login request model."""
    username: str
    password: str
    tenant_id: str


@dataclass_json
@dataclass
class TokenResponse:
    """Authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@dataclass_json
@dataclass
class RefreshTokenRequest:
    """Refresh token request model."""
    refresh_token: str


@dataclass_json
@dataclass
class UserCreate:
    """User creation model."""
    username: str
    email: str
    full_name: str
    password: str
    roles: List[UserRole]
    is_active: bool = True


@dataclass_json
@dataclass
class UserUpdate:
    """User update model."""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    roles: Optional[List[UserRole]] = None
    is_active: Optional[bool] = None


@dataclass_json
@dataclass
class UserResponse:
    """User response model."""
    id: str
    tenant_id: str
    username: str
    email: str
    full_name: str
    roles: List[UserRole]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


@dataclass_json
@dataclass
class APIKeyCreate:
    """API key creation model."""
    name: str
    permissions: List[str]
    expires_at: Optional[datetime] = None


@dataclass_json
@dataclass
class APIKeyResponse:
    """API key response model."""
    id: str
    tenant_id: str
    user_id: str
    name: str
    permissions: List[str]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    key: Optional[str] = None  # Only included when creating


@dataclass_json
@dataclass
class BatchAuditLogCreate:
    """Batch audit log creation model."""
    audit_logs: List[AuditLogEventCreate]


@dataclass_json
@dataclass
class ErrorResponse:
    """API error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass_json
@dataclass
class HealthResponse:
    """Health check response model."""
    status: str
    service: str
    timestamp: str
    version: str


# Utility functions for model conversion
def to_dict(obj: Any) -> Dict[str, Any]:
    """Convert a dataclass to dictionary, handling datetime serialization."""
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, list):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: to_dict(value) for key, value in obj.items()}
    else:
        return obj


def from_dict(data: Dict[str, Any], model_class: type) -> Any:
    """Convert dictionary to dataclass, handling datetime parsing."""
    if hasattr(model_class, 'from_dict'):
        return model_class.from_dict(data)
    else:
        return model_class(**data)


# Type aliases for convenience
AuditEvent = AuditLogEvent
AuditEventCreate = AuditLogEventCreate
AuditQuery = AuditLogQuery
AuditSummary = AuditLogSummary
PaginatedEvents = PaginatedAuditLogs