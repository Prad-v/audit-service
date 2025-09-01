"""
Outage Monitoring API Endpoints

This module provides API endpoints for managing multi-cloud outage monitoring.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.database import get_db
from app.services.outage_monitor import (
    OutageMonitoringService, 
    OutageEvent, 
    OutageSource,
    OutageStatus
)
from app.models.events import CloudProvider
from app.core.auth import get_current_user
from app.services.background_tasks import background_task_manager
from sqlalchemy import select, delete, and_, text
from app.models.events import CloudEvent, EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outages", tags=["outage-monitoring"])


@router.post("/check/all")
async def check_all_providers_outages(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually check all cloud providers for outages
    """
    try:
        all_outages = []
        provider_results = {}
        
        for provider in CloudProvider:
            try:
                logger.info(f"Checking {provider.value} for outages...")
                outages = await background_task_manager.manual_check_outages(db, provider)
                all_outages.extend(outages)
                
                # Get monitor details from the background task manager
                monitor = background_task_manager.outage_service.monitors[provider]
                
                provider_results[provider.value] = {
                    "status": "success",
                    "outages_found": len(outages),
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "details": {
                        "rss_feed": getattr(monitor, 'status_page_url', 'N/A'),
                        "api_url": getattr(monitor, 'api_url', 'N/A')
                    }
                }
                
                # Process outages in background
                for outage in outages:
                    background_tasks.add_task(background_task_manager.outage_service.process_outage, outage)
                    
            except Exception as provider_error:
                logger.error(f"Error checking {provider.value}: {provider_error}")
                provider_results[provider.value] = {
                    "status": "error",
                    "error": str(provider_error),
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "outages_found": 0
                }
                # Continue with other providers even if one fails
                continue
        
        return {
            "message": "Checked all providers for outages",
            "total_outages_found": len(all_outages),
            "outages_by_provider": {
                provider.value: len([o for o in all_outages if o.provider == provider])
                for provider in CloudProvider
            },
            "provider_results": provider_results,
            "outages": [
                {
                    "provider": outage.provider.value,
                    "service": outage.service,
                    "region": outage.region,
                    "status": outage.status.value,
                    "severity": outage.severity.value,
                    "title": outage.title,
                    "start_time": outage.start_time.isoformat(),
                    "source": outage.source.value
                }
                for outage in all_outages
            ]
        }
    except Exception as e:
        logger.error(f"Error checking all providers for outages: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking outages: {str(e)}")


