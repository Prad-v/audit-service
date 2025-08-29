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
    # Filtering parameters (same as query)
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