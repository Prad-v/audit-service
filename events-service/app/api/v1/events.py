"""
Cloud Events API Endpoints

This module contains FastAPI endpoints for managing cloud provider events.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import CloudEvent
from app.models.events import (
    CloudEventCreate, CloudEventResponse, CloudEventListResponse,
    EventType, EventSeverity, EventStatus, CloudProvider
)
from app.core.database import get_db
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/events", response_model=CloudEventResponse, status_code=status.HTTP_201_CREATED)
async def create_cloud_event(
    event_data: CloudEventCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new cloud event"""
    try:
        # Generate event ID
        event_id = f"event-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user[:8]}"
        
        # Set event time if not provided
        if not event_data.event_time:
            event_data.event_time = datetime.utcnow()
        
        # Create event
        event = CloudEvent(
            event_id=event_id,
            external_id=event_data.external_id,
            event_type=event_data.event_type,
            severity=event_data.severity,
            status=EventStatus.ACTIVE,
            cloud_provider=event_data.cloud_provider,
            project_id=event_data.project_id,
            subscription_id=event_data.subscription_id,
            title=event_data.title,
            description=event_data.description,
            summary=event_data.summary,
            service_name=event_data.service_name,
            resource_type=event_data.resource_type,
            resource_id=event_data.resource_id,
            region=event_data.region,
            event_time=event_data.event_time,
            raw_data=event_data.raw_data,
            tenant_id="default",  # TODO: Get from user context
        )
        
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        # Process event for alerting
        from app.services.event_processor import EventProcessor
        processor = EventProcessor(db)
        await processor.process_event(event)
        
        return CloudEventResponse.from_orm(event)
        
    except Exception as e:
        logger.error(f"Error creating cloud event: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating cloud event: {str(e)}")


