"""
Audit log service for the audit log framework.

This service handles audit log creation, retrieval, and management
with high-performance batch processing and filtering capabilities.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

import structlog
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthorizationError,
)
from app.db.database import get_database_manager
from app.db.schemas import AuditLog, User
from app.models.audit import (
    AuditLogCreate,
    AuditLogBatchCreate,
    AuditLogResponse,
    AuditLogQuery,
    AuditLogSummary,
    PaginatedAuditLogs,
    AuditLogExport,
    EventType,
    Severity,
)
from app.models.base import PaginationParams, SortOrder
from app.services.nats_service import get_nats_service
from app.services.cache_service import get_cache_service
from app.utils.metrics import audit_metrics

logger = structlog.get_logger(__name__)


class AuditService:
    """Service for managing audit logs with high-performance operations."""
    
    def __init__(self):
        self.db_manager = get_database_manager()
        self.nats_service = get_nats_service()
        self.cache_service = get_cache_service()
    
    async def create_audit_log(
        self,
        audit_data: AuditLogCreate,
        tenant_id: str,
        user_id: Optional[str] = None,
    ) -> AuditLogResponse:
        """Create a single audit log entry."""
        try:
            # Generate audit log ID
            audit_id = str(uuid4())
            
            # Create audit log record
            audit_log = AuditLog(
                id=audit_id,
                tenant_id=tenant_id,
                user_id=user_id,
                event_type=audit_data.event_type,
                resource_type=audit_data.resource_type,
                resource_id=audit_data.resource_id,
                action=audit_data.action,
                severity=audit_data.severity,
                description=audit_data.description,
                event_metadata=audit_data.metadata or {},
                ip_address=audit_data.ip_address,
                user_agent=audit_data.user_agent,
                session_id=audit_data.session_id,
                correlation_id=audit_data.correlation_id,
                timestamp=audit_data.timestamp or datetime.now(timezone.utc),
                created_at=datetime.now(timezone.utc),
            )
            
            # Store in database
            async with self.db_manager.get_session() as session:
                session.add(audit_log)
                await session.commit()
                await session.refresh(audit_log)
            
            # Publish to NATS for real-time processing
            await self._publish_audit_event(audit_log)
            
            # Update metrics
            audit_metrics.audit_logs_created.inc()
            audit_metrics.audit_logs_by_type.labels(
                event_type=audit_data.event_type.value
            ).inc()
            
            logger.info(
                "Audit log created",
                audit_id=audit_id,
                tenant_id=tenant_id,
                event_type=audit_data.event_type.value,
                resource_type=audit_data.resource_type,
                action=audit_data.action,
            )
            
            return AuditLogResponse.from_orm(audit_log)
            
        except Exception as e:
            audit_metrics.audit_logs_errors.inc()
            logger.error("Failed to create audit log", error=str(e))
            raise
    
    async def create_audit_logs_batch(
        self,
        batch_data: AuditLogBatchCreate,
        tenant_id: str,
        user_id: Optional[str] = None,
    ) -> List[AuditLogResponse]:
        """Create multiple audit log entries in a batch."""
        try:
            audit_logs = []
            current_time = datetime.now(timezone.utc)
            
            # Create audit log records
            for audit_data in batch_data.audit_logs:
                audit_id = str(uuid4())
                
                audit_log = AuditLog(
                    id=audit_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    event_type=audit_data.event_type,
                    resource_type=audit_data.resource_type,
                    resource_id=audit_data.resource_id,
                    action=audit_data.action,
                    severity=audit_data.severity,
                    description=audit_data.description,
                    event_metadata=audit_data.metadata or {},
                    ip_address=audit_data.ip_address,
                    user_agent=audit_data.user_agent,
                    session_id=audit_data.session_id,
                    correlation_id=audit_data.correlation_id,
                    timestamp=audit_data.timestamp or current_time,
                    created_at=current_time,
                )
                audit_logs.append(audit_log)
            
            # Batch insert to database
            async with self.db_manager.get_session() as session:
                session.add_all(audit_logs)
                await session.commit()
                
                # Refresh all records to get generated fields
                for audit_log in audit_logs:
                    await session.refresh(audit_log)
            
            # Publish batch to NATS for real-time processing
            await self._publish_audit_batch(audit_logs)
            
            # Update metrics
            audit_metrics.audit_logs_created.inc(len(audit_logs))
            audit_metrics.batch_operations.inc()
            
            logger.info(
                "Audit log batch created",
                batch_size=len(audit_logs),
                tenant_id=tenant_id,
            )
            
            return [AuditLogResponse.from_orm(log) for log in audit_logs]
            
        except Exception as e:
            audit_metrics.audit_logs_errors.inc()
            logger.error("Failed to create audit log batch", error=str(e))
            raise
    
    async def get_audit_log(
        self,
        audit_id: str,
        tenant_id: str,
        user_id: str,
    ) -> AuditLogResponse:
        """Get a single audit log by ID."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(AuditLog).where(
                    AuditLog.id == audit_id,
                    AuditLog.tenant_id == tenant_id,
                )
                result = await session.execute(stmt)
                audit_log = result.scalar_one_or_none()
                
                if not audit_log:
                    raise NotFoundError("Audit log not found")
                
                return AuditLogResponse.from_orm(audit_log)
                
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to get audit log", audit_id=audit_id, error=str(e))
            raise
    
    async def query_audit_logs(
        self,
        query: AuditLogQuery,
        tenant_id: str,
        user_id: str,
        pagination: PaginationParams,
    ) -> PaginatedAuditLogs:
        """Query audit logs with filtering, sorting, and pagination."""
        try:
            # Check cache first
            cache_key = self._build_cache_key(query, tenant_id, pagination)
            cached_result = await self.cache_service.get(cache_key)
            if cached_result:
                audit_metrics.cache_hits.inc()
                return PaginatedAuditLogs.parse_obj(cached_result)
            
            async with self.db_manager.get_session() as session:
                # Build base query
                stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
                
                # Apply filters
                stmt = self._apply_filters(stmt, query)
                
                # Get total count
                count_stmt = select(func.count()).select_from(stmt.subquery())
                total_result = await session.execute(count_stmt)
                total_count = total_result.scalar()
                
                # Apply sorting
                stmt = self._apply_sorting(stmt, query.sort_by, query.sort_order)
                
                # Apply pagination
                stmt = stmt.offset(pagination.offset).limit(pagination.limit)
                
                # Execute query
                result = await session.execute(stmt)
                audit_logs = result.scalars().all()
                
                # Convert to response models
                items = [AuditLogResponse.from_orm(log) for log in audit_logs]
                
                # Create paginated response
                paginated_result = PaginatedAuditLogs(
                    items=items,
                    total=total_count,
                    page=pagination.page,
                    size=pagination.size,
                    pages=pagination.calculate_pages(total_count),
                )
                
                # Cache the result
                await self.cache_service.set(
                    cache_key,
                    paginated_result.dict(),
                    ttl=300,  # 5 minutes
                )
                
                audit_metrics.cache_misses.inc()
                audit_metrics.queries_executed.inc()
                
                logger.info(
                    "Audit logs queried",
                    tenant_id=tenant_id,
                    total_count=total_count,
                    page=pagination.page,
                    size=pagination.size,
                )
                
                return paginated_result
                
        except Exception as e:
            logger.error("Failed to query audit logs", error=str(e))
            raise
    
    async def get_audit_summary(
        self,
        query: AuditLogQuery,
        tenant_id: str,
        user_id: str,
    ) -> AuditLogSummary:
        """Get audit log summary statistics."""
        try:
            async with self.db_manager.get_session() as session:
                # Build base query
                base_stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
                base_stmt = self._apply_filters(base_stmt, query)
                
                # Total count
                count_stmt = select(func.count()).select_from(base_stmt.subquery())
                total_result = await session.execute(count_stmt)
                total_count = total_result.scalar()
                
                # Event type distribution
                event_type_stmt = (
                    select(AuditLog.event_type, func.count().label('count'))
                    .where(AuditLog.tenant_id == tenant_id)
                    .group_by(AuditLog.event_type)
                )
                event_type_stmt = self._apply_filters(event_type_stmt, query)
                event_type_result = await session.execute(event_type_stmt)
                event_types = {row.event_type.value: row.count for row in event_type_result}
                
                # Severity distribution
                severity_stmt = (
                    select(AuditLog.severity, func.count().label('count'))
                    .where(AuditLog.tenant_id == tenant_id)
                    .group_by(AuditLog.severity)
                )
                severity_stmt = self._apply_filters(severity_stmt, query)
                severity_result = await session.execute(severity_stmt)
                severities = {row.severity.value: row.count for row in severity_result}
                
                # Resource type distribution
                resource_stmt = (
                    select(AuditLog.resource_type, func.count().label('count'))
                    .where(AuditLog.tenant_id == tenant_id)
                    .group_by(AuditLog.resource_type)
                )
                resource_stmt = self._apply_filters(resource_stmt, query)
                resource_result = await session.execute(resource_stmt)
                resource_types = {row.resource_type: row.count for row in resource_result}
                
                return AuditLogSummary(
                    total_count=total_count,
                    event_types=event_types,
                    severities=severities,
                    resource_types=resource_types,
                    date_range={
                        "start": query.start_date.isoformat() if query.start_date else None,
                        "end": query.end_date.isoformat() if query.end_date else None,
                    },
                )
                
        except Exception as e:
            logger.error("Failed to get audit summary", error=str(e))
            raise
    
    async def export_audit_logs(
        self,
        query: AuditLogQuery,
        tenant_id: str,
        user_id: str,
        export_format: str = "json",
    ) -> AuditLogExport:
        """Export audit logs in specified format."""
        try:
            # Limit export size for performance
            max_export_size = 100000  # 100k records max
            
            async with self.db_manager.get_session() as session:
                # Build query
                stmt = select(AuditLog).where(AuditLog.tenant_id == tenant_id)
                stmt = self._apply_filters(stmt, query)
                stmt = self._apply_sorting(stmt, query.sort_by, query.sort_order)
                stmt = stmt.limit(max_export_size)
                
                # Execute query
                result = await session.execute(stmt)
                audit_logs = result.scalars().all()
                
                # Convert to export format
                export_data = []
                for log in audit_logs:
                    export_data.append({
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "event_type": log.event_type.value,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "action": log.action,
                        "severity": log.severity.value,
                        "description": log.description,
                        "metadata": log.event_metadata,
                        "ip_address": log.ip_address,
                        "user_agent": log.user_agent,
                        "session_id": log.session_id,
                        "correlation_id": log.correlation_id,
                    })
                
                audit_metrics.exports_generated.inc()
                
                logger.info(
                    "Audit logs exported",
                    tenant_id=tenant_id,
                    count=len(export_data),
                    format=export_format,
                )
                
                return AuditLogExport(
                    data=export_data,
                    format=export_format,
                    count=len(export_data),
                    generated_at=datetime.now(timezone.utc),
                )
                
        except Exception as e:
            logger.error("Failed to export audit logs", error=str(e))
            raise
    
    def _apply_filters(self, stmt, query: AuditLogQuery):
        """Apply filters to the query statement."""
        if query.start_date:
            stmt = stmt.where(AuditLog.timestamp >= query.start_date)
        
        if query.end_date:
            stmt = stmt.where(AuditLog.timestamp <= query.end_date)
        
        if query.event_types:
            stmt = stmt.where(AuditLog.event_type.in_(query.event_types))
        
        if query.resource_types:
            stmt = stmt.where(AuditLog.resource_type.in_(query.resource_types))
        
        if query.resource_ids:
            stmt = stmt.where(AuditLog.resource_id.in_(query.resource_ids))
        
        if query.actions:
            stmt = stmt.where(AuditLog.action.in_(query.actions))
        
        if query.severities:
            stmt = stmt.where(AuditLog.severity.in_(query.severities))
        
        if query.user_ids:
            stmt = stmt.where(AuditLog.user_id.in_(query.user_ids))
        
        if query.ip_addresses:
            stmt = stmt.where(AuditLog.ip_address.in_(query.ip_addresses))
        
        if query.session_ids:
            stmt = stmt.where(AuditLog.session_id.in_(query.session_ids))
        
        if query.correlation_ids:
            stmt = stmt.where(AuditLog.correlation_id.in_(query.correlation_ids))
        
        if query.search:
            search_term = f"%{query.search}%"
            stmt = stmt.where(
                or_(
                    AuditLog.description.ilike(search_term),
                    AuditLog.action.ilike(search_term),
                    AuditLog.resource_type.ilike(search_term),
                )
            )
        
        return stmt
    
    def _apply_sorting(self, stmt, sort_by: Optional[str], sort_order: SortOrder):
        """Apply sorting to the query statement."""
        if not sort_by:
            sort_by = "timestamp"
        
        sort_column = getattr(AuditLog, sort_by, AuditLog.timestamp)
        
        if sort_order == SortOrder.DESC:
            stmt = stmt.order_by(desc(sort_column))
        else:
            stmt = stmt.order_by(asc(sort_column))
        
        return stmt
    
    def _build_cache_key(
        self,
        query: AuditLogQuery,
        tenant_id: str,
        pagination: PaginationParams,
    ) -> str:
        """Build cache key for query results."""
        key_parts = [
            "audit_query",
            tenant_id,
            str(hash(query.json())),
            f"page_{pagination.page}",
            f"size_{pagination.size}",
        ]
        return ":".join(key_parts)
    
    async def _publish_audit_event(self, audit_log: AuditLog):
        """Publish single audit event to NATS."""
        try:
            event_data = {
                "id": audit_log.id,
                "tenant_id": audit_log.tenant_id,
                "event_type": audit_log.event_type.value,
                "resource_type": audit_log.resource_type,
                "resource_id": audit_log.resource_id,
                "action": audit_log.action,
                "severity": audit_log.severity.value,
                "timestamp": audit_log.timestamp.isoformat(),
                "metadata": audit_log.event_metadata,
            }
            
            await self.nats_service.publish(
                subject=f"audit.events.{audit_log.tenant_id}",
                data=event_data,
            )
            
        except Exception as e:
            logger.warning("Failed to publish audit event to NATS", error=str(e))
    
    async def _publish_audit_batch(self, audit_logs: List[AuditLog]):
        """Publish batch of audit events to NATS."""
        try:
            batch_data = {
                "batch_id": str(uuid4()),
                "tenant_id": audit_logs[0].tenant_id if audit_logs else None,
                "count": len(audit_logs),
                "events": [
                    {
                        "id": log.id,
                        "event_type": log.event_type.value,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "action": log.action,
                        "severity": log.severity.value,
                        "timestamp": log.timestamp.isoformat(),
                    }
                    for log in audit_logs
                ],
            }
            
            await self.nats_service.publish(
                subject=f"audit.batch.{audit_logs[0].tenant_id}",
                data=batch_data,
            )
            
        except Exception as e:
            logger.warning("Failed to publish audit batch to NATS", error=str(e))


# Global audit service instance
_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    """Get the global audit service instance."""
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service