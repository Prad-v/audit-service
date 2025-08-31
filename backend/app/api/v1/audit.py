"""
Audit log endpoints for the audit log framework.

This module provides endpoints for creating, querying, and exporting
audit log events with multi-tenant support and advanced filtering.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import JSONResponse
import structlog

from app.api.middleware import (
    get_current_user,
    require_permission,
)
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthorizationError,
)
from app.models.audit import (
    AuditEventCreate,
    AuditEventBatchCreate,
    AuditEventResponse,
    AuditEventQuery,
    AuditEventQueryResponse,
    PaginatedResponse,
    DynamicFilter,
    DynamicFilterGroup,
)
from app.models.metrics import (
    MetricsData,
    IngestionRateData,
    QueryRateData,
    TopEventType,
    SystemMetrics,
    MetricsResponse,
)
from app.models.auth import Permission
from app.models.base import PaginationParams, SortOrder
from app.services.audit_service import get_audit_service
from datetime import datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

logger = structlog.get_logger(__name__)
router = APIRouter()

# Rate limiter for audit endpoints
limiter = Limiter(key_func=get_remote_address)


@router.post("/events", response_model=AuditEventResponse)
@require_permission(Permission.WRITE_AUDIT)
@limiter.limit("1000/minute")  # High rate limit for audit writes
async def create_audit_event(
    request: Request,
    audit_data: AuditEventCreate,
):
    """
    Create a single audit log event.
    
    This endpoint allows authorized users to create individual audit log entries.
    The event will be stored in the database and published to NATS for real-time processing.
    
    **Required Permission**: AUDIT_WRITE
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        # Extract client information if not provided
        if not audit_data.ip_address:
            audit_data.ip_address = request.client.host if request.client else None
        
        if not audit_data.user_agent:
            audit_data.user_agent = request.headers.get("user-agent")
        
        if not audit_data.correlation_id:
            audit_data.correlation_id = getattr(request.state, "correlation_id", None)
        
        audit_service = get_audit_service()
        result = await audit_service.create_audit_event(
            audit_data=audit_data,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        
        logger.info(
            "Audit event created via API",
            audit_id=result.audit_id,
            tenant_id=tenant_id,
            event_type=audit_data.event_type,
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to create audit event", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit event",
        )


@router.post("/events/batch", response_model=List[AuditEventResponse])
@require_permission(Permission.WRITE_AUDIT)
@limiter.limit("100/minute")  # Lower rate limit for batch operations
async def create_audit_events_batch(
    request: Request,
    batch_data: AuditEventBatchCreate,
):
    """
    Create multiple audit log events in batch.
    
    This endpoint allows authorized users to create multiple audit log entries
    in a single request for improved performance. Maximum batch size is 1000 events.
    
    **Required Permission**: AUDIT_WRITE
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        # Validate batch size
        if len(batch_data.events) > 1000:
            raise ValidationError("Batch size cannot exceed 1000 events")
        
        if len(batch_data.events) == 0:
            raise ValidationError("Batch cannot be empty")
        
        # Enrich audit logs with client information
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        correlation_id = getattr(request.state, "correlation_id", None)
        
        for audit_log in batch_data.events:
            if not audit_log.ip_address:
                audit_log.ip_address = client_ip
            if not audit_log.user_agent:
                audit_log.user_agent = user_agent
            if not audit_log.correlation_id:
                audit_log.correlation_id = correlation_id
        
        audit_service = get_audit_service()
        results = await audit_service.create_audit_logs_batch(
            batch_data=batch_data,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        
        logger.info(
            "Audit events batch created via API",
            batch_size=len(results),
            tenant_id=tenant_id,
        )
        
        return results
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to create audit events batch", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit events batch",
        )


@router.get("/events", response_model=AuditEventQueryResponse)
@require_permission(Permission.READ_AUDIT)
@limiter.limit("300/minute")  # Rate limit for queries
async def get_audit_events(
    request: Request,
    # Pagination parameters
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=1000, description="Page size"),
    # Standard filtering parameters
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    event_types: Optional[List[str]] = Query(None, description="Event type filters"),
    resource_types: Optional[List[str]] = Query(None, description="Resource type filters"),
    resource_ids: Optional[List[str]] = Query(None, description="Resource ID filters"),
    actions: Optional[List[str]] = Query(None, description="Action filters"),
    severities: Optional[List[str]] = Query(None, description="Severity filters"),
    user_ids: Optional[List[str]] = Query(None, description="User ID filters"),
    ip_addresses: Optional[List[str]] = Query(None, description="IP address filters"),
    session_ids: Optional[List[str]] = Query(None, description="Session ID filters"),
    correlation_ids: Optional[List[str]] = Query(None, description="Correlation ID filters"),
    search: Optional[str] = Query(None, description="Search term"),
    # Dynamic filtering parameters
    dynamic_filters: Optional[str] = Query(None, description="JSON string of dynamic filters"),
    filter_groups: Optional[str] = Query(None, description="JSON string of filter groups"),
    # Sorting parameters
    sort_by: Optional[str] = Query("timestamp", description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
):
    """
    Query audit log events with filtering and pagination.
    
    This endpoint allows authorized users to retrieve audit log events with
    comprehensive filtering, sorting, and pagination capabilities.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        # Parse dynamic filters from JSON strings
        parsed_dynamic_filters = None
        parsed_filter_groups = None
        
        if dynamic_filters:
            try:
                import json
                dynamic_filters_data = json.loads(dynamic_filters)
                if isinstance(dynamic_filters_data, list):
                    parsed_dynamic_filters = [DynamicFilter(**filter_data) for filter_data in dynamic_filters_data]
                else:
                    parsed_dynamic_filters = [DynamicFilter(**dynamic_filters_data)]
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dynamic_filters JSON: {str(e)}"
                )
        
        if filter_groups:
            try:
                import json
                filter_groups_data = json.loads(filter_groups)
                if isinstance(filter_groups_data, list):
                    parsed_filter_groups = [DynamicFilterGroup(**group_data) for group_data in filter_groups_data]
                else:
                    parsed_filter_groups = [DynamicFilterGroup(**filter_groups_data)]
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid filter_groups JSON: {str(e)}"
                )
        
        # Build query parameters
        query = AuditEventQuery(
            start_time=start_date,
            end_time=end_date,
            event_type=event_types[0] if event_types else None,
            resource_type=resource_types[0] if resource_types else None,
            resource_id=resource_ids[0] if resource_ids else None,
            action=actions[0] if actions else None,
            status=severities[0] if severities else None,
            user_id=user_ids[0] if user_ids else None,
            ip_address=ip_addresses[0] if ip_addresses else None,
            session_id=session_ids[0] if session_ids else None,
            correlation_id=correlation_ids[0] if correlation_ids else None,
            dynamic_filters=parsed_dynamic_filters,
            filter_groups=parsed_filter_groups,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        pagination = PaginationParams(page=page, size=size)
        
        audit_service = get_audit_service()
        results = await audit_service.query_audit_logs(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
            pagination=pagination,
        )
        
        logger.info(
            "Audit events queried via API",
            tenant_id=tenant_id,
            total_results=results.total_count,
            page=page,
            size=size,
        )
        
        return results
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to query audit events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query audit events",
        )


