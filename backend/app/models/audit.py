"""
Audit log Pydantic models for the audit log framework.

This module contains all Pydantic models for audit log data validation,
serialization, and API request/response handling.
"""

import uuid
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import UUID4

from app.models.base import PaginatedResponse


class AuditEventStatus(str, Enum):
    """Audit event status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class AuditEventType(str, Enum):
    """Common audit event types."""
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    RESOURCE_CREATE = "resource.create"
    RESOURCE_READ = "resource.read"
    RESOURCE_UPDATE = "resource.update"
    RESOURCE_DELETE = "resource.delete"
    PERMISSION_GRANT = "permission.grant"
    PERMISSION_REVOKE = "permission.revoke"
    API_ACCESS = "api.access"
    DATA_EXPORT = "data.export"
    SYSTEM_CONFIG = "system.config"
    SECURITY_ALERT = "security.alert"


class AuditAction(str, Enum):
    """Common audit actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    GRANT = "grant"
    REVOKE = "revoke"
    EXPORT = "export"
    IMPORT = "import"
    CONFIGURE = "configure"
    EXECUTE = "execute"


class BaseAuditModel(BaseModel):
    """Base model for audit-related data."""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        from_attributes = True


class AuditEventCreate(BaseAuditModel):
    """Model for creating audit events."""
    
    event_type: str = Field(..., description="Type of audit event", max_length=100)
    user_id: Optional[str] = Field(None, description="User ID who performed the action", max_length=255)
    session_id: Optional[str] = Field(None, description="Session ID", max_length=255)
    ip_address: Optional[Union[IPv4Address, IPv6Address, str]] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    resource_type: Optional[str] = Field(None, description="Type of resource affected", max_length=100)
    resource_id: Optional[str] = Field(None, description="ID of the resource affected", max_length=255)
    action: str = Field(..., description="Action performed", max_length=100)
    status: AuditEventStatus = Field(AuditEventStatus.SUCCESS, description="Status of the action")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Request data (sanitized)")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response data (sanitized)")
    metadata: Optional[Union[Dict[str, Any], Any]] = Field(None, description="Additional metadata")
    tenant_id: str = Field(..., description="Tenant ID", max_length=255)
    service_name: str = Field(..., description="Name of the service", max_length=100)
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request tracing", max_length=255)
    retention_period_days: int = Field(90, description="Retention period in days", ge=1, le=2555)
    
    @validator('ip_address', pre=True)
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                # Try to parse as IPv4 or IPv6
                from ipaddress import ip_address
                ip_address(v)
                return v
            except ValueError:
                # If not a valid IP, return as string (might be hostname)
                return v
        return str(v)
    
    @validator('request_data', 'response_data', 'metadata')
    def validate_json_data(cls, v):
        """Validate JSON data fields."""
        if v is None:
            return v
        if not isinstance(v, dict):
            raise ValueError("Must be a dictionary")
        return v
    
    @validator('retention_period_days')
    def validate_retention_period(cls, v):
        """Validate retention period is within allowed range."""
        if v < 1 or v > 2555:  # 7 years max
            raise ValueError("Retention period must be between 1 and 2555 days")
        return v