@router.post("/check/{provider}")
async def check_provider_outages(
    provider: CloudProvider,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually check a specific cloud provider for outages
    """
    try:
        outage_service = OutageMonitoringService(db)
        outages = await outage_service.manual_check(provider)
        
        # Process outages in background
        for outage in outages:
            background_tasks.add_task(outage_service.process_outage, outage)
        
        return {
            "message": f"Checked {provider.value} for outages",
            "outages_found": len(outages),
            "outages": [
                {
                    "provider": outage.provider.value,
                    "service": outage.service,
                    "region": outage.region,
                    "status": outage.status.value,
                    "severity": outage.severity.value,
                    "title": outage.title,
                    "start_time": outage.start_time.isoformat(),
                    "source": outage.source.value
                }
                for outage in outages
            ]
        }
    except Exception as e:
        logger.error(f"Error checking outages for {provider.value}: {e}")
        raise HTTPException(status_code=500, detail=f"Error checking outages: {str(e)}")


@router.get("/status")
async def get_outage_monitoring_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current status of outage monitoring service
    """
    try:
        return await background_task_manager.get_outage_monitoring_status()
    except Exception as e:
        logger.error(f"Error getting outage monitoring status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.post("/start")
async def start_outage_monitoring(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start the outage monitoring service
    """
    try:
        outage_service = OutageMonitoringService(db)
        
        if outage_service.running:
            return {"message": "Outage monitoring service is already running"}
        
        # Start monitoring in background
        background_tasks.add_task(outage_service.start_monitoring)
        
        return {"message": "Outage monitoring service started"}
    except Exception as e:
        logger.error(f"Error starting outage monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting monitoring: {str(e)}")


@router.post("/pause")
async def pause_outage_monitoring(
    db: AsyncSession = Depends(get_db)
):
    """
    Pause the outage monitoring service
    """
    try:
        outage_service = OutageMonitoringService(db)
        
        if not outage_service.running:
            return {"message": "Outage monitoring service is already paused"}
        
        await outage_service.pause_monitoring()
        
        return {"message": "Outage monitoring service paused"}
    except Exception as e:
        logger.error(f"Error pausing outage monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error pausing monitoring: {str(e)}")

@router.post("/resume")
async def resume_outage_monitoring(
    db: AsyncSession = Depends(get_db)
):
    """
    Resume the outage monitoring service
    """
    try:
        outage_service = OutageMonitoringService(db)
        
        if outage_service.running:
            return {"message": "Outage monitoring service is already running"}
        
        await outage_service.resume_monitoring()
        
        return {"message": "Outage monitoring service resumed"}
    except Exception as e:
        logger.error(f"Error resuming outage monitoring: {e}")
        raise HTTPException(status_code=500, detail=f"Error resuming monitoring: {str(e)}")


@router.put("/config")
async def update_outage_monitoring_config(
    check_interval: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Update outage monitoring configuration
    """
    try:
        outage_service = OutageMonitoringService(db)
        
        if check_interval is not None:
            if check_interval < 60:  # Minimum 1 minute
                raise HTTPException(status_code=400, detail="Check interval must be at least 60 seconds")
            outage_service.check_interval = check_interval
        
        return {
            "message": "Outage monitoring configuration updated",
            "check_interval_seconds": outage_service.check_interval
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating outage monitoring config: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating config: {str(e)}")


@router.get("/providers/{provider}/status")
async def get_provider_status(
    provider: CloudProvider,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed status for a specific cloud provider
    """
    try:
        outage_service = OutageMonitoringService(db)
        
        if provider not in outage_service.monitors:
            raise HTTPException(status_code=404, detail=f"Provider {provider.value} not found")
        
        monitor = outage_service.monitors[provider]
        
        return {
            "provider": provider.value,
            "last_check": monitor.last_check.isoformat() if monitor.last_check else None,
            "known_outages_count": len(monitor.known_outages),
            "status_page_url": getattr(monitor, 'status_page_url', None),
            "api_url": getattr(monitor, 'api_url', None)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider status for {provider.value}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting provider status: {str(e)}")


@router.get("/history")
async def get_outage_history(
    provider: Optional[CloudProvider] = None,
    limit: int = 100,
    days: int = 365,
    source: str = "database",  # "database" or "providers"
    db: AsyncSession = Depends(get_db)
):
    """
    Get outage history from the database or directly from cloud provider APIs
    """
    try:
        if source == "providers":
            # Get historical data directly from cloud provider APIs
            from datetime import datetime, timedelta
            
            outage_service = OutageMonitoringService(db)
            
            # Convert provider enum to CloudProvider if specified
            cloud_provider = None
            if provider:
                cloud_provider = CloudProvider(provider.value)
            
            outages = await outage_service.get_historical_outages_from_providers(days, cloud_provider)
            
            # Convert to response format
            outage_list = []
            for outage in outages[:limit]:  # Apply limit
                outage_list.append({
                    "event_id": f"historical-{outage.provider.value}-{outage.external_id}",
                    "provider": outage.provider.value,
                    "service": outage.service,
                    "region": outage.region,
                    "severity": outage.severity.value,
                    "status": outage.status.value,
                    "title": outage.title,
                    "description": outage.description,
                    "event_time": outage.start_time.isoformat(),
                    "resolved_at": outage.end_time.isoformat() if outage.end_time else None,
                    "outage_status": outage.status.value,
                    "affected_services": outage.affected_services,
                    "affected_regions": outage.affected_regions,
                    "raw_data": outage.raw_data
                })
            
            # Calculate statistics
            statistics = {}
            provider_outages = {}
            for outage in outages:
                provider = outage.provider.value
                if provider not in provider_outages:
                    provider_outages[provider] = []
                provider_outages[provider].append(outage)
            
            for provider, provider_outage_list in provider_outages.items():
                if provider_outage_list:
                    first_outage = min(o.start_time for o in provider_outage_list)
                    last_outage = max(o.start_time for o in provider_outage_list)
                    statistics[provider] = {
                        "count": len(provider_outage_list),
                        "first_outage": first_outage.isoformat(),
                        "last_outage": last_outage.isoformat()
                    }
            
            return {
                "outages": outage_list,
                "total_count": len(outage_list),
                "statistics": statistics,
                "period": {
                    "days": days,
                    "start_date": (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(),
                    "end_date": datetime.now(timezone.utc).isoformat()
                },
                "source": "providers"
            }
        
        # Database source (existing logic)
        from sqlalchemy import select, desc, func
        from app.db.schemas import CloudEvent
        from app.models.events import EventType
        from datetime import datetime, timedelta
        
        # Calculate the date from which to fetch data
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        query = select(CloudEvent).where(
            CloudEvent.event_type == EventType.OUTAGE_STATUS,
            CloudEvent.event_time >= start_date
        ).order_by(desc(CloudEvent.event_time)).limit(limit)
        
        if provider:
            query = query.where(CloudEvent.cloud_provider == provider)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        # Convert to response format
        outage_list = []
        for event in events:
            outage_list.append({
                "event_id": event.event_id,
                "provider": event.cloud_provider.value,
                "service": event.service_name,
                "region": event.region,
                "severity": event.severity.value,
                "status": event.status.value,
                "title": event.title,
                "description": event.description,
                "event_time": event.event_time.isoformat(),
                "resolved_at": event.resolved_at.isoformat() if event.resolved_at else None,
                "outage_status": event.raw_data.get("outage_status") if event.raw_data else None,
                "affected_services": event.raw_data.get("affected_services", []) if event.raw_data else [],
                "affected_regions": event.raw_data.get("affected_regions", []) if event.raw_data else [],
                "raw_data": event.raw_data
            })
        
        return {
            "outages": outage_list,
            "total_count": len(outage_list),
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.now(timezone.utc).isoformat()
            },
            "source": "database"
        }
        
    except Exception as e:
        logger.error(f"Error getting outage history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting outage history: {str(e)}")


@router.post("/webhook/test")
async def test_outage_webhook(
    webhook_url: str,
    provider: CloudProvider = CloudProvider.GCP,
    db: AsyncSession = Depends(get_db)
):
    """
    Test outage webhook delivery
    """
    try:
        import aiohttp
        import json
        from datetime import datetime
        
        # Create test outage event
        test_outage = {
            "event_type": "outage_detected",
            "subscription_id": "test-subscription",
            "subscription_name": "Test Outage Subscription",
            "outage": {
                "event_id": f"test-outage-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                "provider": provider.value,
                "service": "test-service",
                "region": "test-region",
                "severity": "high",
                "status": "investigating",
                "title": "Test Outage Event",
                "description": "This is a test outage event for webhook testing",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "affected_services": ["test-service"],
                "affected_regions": ["test-region"]
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Audit-Service-Outage-Monitor/1.0"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=test_outage,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return {
                    "message": "Test webhook sent",
                    "webhook_url": webhook_url,
                    "response_status": response.status,
                    "response_text": await response.text(),
                    "test_data": test_outage
                }
                
    except Exception as e:
        logger.error(f"Error testing outage webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing webhook: {str(e)}")


@router.post("/cleanup-duplicates")
async def cleanup_duplicate_outages(
    db: AsyncSession = Depends(get_db)
):
    """
    Clean up duplicate outage entries from the database
    """
    try:
        # Find duplicates based on title, provider, and service
        duplicate_query = text("""
            WITH duplicates AS (
                SELECT 
                    title,
                    cloud_provider,
                    service_name,
                    COUNT(*) as count
                FROM cloud_events 
                WHERE event_type = 'OUTAGE_STATUS'
                GROUP BY title, cloud_provider, service_name
                HAVING COUNT(*) > 1
            )
            SELECT title, cloud_provider, service_name, count
            FROM duplicates
            ORDER BY count DESC
        """)
        
        result = await db.execute(duplicate_query)
        duplicates = result.fetchall()
        
        if not duplicates:
            return {
                "message": "No duplicate outages found",
                "duplicates_removed": 0
            }
        
        # Delete duplicates, keeping only the most recent one
        delete_query = text("""
            DELETE FROM cloud_events 
            WHERE event_id IN (
                SELECT event_id FROM (
                    SELECT 
                        event_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY title, cloud_provider, service_name 
                            ORDER BY event_time DESC
                        ) as rn
                    FROM cloud_events 
                    WHERE event_type = 'OUTAGE_STATUS'
                ) ranked
                WHERE rn > 1
            )
        """)
        
        result = await db.execute(delete_query)
        await db.commit()
        
        # Get count of remaining outages
        count_query = text("""
            SELECT COUNT(*) as count
            FROM cloud_events 
            WHERE event_type = 'OUTAGE_STATUS'
        """)
        
        result = await db.execute(count_query)
        remaining_count = result.scalar()
        
        return {
            "message": "Duplicate outages cleaned up successfully",
            "duplicates_found": len(duplicates),
            "duplicates_removed": sum(d.count - 1 for d in duplicates),
            "remaining_outages": remaining_count,
            "duplicate_details": [
                {
                    "title": d.title,
                    "provider": d.cloud_provider,
                    "service": d.service_name,
                    "count": d.count
                }
                for d in duplicates
            ]
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up duplicate outages: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error cleaning up duplicates: {str(e)}")


@router.get("/active")
async def get_active_outages(
    provider: Optional[CloudProvider] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get currently active (non-resolved) outages from cloud provider APIs
    """
    try:
        outage_service = OutageMonitoringService(db)
        
        # Convert provider enum to CloudProvider if specified
        cloud_provider = None
        if provider:
            cloud_provider = CloudProvider(provider.value)
            # Get active outages for specific provider
            if cloud_provider in outage_service.monitors:
                monitor = outage_service.monitors[cloud_provider]
                outages = await monitor.get_active_outages()
            else:
                raise HTTPException(status_code=400, detail=f"Provider {provider.value} not supported")
        else:
            # Get active outages from all providers
            outages = await outage_service.get_all_active_outages()
        
        # Convert to response format
        outage_list = []
        for outage in outages:
            outage_list.append({
                "event_id": f"active-{outage.provider.value}-{outage.external_id}" if outage.external_id else f"active-{outage.provider.value}-{outage.start_time.strftime('%Y%m%d%H%M%S')}",
                "provider": outage.provider.value,
                "service": outage.service,
                "region": outage.region,
                "severity": outage.severity.value,
                "status": outage.status.value,
                "title": outage.title,
                "description": outage.description,
                "event_time": outage.start_time.isoformat(),
                "resolved_at": outage.end_time.isoformat() if outage.end_time else None,
                "outage_status": outage.status.value,
                "affected_services": outage.affected_services,
                "affected_regions": outage.affected_regions,
                "raw_data": outage.raw_data
            })
        
        # Calculate statistics
        statistics = {}
        provider_outages = {}
        for outage in outages:
            provider = outage.provider.value
            if provider not in provider_outages:
                provider_outages[provider] = []
            provider_outages[provider].append(outage)
        
        for provider, provider_outage_list in provider_outages.items():
            if provider_outage_list:
                statistics[provider] = {
                    "count": len(provider_outage_list),
                    "severity_breakdown": {
                        "critical": len([o for o in provider_outage_list if o.severity.value == "critical"]),
                        "high": len([o for o in provider_outage_list if o.severity.value == "high"]),
                        "medium": len([o for o in provider_outage_list if o.severity.value == "medium"]),
                        "low": len([o for o in provider_outage_list if o.severity.value == "low"]),
                        "info": len([o for o in provider_outage_list if o.severity.value == "info"])
                    }
                }
        
        return {
            "outages": outage_list,
            "total_count": len(outage_list),
            "statistics": statistics,
            "source": "providers",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active outages: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting active outages: {str(e)}")
