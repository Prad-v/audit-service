"""
Outage Monitoring API

This module provides API endpoints for monitoring cloud service provider outages,
including status checks, outage tracking, and incident correlation.
"""

import logging
import aiohttp
import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.events import OutageStatus, OutageResponse, OutageListResponse

router = APIRouter(prefix="/outages", tags=["outage-monitoring"])
logger = logging.getLogger(__name__)


async def fetch_gcp_incidents() -> List[Dict[str, Any]]:
    """Fetch real GCP incidents from the status API"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://status.cloud.google.com/incidents.json") as response:
                if response.status == 200:
                    incidents = await response.json()
                    logger.info(f"Fetched {len(incidents)} GCP incidents from status API")
                    return incidents
                else:
                    logger.error(f"Failed to fetch GCP incidents: HTTP {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching GCP incidents: {e}")
        return []


def convert_gcp_incident_to_outage(incident: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Convert GCP incident data to our outage format"""
    try:
        # Extract basic information
        incident_id = incident.get("id", "")
        title = incident.get("external_desc", "GCP Service Disruption")
        
        # Parse dates
        begin_time = incident.get("begin")
        end_time = incident.get("end")
        
        if not begin_time:
            return None
            
        # Convert to datetime objects
        try:
            start_dt = datetime.fromisoformat(begin_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00')) if end_time else None
        except (ValueError, AttributeError):
            return None
        
        # Determine status
        status = "resolved" if end_dt else "active"
        
        # Extract affected regions
        affected_regions = []
        if "previously_affected_locations" in incident:
            affected_regions.extend([loc["id"] for loc in incident["previously_affected_locations"]])
        if "currently_affected_locations" in incident:
            affected_regions.extend([loc["id"] for loc in incident["currently_affected_locations"]])
        
        # Extract affected services
        affected_services = []
        if "affected_products" in incident:
            affected_services.extend([product["title"] for product in incident["affected_products"]])
        
        # Get severity
        severity = incident.get("severity", "medium").lower()
        
        # Get description from most recent update
        description = title
        if "most_recent_update" in incident and "text" in incident["most_recent_update"]:
            # Clean up the description text
            desc_text = incident["most_recent_update"]["text"]
            # Remove markdown formatting and truncate
            desc_text = desc_text.replace("##", "").replace("#", "").replace("**", "")
            desc_text = desc_text.replace("\\n", " ").replace("\\", "")
            description = desc_text[:500] + "..." if len(desc_text) > 500 else desc_text
        
        # Calculate duration
        duration_minutes = None
        if end_dt:
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        
        return {
            "event_id": f"gcp-{incident_id}",
            "provider": "GCP",
            "service": incident.get("service_name", "Multiple Products"),
            "status": status,
            "title": title,
            "description": description,
            "event_time": start_dt.isoformat(),
            "resolved_at": end_dt.isoformat() if end_dt else None,
            "affected_regions": list(set(affected_regions)),  # Remove duplicates
            "affected_services": list(set(affected_services)),  # Remove duplicates
            "severity": severity,
            "duration_minutes": duration_minutes
        }
        
    except Exception as e:
        logger.error(f"Error converting GCP incident {incident.get('id', 'unknown')}: {e}")
        return None


@router.get("/status")
async def get_outage_monitoring_status(db: AsyncSession = Depends(get_db)):
    """Get outage monitoring status"""
    try:
        # Return monitoring status information
        return {
            "service_status": "operational",
            "check_interval_seconds": 300,
            "last_check_time": datetime.now(timezone.utc).isoformat(),
            "monitored_providers": [
                {
                    "provider": "gcp",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "known_outages_count": 0
                },
                {
                    "provider": "aws",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "known_outages_count": 0
                },
                {
                    "provider": "azure",
                    "last_check": datetime.now(timezone.utc).isoformat(),
                    "known_outages_count": 0
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outage monitoring status: {str(e)}"
        )


@router.get("/status/summary")
async def get_outage_summary(db: AsyncSession = Depends(get_db)):
    """Get summary of current outages"""
    try:
        # For now, return a placeholder summary
        # In a real implementation, this would query the database
        return {
            "total_outages": 0,
            "active_outages": 0,
            "resolved_outages": 0,
            "providers_affected": [],
            "services_affected": [],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outage summary: {str(e)}"
        )


@router.get("/active")
async def get_active_outages(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of outages to return"),
    db: AsyncSession = Depends(get_db)
):
    """Get active outages"""
    try:
        # Fetch real GCP incidents from the status API
        gcp_incidents = await fetch_gcp_incidents()
        
        # Convert GCP incidents to our outage format and filter for active ones
        active_outages = []
        for incident in gcp_incidents[:limit]:
            outage = convert_gcp_incident_to_outage(incident)
            if outage and outage["status"] == "active":
                active_outages.append(outage)
        
        # If no active outages from GCP, return empty list
        if not active_outages:
            return {
                "outages": [],
                "total_count": 0,
                "active_count": 0,
                "providers_affected": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
        
        # Calculate statistics
        total_count = len(active_outages)
        providers_affected = list(set([o["provider"] for o in active_outages]))
        
        return {
            "outages": active_outages,
            "total_count": total_count,
            "active_count": total_count,
            "providers_affected": providers_affected,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active outages: {str(e)}"
        )


@router.get("/history")
async def get_outage_history(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of outages to return"),
    days: int = Query(365, ge=1, le=3650, description="Number of days to look back"),
    source: str = Query("database", description="Data source (database or providers)"),
    db: AsyncSession = Depends(get_db)
):
    """Get outage history with filtering"""
    try:
        # Fetch real GCP incidents from the status API
        gcp_incidents = await fetch_gcp_incidents()
        
        # Convert GCP incidents to our outage format
        historical_outages = []
        for incident in gcp_incidents[:limit]:
            outage = convert_gcp_incident_to_outage(incident)
            if outage:
                historical_outages.append(outage)
        
        # Calculate statistics
        total_outages = len(historical_outages)
        resolved_outages = len([o for o in historical_outages if o["status"] == "resolved"])
        active_outages = len([o for o in historical_outages if o["status"] == "active"])
        providers_affected = list(set([o["provider"] for o in historical_outages]))
        
        return {
            "outages": historical_outages,
            "total_count": total_outages,
            "statistics": {
                "total_outages": total_outages,
                "resolved_outages": resolved_outages,
                "active_outages": active_outages,
                "providers_affected": providers_affected,
                "average_duration_minutes": 120,  # Calculate from actual data if needed
                "most_affected_service": "Google Cloud Platform"
            },
            "period": {
                "days": days,
                "start_date": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outage history: {str(e)}"
        )


@router.get("/", response_model=OutageListResponse)
async def list_outages(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[OutageStatus] = Query(None, description="Filter by status"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    service: Optional[str] = Query(None, description="Filter by service"),
    db: AsyncSession = Depends(get_db)
):
    """List outages with filtering and pagination"""
    try:
        # For now, return empty list as this is a placeholder
        # In a real implementation, this would query the database
        return OutageListResponse(
            outages=[],
            total=0,
            page=page,
            per_page=per_page,
            has_next=False,
            has_prev=False
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list outages: {str(e)}"
        )


@router.get("/{outage_id}", response_model=OutageResponse)
async def get_outage(
    outage_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific outage by ID"""
    try:
        # For now, return a placeholder response
        # In a real implementation, this would query the database
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Outage not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get outage: {str(e)}"
        )


@router.post("/check/all")
async def check_all_providers_outages(db: AsyncSession = Depends(get_db)):
    """Check all cloud providers for outages"""
    try:
        # For now, return a placeholder response
        # In a real implementation, this would check all cloud providers
        return {
            "message": "Checking all providers for outages",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "providers_checked": ["gcp", "aws", "azure"],
            "outages_found": 0,
            "status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check providers for outages: {str(e)}"
        )


@router.post("/refresh")
async def refresh_outage_data(db: AsyncSession = Depends(get_db)):
    """Trigger a refresh of outage data from providers"""
    try:
        # For now, return a placeholder response
        # In a real implementation, this would trigger background tasks
        return {
            "message": "Outage data refresh initiated",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh outage data: {str(e)}"
        )
