"""
Base models for the audit log framework.

This module contains base model classes and common data structures
used throughout the application.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Generic, TypeVar
from enum import Enum

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel


T = TypeVar('T')


class BaseAppModel(BaseModel):
    """Base model for all application models."""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""
    
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")


class SoftDeleteMixin(BaseModel):
    """Mixin for models with soft delete functionality."""
    
    is_deleted: bool = Field(False, description="Whether record is soft deleted")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")


class PaginationParams(BaseAppModel):
    """Model for pagination parameters."""
    
    page: int = Field(1, description="Page number", ge=1)
    page_size: int = Field(50, description="Page size", ge=1, le=1000)
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic model for paginated responses."""
    
    items: List[T] = Field(..., description="List of items")
    total_count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total_count: int,
        page: int,
        page_size: int,
    ) -> 'PaginatedResponse[T]':
        """Create a paginated response."""
        total_pages = (total_count + page_size - 1) // page_size
        has_next = page < total_pages
        has_previous = page > 1
        
        return cls(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class SortParams(BaseAppModel):
    """Model for sorting parameters."""
    
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")


class FilterParams(BaseAppModel):
    """Base model for filter parameters."""
    
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")


class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ServiceHealth(BaseAppModel):
    """Model for service health information."""
    
    name: str = Field(..., description="Service name")
    status: HealthStatus = Field(..., description="Service health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
    error: Optional[str] = Field(None, description="Error message if unhealthy")
    last_check: datetime = Field(..., description="Last health check timestamp")


class SystemHealth(BaseAppModel):
    """Model for overall system health."""
    
    status: HealthStatus = Field(..., description="Overall system health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Environment name")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    services: List[ServiceHealth] = Field(..., description="Individual service health")


class ErrorResponse(BaseAppModel):
    """Model for error responses."""
    
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class SuccessResponse(BaseAppModel):
    """Model for success responses."""
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class BulkOperationResult(BaseAppModel):
    """Model for bulk operation results."""
    
    total_count: int = Field(..., description="Total number of items processed")
    success_count: int = Field(..., description="Number of successful operations")
    error_count: int = Field(..., description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class ExportFormat(str, Enum):
    """Export format enumeration."""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"


class ExportStatus(str, Enum):
    """Export status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class ExportJob(BaseAppModel):
    """Model for export job information."""
    
    id: str = Field(..., description="Export job ID")
    status: ExportStatus = Field(..., description="Export job status")
    format: ExportFormat = Field(..., description="Export format")
    total_records: Optional[int] = Field(None, description="Total number of records to export")
    processed_records: Optional[int] = Field(None, description="Number of records processed")
    download_url: Optional[str] = Field(None, description="Download URL when completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    expires_at: Optional[datetime] = Field(None, description="Download URL expiration timestamp")


class MetricValue(BaseAppModel):
    """Model for metric values."""
    
    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Metric unit")
    timestamp: datetime = Field(..., description="Metric timestamp")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")


class SystemMetrics(BaseAppModel):
    """Model for system metrics."""
    
    timestamp: datetime = Field(..., description="Metrics timestamp")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")
    network_io_bytes: Dict[str, int] = Field(..., description="Network I/O bytes")
    active_connections: int = Field(..., description="Number of active connections")
    request_rate: float = Field(..., description="Request rate per second")
    error_rate: float = Field(..., description="Error rate percentage")
    response_time_p95: float = Field(..., description="95th percentile response time")


class ConfigurationItem(BaseAppModel):
    """Model for configuration items."""
    
    key: str = Field(..., description="Configuration key")
    value: Any = Field(..., description="Configuration value")
    description: Optional[str] = Field(None, description="Configuration description")
    is_sensitive: bool = Field(False, description="Whether the value is sensitive")
    category: Optional[str] = Field(None, description="Configuration category")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated")


class AuditContext(BaseAppModel):
    """Model for audit context information."""
    
    user_id: Optional[str] = Field(None, description="User ID")
    tenant_id: str = Field(..., description="Tenant ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    service_name: str = Field(..., description="Service name")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for audit logging."""
        return self.dict(exclude_none=True)