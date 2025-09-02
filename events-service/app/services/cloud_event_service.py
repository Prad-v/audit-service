"""
CloudEvent Service for Incident Management

This module provides functionality to create and manage CloudEvents
for incident lifecycle events and updates.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from cloudevents.http import CloudEvent
from cloudevents.conversion import to_structured


async def create_cloud_event(
    event_type: str,
    source: str,
    data: Dict[str, Any],
    subject: Optional[str] = None,
    id: Optional[str] = None,
    time: Optional[datetime] = None
) -> CloudEvent:
    """Create a CloudEvent for incident management"""
    
    # Generate event ID if not provided
    if not id:
        id = str(uuid.uuid4())
    
    # Use current time if not provided
    if not time:
        time = datetime.now(timezone.utc)
    
    # Create CloudEvent
    event = CloudEvent(
        {
            "type": event_type,
            "source": source,
            "id": id,
            "time": time.isoformat(),
            "datacontenttype": "application/json",
            "specversion": "1.0"
        },
        data
    )
    
    # Add subject if provided
    if subject:
        event["subject"] = subject
    
    return event


async def create_incident_created_event(
    incident_id: str,
    title: str,
    status: str,
    severity: str,
    affected_services: list,
    start_time: datetime
) -> CloudEvent:
    """Create CloudEvent for incident creation"""
    
    event_data = {
        "incident_id": incident_id,
        "title": title,
        "status": status,
        "severity": severity,
        "affected_services": affected_services,
        "start_time": start_time.isoformat(),
        "event_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return await create_cloud_event(
        event_type="com.example.incident.created",
        source="/incident-management",
        data=event_data,
        subject=incident_id
    )


async def create_incident_updated_event(
    incident_id: str,
    status: str,
    updated_fields: list,
    updated_at: datetime
) -> CloudEvent:
    """Create CloudEvent for incident updates"""
    
    event_data = {
        "incident_id": incident_id,
        "status": status,
        "updated_fields": updated_fields,
        "updated_at": updated_at.isoformat(),
        "event_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return await create_cloud_event(
        event_type="com.example.incident.updated",
        source="/incident-management",
        data=event_data,
        subject=incident_id
    )


async def create_incident_update_added_event(
    incident_id: str,
    update_id: str,
    status: str,
    message: str,
    update_type: str
) -> CloudEvent:
    """Create CloudEvent for incident update addition"""
    
    event_data = {
        "incident_id": incident_id,
        "update_id": update_id,
        "status": status,
        "message": message,
        "update_type": update_type,
        "event_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return await create_cloud_event(
        event_type="com.example.incident.update_added",
        source="/incident-management",
        data=event_data,
        subject=incident_id
    )


async def create_incident_resolved_event(
    incident_id: str,
    resolution_time: datetime,
    resolution_summary: str
) -> CloudEvent:
    """Create CloudEvent for incident resolution"""
    
    event_data = {
        "incident_id": incident_id,
        "resolution_time": resolution_time.isoformat(),
        "resolution_summary": resolution_summary,
        "event_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return await create_cloud_event(
        event_type="com.example.incident.resolved",
        source="/incident-management",
        data=event_data,
        subject=incident_id
    )


async def create_incident_deleted_event(
    incident_id: str,
    deleted_by: str,
    deleted_at: datetime
) -> CloudEvent:
    """Create CloudEvent for incident deletion"""
    
    event_data = {
        "incident_id": incident_id,
        "deleted_by": deleted_by,
        "deleted_at": deleted_at.isoformat(),
        "event_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    return await create_cloud_event(
        event_type="com.example.incident.deleted",
        source="/incident-management",
        data=event_data,
        subject=incident_id
    )


def cloud_event_to_dict(event: CloudEvent) -> Dict[str, Any]:
    """Convert CloudEvent to dictionary format"""
    return {
        "id": event["id"],
        "type": event["type"],
        "source": event["source"],
        "subject": event.get("subject"),
        "time": event["time"],
        "data": event.data,
        "specversion": event["specversion"]
    }


def cloud_event_to_json(event: CloudEvent) -> str:
    """Convert CloudEvent to JSON string"""
    import json
    return json.dumps(cloud_event_to_dict(event), indent=2)


def cloud_event_to_structured(event: CloudEvent) -> Dict[str, Any]:
    """Convert CloudEvent to structured format for HTTP transport"""
    return to_structured(event)