class AuditEventUpdate(BaseAuditModel):
    """Model for updating audit events (limited fields)."""
    
    status: Optional[AuditEventStatus] = None
    response_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditEventResponse(BaseAuditModel):
    """Model for audit event responses."""
    
    audit_id: UUID4 = Field(..., description="Unique audit event ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: str = Field(..., description="Type of audit event")
    user_id: Optional[str] = Field(None, description="User ID who performed the action")
    session_id: Optional[str] = Field(None, description="Session ID")
    ip_address: Optional[Union[str, IPv4Address, IPv6Address]] = Field(None, description="IP address of the user")
    user_agent: Optional[str] = Field(None, description="User agent string")
    resource_type: Optional[str] = Field(None, description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="ID of the resource affected")
    action: str = Field(..., description="Action performed")
    status: AuditEventStatus = Field(..., description="Status of the action")
    request_data: Optional[Dict[str, Any]] = Field(None, description="Request data")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    metadata: Optional[Union[Dict[str, Any], Any]] = Field(None, description="Additional metadata")
    tenant_id: str = Field(..., description="Tenant ID")
    service_name: str = Field(..., description="Name of the service")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    retention_period_days: int = Field(..., description="Retention period in days")
    created_at: datetime = Field(..., description="Record creation timestamp")
    partition_date: date = Field(..., description="Partition date for the record")


class AuditEventBatchCreate(BaseAuditModel):
    """Model for batch audit event creation."""
    
    events: List[AuditEventCreate] = Field(..., description="List of audit events to create", min_items=1, max_items=1000)
    
    @validator('events')
    def validate_events_limit(cls, v):
        """Validate batch size limits."""
        if len(v) > 1000:
            raise ValueError("Batch size cannot exceed 1000 events")
        return v


class AuditEventBatchResponse(BaseAuditModel):
    """Model for batch audit event creation response."""
    
    created_count: int = Field(..., description="Number of events successfully created")
    failed_count: int = Field(..., description="Number of events that failed to create")
    created_ids: List[UUID4] = Field(..., description="List of created audit event IDs")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors for failed events")


class FilterOperator(str, Enum):
    """Supported filter operators for dynamic filtering."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX = "regex"


class DynamicFilter(BaseModel):
    """Dynamic filter for any field with flexible operators."""
    field: str = Field(..., description="Field name to filter on (supports dot notation for nested fields)")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Optional[Union[str, int, float, bool, List[Any]]] = Field(None, description="Filter value (not required for is_null/is_not_null)")
    case_sensitive: bool = Field(True, description="Case sensitive matching (for string fields)")

    @validator('field')
    def validate_field(cls, v):
        """Validate field name."""
        if not v or not v.strip():
            raise ValueError("Field name cannot be empty")
        return v.strip()

    @root_validator(skip_on_failure=True)
    def validate_value_for_operator(cls, values):
        """Validate that value is provided for operators that require it."""
        operator = values.get('operator')
        value = values.get('value')
        
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            if value is not None:
                raise ValueError(f"Value should not be provided for operator '{operator}'")
        else:
            if value is None:
                raise ValueError(f"Value is required for operator '{operator}'")
        
        return values

    class Config:
        json_schema_extra = {
            "example": {
                "field": "event_type",
                "operator": "eq",
                "value": "user_login",
                "case_sensitive": True
            }
        }


class DynamicFilterGroup(BaseModel):
    """Group of dynamic filters with logical operator."""
    filters: List[DynamicFilter] = Field(..., description="List of filters")
    operator: str = Field("AND", description="Logical operator to combine filters (AND/OR)")

    @validator('operator')
    def validate_operator(cls, v):
        """Validate logical operator."""
        if v.upper() not in ['AND', 'OR']:
            raise ValueError("Operator must be 'AND' or 'OR'")
        return v.upper()

    @validator('filters')
    def validate_filters(cls, v):
        """Validate that at least one filter is provided."""
        if not v:
            raise ValueError("At least one filter must be provided")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "filters": [
                    {"field": "event_type", "operator": "eq", "value": "user_login"},
                    {"field": "status", "operator": "eq", "value": "success"}
                ],
                "operator": "AND"
            }
        }


class AuditEventQuery(BaseAuditModel):
    """Model for audit event query parameters."""
    
    # Time range filters
    start_time: Optional[datetime] = Field(None, description="Start time for query range")
    end_time: Optional[datetime] = Field(None, description="End time for query range")
    
    # Entity filters
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    service_name: Optional[str] = Field(None, description="Filter by service name")
    
    # Event filters
    event_type: Optional[str] = Field(None, description="Filter by event type")
    action: Optional[str] = Field(None, description="Filter by action")
    status: Optional[AuditEventStatus] = Field(None, description="Filter by status")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    
    # Correlation and session
    correlation_id: Optional[str] = Field(None, description="Filter by correlation ID")
    session_id: Optional[str] = Field(None, description="Filter by session ID")
    
    # Network filters
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    
    # Dynamic filters for flexible field querying
    dynamic_filters: Optional[List[DynamicFilter]] = Field(None, description="Dynamic filters for any field")
    filter_groups: Optional[List[DynamicFilterGroup]] = Field(None, description="Groups of dynamic filters")
    
    # Pagination
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(50, description="Page size", ge=1, le=1000)
    
    # Sorting
    sort_by: str = Field("timestamp", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort order."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v.lower()
    
    @root_validator(skip_on_failure=True)
    def validate_time_range(cls, values):
        """Validate time range parameters."""
        start_time = values.get('start_time')
        end_time = values.get('end_time')
        
        if start_time and end_time and start_time >= end_time:
            raise ValueError("start_time must be before end_time")
        
        return values

    @root_validator(skip_on_failure=True)
    def validate_dynamic_filters(cls, values):
        """Validate dynamic filters."""
        dynamic_filters = values.get('dynamic_filters')
        filter_groups = values.get('filter_groups')
        
        # Only prevent use of query parameter fields, not database fields
        reserved_fields = {
            'page', 'page_size', 'sort_by', 'sort_order', 'dynamic_filters', 'filter_groups'
        }
        
        if dynamic_filters:
            for filter_item in dynamic_filters:
                if filter_item.field in reserved_fields:
                    raise ValueError(f"Field '{filter_item.field}' is reserved. Use standard filter parameters instead.")
        
        if filter_groups:
            for group in filter_groups:
                for filter_item in group.filters:
                    if filter_item.field in reserved_fields:
                        raise ValueError(f"Field '{filter_item.field}' is reserved. Use standard filter parameters instead.")
        
        return values


class AuditEventQueryResponse(PaginatedResponse[AuditEventResponse]):
    """Model for audit event query response."""
    
    # Inherits all fields from PaginatedResponse[AuditEventResponse]
    # items: List[AuditEventResponse]
    # total_count: int
    # page: int
    # page_size: int
    # total_pages: int
    # has_next: bool
    # has_previous: bool


class AuditEventExport(BaseAuditModel):
    """Model for audit event export parameters."""
    
    query: AuditEventQuery = Field(..., description="Query parameters for export")
    format: str = Field("csv", description="Export format (csv, json)")
    include_headers: bool = Field(True, description="Include headers in CSV export")
    max_records: int = Field(100000, description="Maximum records to export", le=100000)
    
    @validator('format')
    def validate_format(cls, v):
        """Validate export format."""
        if v.lower() not in ['csv', 'json']:
            raise ValueError("Format must be 'csv' or 'json'")
        return v.lower()


class AuditEventExportResponse(BaseAuditModel):
    """Model for audit event export response."""
    
    export_id: UUID4 = Field(..., description="Export job ID")
    status: str = Field(..., description="Export status")
    download_url: Optional[str] = Field(None, description="Download URL when ready")
    created_at: datetime = Field(..., description="Export creation time")
    expires_at: Optional[datetime] = Field(None, description="Download URL expiration time")
    record_count: Optional[int] = Field(None, description="Number of records exported")


class AuditStatistics(BaseAuditModel):
    """Model for audit statistics."""
    
    tenant_id: str = Field(..., description="Tenant ID")
    stats_date: date = Field(..., description="Statistics date")
    total_events: int = Field(..., description="Total events for the day")
    unique_users: int = Field(..., description="Number of unique users")
    success_count: int = Field(..., description="Number of successful events")
    error_count: int = Field(..., description="Number of error events")
    warning_count: int = Field(..., description="Number of warning events")
    top_event_types: List[Dict[str, Any]] = Field(..., description="Top event types with counts")
    top_actions: List[Dict[str, Any]] = Field(..., description="Top actions with counts")
    hourly_distribution: List[Dict[str, Any]] = Field(..., description="Hourly event distribution")


class AuditStatisticsQuery(BaseAuditModel):
    """Model for audit statistics query parameters."""
    
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    start_date: date = Field(..., description="Start date for statistics")
    end_date: date = Field(..., description="End date for statistics")
    group_by: str = Field("day", description="Grouping period (day, week, month)")
    
    @validator('group_by')
    def validate_group_by(cls, v):
        """Validate group by parameter."""
        if v not in ['day', 'week', 'month']:
            raise ValueError("group_by must be 'day', 'week', or 'month'")
        return v
    
    @root_validator(skip_on_failure=True)
    def validate_date_range(cls, values):
        """Validate date range."""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValueError("start_date must be before or equal to end_date")
        
        return values


class AuditStatisticsResponse(BaseAuditModel):
    """Model for audit statistics response."""
    
    statistics: List[AuditStatistics] = Field(..., description="List of audit statistics")
    summary: Dict[str, Any] = Field(..., description="Summary statistics")
    period: str = Field(..., description="Statistics period")


# Aliases for backward compatibility
AuditLogCreate = AuditEventCreate
AuditLogBatchCreate = AuditEventBatchCreate
AuditLogResponse = AuditEventResponse
AuditLogQuery = AuditEventQuery
AuditLogSummary = AuditStatistics
PaginatedAuditLogs = AuditEventQueryResponse
AuditLogExport = AuditEventExport
EventType = AuditEventType
Severity = AuditEventStatus