@router.get("/events/{audit_id}", response_model=AuditEventResponse)
@require_permission(Permission.READ_AUDIT)
@limiter.limit("500/minute")
async def get_audit_event(
    request: Request,
    audit_id: str,
):
    """
    Get a specific audit log event by ID.
    
    This endpoint allows authorized users to retrieve a single audit log
    event by its unique identifier.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        audit_service = get_audit_service()
        result = await audit_service.get_audit_log(
            audit_id=audit_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        
        logger.info(
            "Audit event retrieved via API",
            audit_id=audit_id,
            tenant_id=tenant_id,
        )
        
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get audit event", audit_id=audit_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit event",
        )


@router.get("/events/export", response_model=AuditEventQueryResponse)
@require_permission(Permission.EXPORT_AUDIT)
@limiter.limit("10/minute")  # Low rate limit for exports
async def export_audit_events(
    request: Request,
    # Export parameters
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    # Standard filtering parameters
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    event_types: Optional[List[str]] = Query(None, description="Event type filters"),
    resource_types: Optional[List[str]] = Query(None, description="Resource type filters"),
    resource_ids: Optional[List[str]] = Query(None, description="Resource ID filters"),
    actions: Optional[List[str]] = Query(None, description="Action filters"),
    severities: Optional[List[str]] = Query(None, description="Severity filters"),
    user_ids: Optional[List[str]] = Query(None, description="User ID filters"),
    ip_addresses: Optional[List[str]] = Query(None, description="IP address filters"),
    session_ids: Optional[List[str]] = Query(None, description="Session ID filters"),
    correlation_ids: Optional[List[str]] = Query(None, description="Correlation ID filters"),
    search: Optional[str] = Query(None, description="Search term"),
    # Dynamic filtering parameters
    dynamic_filters: Optional[str] = Query(None, description="JSON string of dynamic filters"),
    filter_groups: Optional[str] = Query(None, description="JSON string of filter groups"),
    # Sorting parameters
    sort_by: Optional[str] = Query("timestamp", description="Sort field"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
):
    """
    Export audit log events in CSV or JSON format.
    
    This endpoint allows authorized users to export audit log events
    with the same filtering capabilities as the query endpoint.
    Maximum export size is 100,000 records.
    
    **Required Permission**: EXPORT_DATA
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        # Parse dynamic filters from JSON strings
        parsed_dynamic_filters = None
        parsed_filter_groups = None
        
        if dynamic_filters:
            try:
                import json
                dynamic_filters_data = json.loads(dynamic_filters)
                if isinstance(dynamic_filters_data, list):
                    parsed_dynamic_filters = [DynamicFilter(**filter_data) for filter_data in dynamic_filters_data]
                else:
                    parsed_dynamic_filters = [DynamicFilter(**dynamic_filters_data)]
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid dynamic_filters JSON: {str(e)}"
                )
        
        if filter_groups:
            try:
                import json
                filter_groups_data = json.loads(filter_groups)
                if isinstance(filter_groups_data, list):
                    parsed_filter_groups = [DynamicFilterGroup(**group_data) for group_data in filter_groups_data]
                else:
                    parsed_filter_groups = [DynamicFilterGroup(**filter_groups_data)]
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid filter_groups JSON: {str(e)}"
                )
        
        # Build query parameters
        query = AuditEventQuery(
            start_time=start_date,
            end_time=end_date,
            event_type=event_types[0] if event_types else None,
            resource_type=resource_types[0] if resource_types else None,
            resource_id=resource_ids[0] if resource_ids else None,
            action=actions[0] if actions else None,
            status=severities[0] if severities else None,
            user_id=user_ids[0] if user_ids else None,
            ip_address=ip_addresses[0] if ip_addresses else None,
            session_id=session_ids[0] if session_ids else None,
            correlation_id=correlation_ids[0] if correlation_ids else None,
            dynamic_filters=parsed_dynamic_filters,
            filter_groups=parsed_filter_groups,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        audit_service = get_audit_service()
        result = await audit_service.export_audit_logs(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
            export_format=format,
        )
        
        logger.info(
            "Audit events exported via API",
            tenant_id=tenant_id,
            format=format,
            count=result.count,
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to export audit events", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit events",
        )


@router.get("/summary", response_model=AuditEventQueryResponse)
@require_permission(Permission.READ_AUDIT)
@limiter.limit("100/minute")
async def get_audit_summary(
    request: Request,
    # Filtering parameters
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    event_types: Optional[List[str]] = Query(None, description="Event type filters"),
    resource_types: Optional[List[str]] = Query(None, description="Resource type filters"),
    resource_ids: Optional[List[str]] = Query(None, description="Resource ID filters"),
    actions: Optional[List[str]] = Query(None, description="Action filters"),
    severities: Optional[List[str]] = Query(None, description="Severity filters"),
    user_ids: Optional[List[str]] = Query(None, description="User ID filters"),
    ip_addresses: Optional[List[str]] = Query(None, description="IP address filters"),
    session_ids: Optional[List[str]] = Query(None, description="Session ID filters"),
    correlation_ids: Optional[List[str]] = Query(None, description="Correlation ID filters"),
    search: Optional[str] = Query(None, description="Search term"),
):
    """
    Get audit log statistics and summary metrics.
    
    This endpoint provides summary statistics for audit log events
    including counts by event type, severity, and resource type.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        # Build query parameters
        query = AuditEventQuery(
            start_time=start_date,
            end_time=end_date,
            event_type=event_types[0] if event_types else None,
            resource_type=resource_types[0] if resource_types else None,
            resource_id=resource_ids[0] if resource_ids else None,
            action=actions[0] if actions else None,
            status=severities[0] if severities else None,
            user_id=user_ids[0] if user_ids else None,
            ip_address=ip_addresses[0] if ip_addresses else None,
            session_id=session_ids[0] if session_ids else None,
            correlation_id=correlation_ids[0] if correlation_ids else None,
        )
        
        audit_service = get_audit_service()
        result = await audit_service.get_audit_summary(
            query=query,
            tenant_id=tenant_id,
            user_id=user_id,
        )
        
        logger.info(
            "Audit summary retrieved via API",
            tenant_id=tenant_id,
            total_count=result.total_count,
        )
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get audit summary", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get audit summary",
        )


# Health check endpoint for audit service
@router.get("/health")
async def audit_health_check():
    """
    Health check endpoint for audit service.
    
    This endpoint provides health status for the audit log service
    and its dependencies.
    """
    try:
        # Basic health check - could be expanded to check database, NATS, etc.
        return {
            "status": "healthy",
            "service": "audit-api",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error("Audit health check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit service unhealthy",
        )


# Metrics endpoints
@router.get("/metrics", response_model=MetricsResponse)
@require_permission(Permission.READ_AUDIT)
async def get_metrics(request: Request):
    """
    Get comprehensive metrics for the audit system.
    
    This endpoint provides overall metrics including ingestion rate, query rate,
    top event types, and system performance metrics.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        audit_service = get_audit_service()
        result = await audit_service.get_metrics(tenant_id=tenant_id)
        
        logger.info("Metrics retrieved", tenant_id=tenant_id)
        
        return result
        
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/metrics/ingestion-rate", response_model=List[IngestionRateData])
@require_permission(Permission.READ_AUDIT)
async def get_ingestion_rate(
    request: Request,
    time_range: str = Query("1h", description="Time range for ingestion rate (e.g., 1h, 24h, 7d)"),
):
    """
    Get event ingestion rate over time.
    
    This endpoint provides ingestion rate data points for the specified time range.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        audit_service = get_audit_service()
        result = await audit_service.get_ingestion_rate(
            time_range=time_range,
            tenant_id=tenant_id,
        )
        
        logger.info("Ingestion rate retrieved", tenant_id=tenant_id, time_range=time_range)
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get ingestion rate", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/metrics/query-rate", response_model=List[QueryRateData])
@require_permission(Permission.READ_AUDIT)
async def get_query_rate(
    request: Request,
    time_range: str = Query("1h", description="Time range for query rate (e.g., 1h, 24h, 7d)"),
):
    """
    Get query rate over time.
    
    This endpoint provides query rate data points for the specified time range.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        audit_service = get_audit_service()
        result = await audit_service.get_query_rate(
            time_range=time_range,
            tenant_id=tenant_id,
        )
        
        logger.info("Query rate retrieved", tenant_id=tenant_id, time_range=time_range)
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get query rate", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/metrics/top-event-types", response_model=List[TopEventType])
@require_permission(Permission.READ_AUDIT)
async def get_top_event_types(
    request: Request,
    limit: int = Query(10, description="Number of top event types to return"),
):
    """
    Get top event types by count.
    
    This endpoint provides statistics on the most common event types.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        audit_service = get_audit_service()
        result = await audit_service.get_top_event_types(
            limit=limit,
            tenant_id=tenant_id,
        )
        
        logger.info("Top event types retrieved", tenant_id=tenant_id, limit=limit)
        
        return result
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get top event types", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/metrics/system", response_model=SystemMetrics)
@require_permission(Permission.READ_AUDIT)
async def get_system_metrics(request: Request):
    """
    Get system performance metrics.
    
    This endpoint provides system-level performance metrics including CPU, memory, and disk usage.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        user_id, tenant_id, _, _ = get_current_user(request)
        
        audit_service = get_audit_service()
        result = await audit_service.get_system_metrics()
        
        logger.info("System metrics retrieved", tenant_id=tenant_id)
        
        return result
        
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/filters/info")
@require_permission(Permission.READ_AUDIT)
async def get_filter_info(request: Request):
    """
    Get information about available fields and operators for dynamic filtering.
    
    This endpoint provides metadata about the available fields that can be used
    for dynamic filtering, along with supported operators and example filters.
    
    **Required Permission**: AUDIT_READ
    """
    try:
        from app.services.dynamic_filter_service import dynamic_filter_service
        
        return {
            "available_fields": dynamic_filter_service.get_available_fields(),
            "supported_operators": dynamic_filter_service.get_supported_operators(),
            "examples": dynamic_filter_service.create_filter_examples(),
            "field_mappings": {
                "standard_fields": [
                    "audit_id", "timestamp", "event_type", "action", "status",
                    "tenant_id", "service_name", "user_id", "resource_type", 
                    "resource_id", "correlation_id", "session_id", "ip_address",
                    "user_agent", "created_at", "updated_at"
                ],
                "json_fields": [
                    "request_data", "response_data", "metadata"
                ],
                "nested_json_examples": [
                    "request_data.method", "request_data.path", "request_data.headers",
                    "response_data.status_code", "response_data.body",
                    "metadata.user_id", "metadata.session_id", "metadata.login_method"
                ]
            }
        }
        
    except Exception as e:
        logger.error("Failed to get filter info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )