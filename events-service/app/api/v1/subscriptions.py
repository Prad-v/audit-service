"""
Event Subscriptions API Endpoints

This module contains FastAPI endpoints for managing event subscriptions to cloud provider events.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import EventSubscription
from app.models.events import (
    EventSubscriptionCreate, EventSubscriptionUpdate, EventSubscriptionResponse, EventSubscriptionListResponse
)
from app.core.database import get_db
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/subscriptions", response_model=EventSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_event_subscription(
    subscription_data: EventSubscriptionCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new event subscription"""
    try:
        # Generate subscription ID
        subscription_id = f"sub-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user[:8]}"
        
        # Create subscription
        subscription = EventSubscription(
            subscription_id=subscription_id,
            name=subscription_data.name,
            description=subscription_data.description,
            project_id=subscription_data.project_id,
            event_types=subscription_data.event_types,
            services=subscription_data.services,
            regions=subscription_data.regions,
            severity_levels=subscription_data.severity_levels,
            custom_filters=subscription_data.custom_filters,
            enabled=subscription_data.enabled,
            auto_resolve=subscription_data.auto_resolve,
            resolve_after_hours=subscription_data.resolve_after_hours,
            tenant_id="default",  # TODO: Get from user context
            created_by=current_user
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        return EventSubscriptionResponse.from_orm(subscription)
        
    except Exception as e:
        logger.error(f"Error creating event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating event subscription: {str(e)}")


@router.get("/subscriptions", response_model=EventSubscriptionListResponse)
async def list_event_subscriptions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = None,
    enabled: Optional[bool] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List event subscriptions"""
    try:
        # Build query
        query = select(EventSubscription).where(EventSubscription.tenant_id == "default")
        
        if project_id:
            query = query.where(EventSubscription.project_id == project_id)
        if enabled is not None:
            query = query.where(EventSubscription.enabled == enabled)
        
        # Get total count
        count_query = select(func.count(EventSubscription.subscription_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        subscriptions = result.scalars().all()
        
        return EventSubscriptionListResponse(
            subscriptions=[EventSubscriptionResponse.from_orm(sub) for sub in subscriptions],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing event subscriptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing event subscriptions: {str(e)}")


@router.get("/subscriptions/{subscription_id}", response_model=EventSubscriptionResponse)
async def get_event_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific event subscription"""
    try:
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        return EventSubscriptionResponse.from_orm(subscription)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting event subscription: {str(e)}")


@router.put("/subscriptions/{subscription_id}", response_model=EventSubscriptionResponse)
async def update_event_subscription(
    subscription_id: str,
    subscription_data: EventSubscriptionUpdate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an event subscription"""
    try:
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        # Update fields
        update_data = subscription_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)
        
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(subscription)
        
        return EventSubscriptionResponse.from_orm(subscription)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating event subscription: {str(e)}")


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an event subscription"""
    try:
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        await db.delete(subscription)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting event subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/enable")
async def enable_event_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable an event subscription"""
    try:
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        subscription.enabled = True
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Event subscription enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error enabling event subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/disable")
async def disable_event_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable an event subscription"""
    try:
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        subscription.enabled = False
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Event subscription disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error disabling event subscription: {str(e)}")


@router.get("/subscriptions/{subscription_id}/test")
async def test_event_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test an event subscription by sending a test event"""
    try:
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        # Create a test event
        test_event = {
            "event_type": "test_event",
            "severity": "info",
            "cloud_provider": "test",
            "title": "Test Event",
            "description": "This is a test event for subscription validation",
            "summary": "Test event for subscription",
            "raw_data": {
                "test": True,
                "subscription_id": subscription_id
            }
        }
        
        # Process the test event through the subscription
        from app.services.event_processor import EventProcessor
        processor = EventProcessor(db)
        
        # Check if the test event would match the subscription
        matches = await processor.check_event_matches_subscription(test_event, subscription)
        
        return {
            "subscription_id": subscription_id,
            "test_event": test_event,
            "matches": matches,
            "message": "Test event would match subscription" if matches else "Test event would not match subscription"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing event subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing event subscription: {str(e)}")


@router.get("/subscriptions/{subscription_id}/events")
async def get_subscription_events(
    subscription_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get events for a specific subscription"""
    try:
        # First check if subscription exists
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        # Get events for this subscription
        from app.db.schemas import CloudEvent
        
        query = select(CloudEvent).where(
            and_(
                CloudEvent.subscription_id == subscription_id,
                CloudEvent.tenant_id == "default"
            )
        ).order_by(CloudEvent.event_time.desc())
        
        # Get total count
        count_query = select(func.count(CloudEvent.event_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Convert to response format
        from app.models.events import CloudEventResponse
        event_responses = []
        for event in events:
            event_responses.append(CloudEventResponse.from_orm(event))
        
        return {
            "subscription_id": subscription_id,
            "events": event_responses,
            "total": total,
            "page": page,
            "per_page": per_page
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription events: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting subscription events: {str(e)}")


@router.get("/subscriptions/{subscription_id}/stats")
async def get_subscription_stats(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for a specific subscription"""
    try:
        # First check if subscription exists
        result = await db.execute(
            select(EventSubscription).where(
                and_(
                    EventSubscription.subscription_id == subscription_id,
                    EventSubscription.tenant_id == "default"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Event subscription not found")
        
        # Get statistics
        from app.db.schemas import CloudEvent
        from datetime import datetime, timedelta
        
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Total events
        total_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.subscription_id == subscription_id,
                CloudEvent.tenant_id == "default"
            )
        )
        total_events = await db.scalar(total_query)
        
        # Events in last 24 hours
        last_24h_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.subscription_id == subscription_id,
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= last_24h
            )
        )
        events_24h = await db.scalar(last_24h_query)
        
        # Events in last 7 days
        last_7d_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.subscription_id == subscription_id,
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= last_7d
            )
        )
        events_7d = await db.scalar(last_7d_query)
        
        # Events in last 30 days
        last_30d_query = select(func.count(CloudEvent.event_id)).where(
            and_(
                CloudEvent.subscription_id == subscription_id,
                CloudEvent.tenant_id == "default",
                CloudEvent.event_time >= last_30d
            )
        )
        events_30d = await db.scalar(last_30d_query)
        
        # Events by severity
        severity_query = select(
            CloudEvent.severity,
            func.count(CloudEvent.event_id)
        ).where(
            and_(
                CloudEvent.subscription_id == subscription_id,
                CloudEvent.tenant_id == "default"
            )
        ).group_by(CloudEvent.severity)
        
        severity_result = await db.execute(severity_query)
        events_by_severity = {row[0]: row[1] for row in severity_result.all()}
        
        return {
            "subscription_id": subscription_id,
            "total_events": total_events,
            "events_last_24h": events_24h,
            "events_last_7d": events_7d,
            "events_last_30d": events_30d,
            "events_by_severity": events_by_severity,
            "subscription_enabled": subscription.enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting subscription stats: {str(e)}")
