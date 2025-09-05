"""
Incident Management API

This module provides API endpoints for managing product outage incidents,
including creation, updates, status changes, and RSS feed generation.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import desc, and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.db.schemas import Incident as IncidentDB, IncidentUpdate as IncidentUpdateDB
from app.models.events import (
    Incident, IncidentUpdate, IncidentCreate, IncidentUpdateRequest,
    IncidentUpdateCreate, IncidentResponse, IncidentListResponse,
    IncidentStatus, IncidentSeverity, IncidentType, RSSFeedConfig
)
from app.services.cloud_event_service import create_cloud_event
from app.services.rss_service import generate_rss_feed

router = APIRouter(prefix="/incidents", tags=["incidents"])
logger = logging.getLogger(__name__)


def generate_incident_id() -> str:
    """Generate a unique incident ID"""
    return f"incident-{uuid.uuid4().hex[:8]}"


def generate_update_id() -> str:
    """Generate a unique update ID"""
    return f"update-{uuid.uuid4().hex[:8]}"


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"  # TODO: Replace with actual auth
):
    """Create a new incident"""
    try:
        # Create incident record
        incident_id = generate_incident_id()
        db_incident = IncidentDB(
            incident_id=incident_id,
            title=incident_data.title,
            description=incident_data.description,
            status=IncidentStatus.INVESTIGATING,  # Always start with investigating
            severity=incident_data.severity,
            incident_type=incident_data.incident_type,
            affected_services=incident_data.affected_services,
            affected_regions=incident_data.affected_regions or [],
            affected_components=incident_data.affected_components or [],
            start_time=incident_data.start_time,
            estimated_resolution=incident_data.estimated_resolution,
            public_message=incident_data.public_message,
            internal_notes=incident_data.internal_notes,
            created_by=current_user,
            assigned_to=incident_data.assigned_to,
            tags=incident_data.tags or [],
            is_public=incident_data.is_public,
            rss_enabled=incident_data.rss_enabled
        )
        
        db.add(db_incident)
        await db.commit()
        await db.refresh(db_incident)
        
        # Create initial status update
        initial_update = IncidentUpdateDB(
            update_id=generate_update_id(),
            incident_id=incident_id,
            status=db_incident.status,
            message=f"Incident created: {incident_data.description}",
            public_message=f"Incident reported: {incident_data.public_message}",
            internal_notes="Initial incident creation",
            update_type="incident_created",
            created_by=current_user,
            is_public=True
        )
        
        db.add(initial_update)
        await db.commit()
        
        # Create CloudEvent for incident
        # event_data = {
        #     "incident_id": incident_id,
        #     "title": incident_data.title,
        #     "status": db_incident.status,
        #     "severity": incident_data.severity,
        #     "affected_services": incident_data.affected_services,
        #     "start_time": incident_data.start_time.isoformat()
        # }
        
        # cloud_event = await create_cloud_event(
        #     event_type="incident.created",
        #     source="incident-management",
        #     data=event_data,
        #     subject=incident_id
        # )
        
        # db_incident.event_id = str(cloud_event["id"])
        # db_incident.event_source = str(cloud_event["source"])
        # await db.commit()
        
        # Convert to Pydantic models for response
        incident = Incident(
            id=db_incident.incident_id,
            title=db_incident.title,
            description=db_incident.description,
            status=db_incident.status,
            severity=db_incident.severity,
            incident_type=db_incident.incident_type,
            affected_services=db_incident.affected_services,
            affected_regions=db_incident.affected_regions,
            affected_components=db_incident.affected_components,
            start_time=db_incident.start_time,
            end_time=db_incident.end_time,
            estimated_resolution=db_incident.estimated_resolution,
            public_message=db_incident.public_message,
            internal_notes=db_incident.internal_notes,
            created_by=db_incident.created_by,
            assigned_to=db_incident.assigned_to,
            tags=db_incident.tags,
            is_public=db_incident.is_public,
            rss_enabled=db_incident.rss_enabled,
            event_id=db_incident.event_id,
            event_source=db_incident.event_source,
            created_at=db_incident.created_at,
            updated_at=db_incident.updated_at,
            updates=[]
        )
        
        incident.updates = [IncidentUpdate(
            id=initial_update.update_id,
            incident_id=initial_update.incident_id,
            status=initial_update.status,
            message=initial_update.message,
            public_message=initial_update.public_message,
            internal_notes=initial_update.internal_notes,
            update_type=initial_update.update_type,
            created_by=initial_update.created_by,
            is_public=initial_update.is_public,
            created_at=initial_update.created_at
        )]
        
        last_update = IncidentUpdate(
            id=initial_update.update_id,
            incident_id=initial_update.incident_id,
            status=initial_update.status,
            message=initial_update.message,
            public_message=initial_update.public_message,
            internal_notes=initial_update.internal_notes,
            update_type=initial_update.update_type,
            created_by=initial_update.created_by,
            is_public=initial_update.is_public,
            created_at=initial_update.created_at
        )
        
        return IncidentResponse(
            incident=incident,
            total_updates=1,
            last_update=last_update
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create incident: {str(e)}"
        )


@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[IncidentStatus] = Query(None, description="Filter by status"),
    severity: Optional[IncidentSeverity] = Query(None, description="Filter by severity"),
    incident_type: Optional[IncidentType] = Query(None, description="Filter by incident type"),
    service: Optional[str] = Query(None, description="Filter by affected service"),
    region: Optional[str] = Query(None, description="Filter by affected region"),
    is_public: Optional[bool] = Query(None, description="Filter by public visibility"),
    db: AsyncSession = Depends(get_db)
):
    """List incidents with filtering and pagination"""
    try:
        # Build query
        query = select(IncidentDB)
        
        # Apply filters
        if status:
            query = query.where(IncidentDB.status == status)
        if severity:
            query = query.where(IncidentDB.severity == severity)
        if incident_type:
            query = query.where(IncidentDB.incident_type == incident_type)
        if service:
            query = query.where(IncidentDB.affected_services.contains([service]))
        if region:
            query = query.where(IncidentDB.affected_regions.contains([region]))
        if is_public is not None:
            query = query.where(IncidentDB.is_public == is_public)
        
        # Get total count
        count_query = select(func.count(IncidentDB.incident_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Apply pagination and ordering
        query = query.order_by(desc(IncidentDB.start_time)) \
                        .offset((page - 1) * per_page) \
                        .limit(per_page)
        
        result = await db.execute(query)
        incidents = result.scalars().all()
        
        # Convert to response models
        incident_models = []
        for incident in incidents:
            incident_model = Incident(
                id=incident.incident_id,
                title=incident.title,
                description=incident.description,
                status=incident.status,
                severity=incident.severity,
                incident_type=incident.incident_type,
                affected_services=incident.affected_services,
                affected_regions=incident.affected_regions,
                affected_components=incident.affected_components,
                start_time=incident.start_time,
                end_time=incident.end_time,
                estimated_resolution=incident.estimated_resolution,
                public_message=incident.public_message,
                internal_notes=incident.internal_notes,
                created_by=incident.created_by,
                assigned_to=incident.assigned_to,
                tags=incident.tags,
                is_public=incident.is_public,
                rss_enabled=incident.rss_enabled,
                event_id=incident.event_id,
                event_source=incident.event_source,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
                updates=[]
            )
            
            # Load updates for each incident
            updates_query = select(IncidentUpdateDB) \
                           .where(IncidentUpdateDB.incident_id == incident.incident_id) \
                           .order_by(desc(IncidentUpdateDB.created_at))
            updates_result = await db.execute(updates_query)
            updates = updates_result.scalars().all()
            
            incident_model.updates = [IncidentUpdate(
                id=update.update_id,
                incident_id=update.incident_id,
                status=update.status,
                message=update.message,
                public_message=update.public_message,
                internal_notes=update.internal_notes,
                update_type=update.update_type,
                created_by=update.created_by,
                is_public=update.is_public,
                created_at=update.created_at
            ) for update in updates]
            
            incident_models.append(incident_model)
        
        return IncidentListResponse(
            incidents=incident_models,
            total=total,
            page=page,
            per_page=per_page,
            has_next=page * per_page < total,
            has_prev=page > 1
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list incidents: {str(e)}"
        )


class LinkIncidentRequest(BaseModel):
    outage_id: str
    incident_id: str

# In-memory storage for demo (in production, use database)
outage_incident_links = {}

@router.post("/link-incident")
async def link_incident_to_outage(request: LinkIncidentRequest):
    """Link an incident to an outage for tracking purposes"""
    try:
        outage_incident_links[request.outage_id] = request.incident_id
        logger.info(f"Linked incident {request.incident_id} to outage {request.outage_id}")
        return {"success": True, "message": "Incident linked to outage successfully"}
    except Exception as e:
        logger.error(f"Failed to link incident to outage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific incident by ID"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Load updates
        updates_query = select(IncidentUpdateDB) \
                       .where(IncidentUpdateDB.incident_id == incident_id) \
                       .order_by(desc(IncidentUpdateDB.created_at))
        updates_result = await db.execute(updates_query)
        updates = updates_result.scalars().all()
        
        incident_model = Incident(
            id=incident.incident_id,
            title=incident.title,
            description=incident.description,
            status=incident.status,
            severity=incident.severity,
            incident_type=incident.incident_type,
            affected_services=incident.affected_services,
            affected_regions=incident.affected_regions,
            affected_components=incident.affected_components,
            start_time=incident.start_time,
            end_time=incident.end_time,
            estimated_resolution=incident.estimated_resolution,
            public_message=incident.public_message,
            internal_notes=incident.internal_notes,
            created_by=incident.created_by,
            assigned_to=incident.assigned_to,
            tags=incident.tags,
            is_public=incident.is_public,
            rss_enabled=incident.rss_enabled,
            event_id=incident.event_id,
            event_source=incident.event_source,
            created_at=incident.created_at,
            updated_at=incident.updated_at,
            updates=[]
        )
        
        incident_model.updates = [IncidentUpdate(
            id=update.update_id,
            incident_id=update.incident_id,
            status=update.status,
            message=update.message,
            public_message=update.public_message,
            internal_notes=update.internal_notes,
            update_type=update.update_type,
            created_by=update.created_by,
            is_public=update.is_public,
            created_at=update.created_at
        ) for update in updates]
        
        last_update = IncidentUpdate(
            id=updates[0].update_id,
            incident_id=updates[0].incident_id,
            status=updates[0].status,
            message=updates[0].message,
            public_message=updates[0].public_message,
            internal_notes=updates[0].internal_notes,
            update_type=updates[0].update_type,
            created_by=updates[0].created_by,
            is_public=updates[0].is_public,
            created_at=updates[0].created_at
        ) if updates else None
        
        return IncidentResponse(
            incident=incident_model,
            total_updates=len(updates),
            last_update=last_update
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incident: {str(e)}"
        )


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    incident_data: IncidentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"  # TODO: Replace with actual auth
):
    """Update an existing incident"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Update fields if provided
        update_fields = incident_data.model_dump(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(incident, field, value)
        
        incident.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(incident)
        
        # Create update record if status changed
        if 'status' in update_fields:
            update_record = IncidentUpdateDB(
                update_id=generate_update_id(),
                incident_id=incident_id,
                status=incident.status,
                message=f"Status updated to {incident.status}",
                public_message=f"Status: {incident.status}",
                internal_notes=f"Status updated by {current_user}",
                update_type="status_change",
                created_by=current_user,
                is_public=True
            )
            db.add(update_record)
            await db.commit()
        
        # Create CloudEvent for incident update
        event_data = {
            "incident_id": incident_id,
            "status": incident.status,
            "updated_fields": list(update_fields.keys()),
            "updated_at": incident.updated_at.isoformat()
        }
        
        await create_cloud_event(
            event_type="incident.updated",
            source="incident-management",
            data=event_data,
            subject=incident_id
        )
        
        # Return updated incident
        return await get_incident(incident_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update incident: {str(e)}"
        )


@router.post("/{incident_id}/updates", response_model=IncidentResponse)
async def add_incident_update(
    incident_id: str,
    update_data: IncidentUpdateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"  # TODO: Replace with actual auth
):
    """Add a new update to an incident"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Create update record
        update_record = IncidentUpdateDB(
            update_id=generate_update_id(),
            incident_id=incident_id,
            status=update_data.status,
            message=update_data.message,
            public_message=update_data.public_message,
            internal_notes=update_data.internal_notes,
            update_type=update_data.update_type,
            created_by=current_user,
            is_public=update_data.is_public,
            affected_services=update_data.affected_services,
            affected_regions=update_data.affected_regions,
            estimated_resolution=update_data.estimated_resolution
        )
        
        db.add(update_record)
        
        # Update incident status if provided
        if update_data.status != incident.status:
            incident.status = update_data.status
            incident.updated_at = datetime.now(timezone.utc)
        
        # Update other fields if provided
        if update_data.affected_services:
            incident.affected_services = update_data.affected_services
        if update_data.affected_regions:
            incident.affected_regions = update_data.affected_regions
        if update_data.estimated_resolution:
            incident.estimated_resolution = update_data.estimated_resolution
        
        await db.commit()
        
        # Create CloudEvent for update
        event_data = {
            "incident_id": incident_id,
            "update_id": update_record.update_id,
            "status": update_data.status,
            "message": update_data.public_message,
            "update_type": update_data.update_type
        }
        
        await create_cloud_event(
            event_type="incident.update_added",
            source="incident-management",
            data=event_data,
            subject=incident_id
        )
        
        # Return updated incident
        return await get_incident(incident_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add incident update: {str(e)}"
        )


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = "system"  # TODO: Replace with actual auth
):
    """Delete an incident (soft delete by setting is_public=False)"""
    try:
        query = select(IncidentDB).where(IncidentDB.incident_id == incident_id)
        result = await db.execute(query)
        incident = result.scalar_one_or_none()
        
        if not incident:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found"
            )
        
        # Soft delete by making it non-public
        incident.is_public = False
        incident.rss_enabled = False
        incident.updated_at = datetime.now(timezone.utc)
        
        # Add deletion update
        update_record = IncidentUpdateDB(
            update_id=generate_update_id(),
            incident_id=incident_id,
            status=incident.status,
            message="Incident deleted",
            public_message="Incident removed from public view",
            internal_notes=f"Incident deleted by {current_user}",
            update_type="incident_deleted",
            created_by=current_user,
            is_public=False
        )
        
        db.add(update_record)
        await db.commit()
        
        # Create CloudEvent for deletion
        event_data = {
            "incident_id": incident_id,
            "deleted_by": current_user,
            "deleted_at": incident.updated_at.isoformat()
        }
        
        await create_cloud_event(
            event_type="incident.deleted",
            source="incident-management",
            data=event_data,
            subject=incident_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete incident: {str(e)}"
        )


@router.get("/rss/feed", response_class=PlainTextResponse)
async def get_rss_feed(
    db: AsyncSession = Depends(get_db),
    include_resolved: bool = Query(False, description="Include resolved incidents"),
    max_items: int = Query(50, ge=1, le=100, description="Maximum items in feed")
):
    """Get RSS feed of public incidents"""
    try:
        # Query public incidents
        query = select(IncidentDB).where(
            and_(
                IncidentDB.is_public == True,
                IncidentDB.rss_enabled == True
            )
        )
        
        if not include_resolved:
            query = query.where(IncidentDB.status != IncidentStatus.RESOLVED)
        
        query = query.order_by(desc(IncidentDB.start_time)).limit(max_items)
        result = await db.execute(query)
        incidents = result.scalars().all()
        
        # Generate RSS feed
        rss_content = await generate_rss_feed(incidents, db)
        
        return PlainTextResponse(
            content=rss_content,
            media_type="application/rss+xml"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate RSS feed: {str(e)}"
        )


@router.get("/status/summary")
async def get_incident_summary(db: AsyncSession = Depends(get_db)):
    """Get summary of current incidents"""
    try:
        # Count incidents by status
        status_query = select(
            IncidentDB.status,
            func.count(IncidentDB.incident_id)
        ).where(IncidentDB.is_public == True).group_by(IncidentDB.status)
        
        status_result = await db.execute(status_query)
        status_counts = status_result.all()
        
        # Count incidents by severity
        severity_query = select(
            IncidentDB.severity,
            func.count(IncidentDB.incident_id)
        ).where(
            and_(
                IncidentDB.is_public == True,
                IncidentDB.status != IncidentStatus.RESOLVED
            )
        ).group_by(IncidentDB.severity)
        
        severity_result = await db.execute(severity_query)
        severity_counts = severity_result.all()
        
        # Get recent incidents
        recent_query = select(IncidentDB).where(
            and_(
                IncidentDB.is_public == True,
                IncidentDB.status != IncidentStatus.RESOLVED
            )
        ).order_by(desc(IncidentDB.start_time)).limit(5)
        
        recent_result = await db.execute(recent_query)
        recent_incidents = recent_result.scalars().all()
        
        return {
            "status_counts": dict(status_counts),
            "severity_counts": dict(severity_counts),
            "total_active": sum(count for _, count in status_counts if _ != IncidentStatus.RESOLVED),
            "total_resolved": next((count for status, count in status_counts if status == IncidentStatus.RESOLVED), 0),
            "recent_incidents": [
                {
                    "id": incident.incident_id,
                    "title": incident.title,
                    "status": incident.status,
                    "severity": incident.severity,
                    "start_time": incident.start_time.isoformat()
                }
                for incident in recent_incidents
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get incident summary: {str(e)}"
        )
