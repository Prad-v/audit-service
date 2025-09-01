"""
Background Tasks Service

This module manages background tasks for the events service, including outage monitoring.
"""

import asyncio
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.outage_monitor import OutageMonitoringService

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """Manages background tasks for the events service"""
    
    def __init__(self):
        self.outage_monitoring_task: Optional[asyncio.Task] = None
        self.outage_service: Optional[OutageMonitoringService] = None
        self.running = False
    
    async def start_outage_monitoring(self, session: AsyncSession):
        """Start the outage monitoring background task"""
        if self.outage_monitoring_task and not self.outage_monitoring_task.done():
            logger.info("Outage monitoring is already running")
            return
        
        try:
            self.outage_service = OutageMonitoringService(session)
            self.outage_monitoring_task = asyncio.create_task(
                self.outage_service.start_monitoring()
            )
            self.running = True
            logger.info("Outage monitoring background task started")
        except Exception as e:
            logger.error(f"Error starting outage monitoring: {e}")
            raise
    
    async def pause_outage_monitoring(self):
        """Pause the outage monitoring background task"""
        if not self.outage_service:
            logger.info("Outage monitoring is not initialized")
            return
        
        try:
            await self.outage_service.pause_monitoring()
            self.running = False
            logger.info("Outage monitoring background task paused")
        except Exception as e:
            logger.error(f"Error pausing outage monitoring: {e}")
            raise
    
    async def resume_outage_monitoring(self):
        """Resume the outage monitoring background task"""
        if not self.outage_service:
            logger.info("Outage monitoring is not initialized")
            return
        
        try:
            await self.outage_service.resume_monitoring()
            self.running = True
            logger.info("Outage monitoring background task resumed")
        except Exception as e:
            logger.error(f"Error resuming outage monitoring: {e}")
            raise
    
    async def stop_outage_monitoring(self):
        """Stop the outage monitoring background task"""
        if not self.outage_monitoring_task or self.outage_monitoring_task.done():
            logger.info("Outage monitoring is not running")
            return
        
        try:
            if self.outage_service:
                await self.outage_service.stop_monitoring()
            
            self.outage_monitoring_task.cancel()
            try:
                await self.outage_monitoring_task
            except asyncio.CancelledError:
                pass
            
            self.running = False
            logger.info("Outage monitoring background task stopped")
        except Exception as e:
            logger.error(f"Error stopping outage monitoring: {e}")
            raise
    
    async def get_outage_monitoring_status(self) -> dict:
        """Get the status of outage monitoring"""
        if not self.outage_service:
            return {
                "status": "not_initialized",
                "running": False,
                "task_status": "not_started",
                "check_interval_seconds": None,
                "last_check_time": None,
                "monitored_providers": []
            }
        
        task_status = "running"
        if self.outage_monitoring_task:
            if self.outage_monitoring_task.done():
                task_status = "completed"
                if self.outage_monitoring_task.cancelled():
                    task_status = "cancelled"
                elif self.outage_monitoring_task.exception():
                    task_status = "failed"
        
        # Get detailed status from the outage service
        status_data = self.outage_service.get_monitoring_status()
        
        return {
            "service_status": "running" if self.running else "paused",
            "running": self.running,
            "task_status": task_status,
            "check_interval_seconds": self.outage_service.check_interval if self.outage_service else None,
            "last_check_time": status_data.get("last_check_time"),
            "monitored_providers": status_data.get("monitored_providers", [])
        }
    
    async def manual_check_outages(self, session: AsyncSession, provider=None):
        """Manually check for outages"""
        if not self.outage_service:
            self.outage_service = OutageMonitoringService(session)
        
        if provider:
            return await self.outage_service.manual_check(provider)
        else:
            # Check all providers
            all_outages = []
            for provider in self.outage_service.monitors.keys():
                outages = await self.outage_service.manual_check(provider)
                all_outages.extend(outages)
            return all_outages


# Global background task manager instance
background_task_manager = BackgroundTaskManager()