@router.get("/events", response_model=CloudEventListResponse)
async def list_cloud_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    event_type: Optional[EventType] = None,
    severity: Optional[EventSeverity] = None,
    status: Optional[EventStatus] = None,
    cloud_provider: Optional[CloudProvider] = None,
    project_id: Optional[str] = None,
    subscription_id: Optional[str] = None,
    service_name: Optional[str] = None,
    region: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List cloud events with filtering"""
    try:
        # Build query
        query = select(CloudEvent).where(CloudEvent.tenant_id == "default")
        
        # Apply filters
        if event_type:
            query = query.where(CloudEvent.event_type == event_type)
        if severity:
            query = query.where(CloudEvent.severity == severity)
        if status:
            query = query.where(CloudEvent.status == status)
        if cloud_provider:
            query = query.where(CloudEvent.cloud_provider == cloud_provider)
        if project_id:
            query = query.where(CloudEvent.project_id == project_id)
        if subscription_id:
            query = query.where(CloudEvent.subscription_id == subscription_id)
        if service_name:
            query = query.where(CloudEvent.service_name == service_name)
        if region:
            query = query.where(CloudEvent.region == region)
        if start_time:
            query = query.where(CloudEvent.event_time >= start_time)
        if end_time:
            query = query.where(CloudEvent.event_time <= end_time)
        
        # Order by event time desc
        query = query.order_by(CloudEvent.event_time.desc())
        
        # Get total count
        count_query = select(func.count(CloudEvent.event_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return CloudEventListResponse(
            events=[CloudEventResponse.from_orm(event) for event in events],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing cloud events: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing cloud events: {str(e)}")


@router.get("/events/{event_id}", response_model=CloudEventResponse)
async def get_cloud_event(
    event_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific cloud event"""
    try:
        result = await db.execute(
            select(CloudEvent).where(
                and_(
                    CloudEvent.event_id == event_id,
                    CloudEvent.tenant_id == "default"
                )
            )
        )
        event = result.scalar_one_or_none()
        
        if not event:
            raise HTTPException(status_code=404, detail="Cloud event not found")
        
        return CloudEventResponse.from_orm(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cloud event: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cloud event: {str(e)}")


@router.put("/events/{event_id}/acknowledge", response_model=CloudEventResponse)
async def acknowledge_cloud_event(
    event_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge a cloud event"""
    try:
        result = await db.execute(
            select(CloudEvent).where(
                and_(
                    CloudEvent.event_id == event_id,
                    CloudEvent.tenant_id == "default"
                )
            )
        )
        event = result.scalar_one_or_none()
        
        if not event:
            raise HTTPException(status_code=404, detail="Cloud event not found")
        
        event.status = EventStatus.ACKNOWLEDGED
        event.acknowledged_at = datetime.utcnow()
        event.acknowledged_by = current_user
        event.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(event)
        
        return CloudEventResponse.from_orm(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging cloud event: {e}")
        raise HTTPException(status_code=500, detail=f"Error acknowledging cloud event: {str(e)}")


@router.put("/events/{event_id}/resolve", response_model=CloudEventResponse)
async def resolve_cloud_event(
    event_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve a cloud event"""
    try:
        result = await db.execute(
            select(CloudEvent).where(
                and_(
                    CloudEvent.event_id == event_id,
                    CloudEvent.tenant_id == "default"
                )
            )
        )
        event = result.scalar_one_or_none()
        
        if not event:
            raise HTTPException(status_code=404, detail="Cloud event not found")
        
        event.status = EventStatus.RESOLVED
        event.resolved_at = datetime.utcnow()
        event.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(event)
        
        return CloudEventResponse.from_orm(event)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving cloud event: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving cloud event: {str(e)}")


@router.post("/events/webhook/grafana")
async def grafana_webhook(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Webhook endpoint for Grafana alerts"""
    try:
        from app.services.webhook_handlers.grafana import GrafanaWebhookHandler
        
        handler = GrafanaWebhookHandler(db)
        events = await handler.process_webhook(request)
        
        return {
            "success": True,
            "message": f"Processed {len(events)} events from Grafana webhook",
            "events": [event.event_id for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error processing Grafana webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/events/webhook/gcp")
async def gcp_webhook(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Webhook endpoint for GCP Cloud Monitoring"""
    try:
        from app.services.webhook_handlers.gcp import GCPWebhookHandler
        
        handler = GCPWebhookHandler(db)
        events = await handler.process_webhook(request)
        
        return {
            "success": True,
            "message": f"Processed {len(events)} events from GCP webhook",
            "events": [event.event_id for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error processing GCP webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/events/webhook/aws")
async def aws_webhook(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Webhook endpoint for AWS CloudWatch"""
    try:
        from app.services.webhook_handlers.aws import AWSWebhookHandler
        
        handler = AWSWebhookHandler()
        events = await handler.process_webhook(request, db)
        
        return {
            "success": True,
            "message": f"Processed {len(events)} events from AWS webhook",
            "events": [event.event_id for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error processing AWS webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/events/webhook/azure")
async def azure_webhook(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Webhook endpoint for Azure Monitor"""
    try:
        from app.services.webhook_handlers.azure import AzureWebhookHandler
        
        handler = AzureWebhookHandler(db)
        events = await handler.process_webhook(request)
        
        return {
            "success": True,
            "message": f"Processed {len(events)} events from Azure webhook",
            "events": [event.event_id for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error processing Azure webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.post("/events/webhook/oci")
async def oci_webhook(
    request: Dict[str, Any],
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Webhook endpoint for OCI Monitoring"""
    try:
        from app.services.webhook_handlers.oci import OCIWebhookHandler
        
        handler = OCIWebhookHandler(db)
        events = await handler.process_webhook(request)
        
        return {
            "success": True,
            "message": f"Processed {len(events)} events from OCI webhook",
            "events": [event.event_id for event in events]
        }
        
    except Exception as e:
        logger.error(f"Error processing OCI webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")


@router.get("/events/stats/summary")
async def get_events_summary(
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get events summary statistics"""
    try:
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Total events
        total_query = select(func.count(CloudEvent.event_id)).where(CloudEvent.tenant_id == "default")
        total_events = await db.scalar(total_query)
        
        # Events in last 24 hours
        last_24h_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= last_24h
            )
        )
        events_24h = await db.scalar(last_24h_query)
        
        # Events in last 7 days
        last_7d_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= last_7d
            )
        )
        events_7d = await db.scalar(last_7d_query)
        
        # Events in last 30 days
        last_30d_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= last_30d
            )
        )
        events_30d = await db.scalar(last_30d_query)
        
        # Events by severity
        severity_query = select(
            CloudEvent.severity,
            func.count(CloudEvent.event_id)
        ).where(CloudEvent.tenant_id == "default").group_by(CloudEvent.severity)
        
        severity_result = await db.execute(severity_query)
        events_by_severity = {row[0]: row[1] for row in severity_result.all()}
        
        # Events by provider
        provider_query = select(
            CloudEvent.cloud_provider,
            func.count(CloudEvent.event_id)
        ).where(CloudEvent.tenant_id == "default").group_by(CloudEvent.cloud_provider)
        
        provider_result = await db.execute(provider_query)
        events_by_provider = {row[0]: row[1] for row in provider_result.all()}
        
        # Events by type
        type_query = select(
            CloudEvent.event_type,
            func.count(CloudEvent.event_id)
        ).where(CloudEvent.tenant_id == "default").group_by(CloudEvent.event_type)
        
        type_result = await db.execute(type_query)
        events_by_type = {row[0]: row[1] for row in type_result.all()}
        
        # Active events
        active_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.tenant_id == "default",
                CloudEvent.status == EventStatus.ACTIVE
            )
        )
        active_events = await db.scalar(active_query)
        
        return {
            "total_events": total_events,
            "events_last_24h": events_24h,
            "events_last_7d": events_7d,
            "events_last_30d": events_30d,
            "active_events": active_events,
            "events_by_severity": events_by_severity,
            "events_by_provider": events_by_provider,
            "events_by_type": events_by_type
        }
        
    except Exception as e:
        logger.error(f"Error getting events summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting events summary: {str(e)}")


@router.get("/events/stats/trends")
async def get_events_trends(
    hours: int = Query(24, ge=1, le=168),  # Max 7 days
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get events trends over time"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        now = datetime.utcnow()
        start_time = now - timedelta(hours=hours)
        
        # Get hourly trends
        hourly_query = select(
            func.date_trunc('hour', CloudEvent.event_time).label('hour'),
            func.count(CloudEvent.event_id).label('count')
        ).where(
            and_(
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= start_time,
                CloudEvent.event_time <= now
            )
        ).group_by(
            func.date_trunc('hour', CloudEvent.event_time)
        ).order_by(
            func.date_trunc('hour', CloudEvent.event_time)
        )
        
        result = await db.execute(hourly_query)
        hourly_trends = [
            {
                "hour": row[0].isoformat(),
                "count": row[1]
            }
            for row in result.all()
        ]
        
        # Get trends by severity
        severity_trends_query = select(
            func.date_trunc('hour', CloudEvent.event_time).label('hour'),
            CloudEvent.severity,
            func.count(CloudEvent.event_id).label('count')
        ).where(
            and_(
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= start_time,
                CloudEvent.event_time <= now
            )
        ).group_by(
            func.date_trunc('hour', CloudEvent.event_time),
            CloudEvent.severity
        ).order_by(
            func.date_trunc('hour', CloudEvent.event_time),
            CloudEvent.severity
        )
        
        severity_result = await db.execute(severity_trends_query)
        severity_trends = {}
        for row in severity_result.all():
            hour = row[0].isoformat()
            severity = row[1]
            count = row[2]
            
            if hour not in severity_trends:
                severity_trends[hour] = {}
            severity_trends[hour][severity] = count
        
        return {
            "time_range_hours": hours,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "hourly_trends": hourly_trends,
            "severity_trends": severity_trends
        }
        
    except Exception as e:
        logger.error(f"Error getting events trends: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting events trends: {str(e)}")
