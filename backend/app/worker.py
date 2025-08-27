"""
Background worker for the audit log framework.

This module provides NATS-based background processing for audit log events,
including batch processing, real-time event handling, and data pipeline operations.
"""

import asyncio
import json
import signal
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from uuid import uuid4

import structlog
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout, ErrNoServers

from app.config import get_settings
from app.db.database import get_database_manager
from app.db.schemas import AuditLog
from app.models.audit import EventType, Severity
from app.services.cache_service import get_cache_service
from app.services.nats_service import get_nats_service
from app.utils.metrics import audit_metrics, track_execution_time
from app.utils.logging import setup_logging

logger = structlog.get_logger(__name__)
settings = get_settings()


class AuditWorker:
    """Background worker for processing audit log events."""
    
    def __init__(self):
        self.nats_service = get_nats_service()
        self.db_manager = get_database_manager()
        self.cache_service = get_cache_service()
        self.running = False
        self.batch_buffer: List[Dict[str, Any]] = []
        self.batch_size = settings.worker.batch_size
        self.batch_timeout = settings.worker.batch_timeout_seconds
        self.last_batch_time = datetime.now(timezone.utc)
    
    async def start(self):
        """Start the background worker."""
        logger.info("Starting audit log worker")
        
        try:
            # Initialize services
            await self.db_manager.initialize()
            await self.cache_service.initialize()
            await self.nats_service.initialize()
            
            # Set up signal handlers
            self._setup_signal_handlers()
            
            # Start processing
            self.running = True
            await self._start_processing()
            
        except Exception as e:
            logger.error("Failed to start worker", error=str(e))
            raise
    
    async def stop(self):
        """Stop the background worker."""
        logger.info("Stopping audit log worker")
        
        self.running = False
        
        # Process remaining batch items
        if self.batch_buffer:
            await self._process_batch()
        
        # Close services
        await self.nats_service.close()
        await self.cache_service.close()
        await self.db_manager.close()
        
        logger.info("Audit log worker stopped")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _start_processing(self):
        """Start processing NATS messages."""
        try:
            # Subscribe to audit event streams
            await self._subscribe_to_events()
            
            # Start batch processing timer
            asyncio.create_task(self._batch_timer())
            
            # Keep worker running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error("Error in worker processing", error=str(e))
            raise
    
    async def _subscribe_to_events(self):
        """Subscribe to NATS subjects for audit events."""
        try:
            # Subscribe to individual audit events
            await self.nats_service.subscribe(
                subject="audit.events.*",
                callback=self._handle_audit_event,
                queue="audit-workers",
            )
            
            # Subscribe to batch audit events
            await self.nats_service.subscribe(
                subject="audit.batch.*",
                callback=self._handle_audit_batch,
                queue="audit-batch-workers",
            )
            
            # Subscribe to system events
            await self.nats_service.subscribe(
                subject="audit.system.*",
                callback=self._handle_system_event,
                queue="audit-system-workers",
            )
            
            logger.info("Subscribed to NATS audit event streams")
            
        except Exception as e:
            logger.error("Failed to subscribe to NATS streams", error=str(e))
            raise
    
    @track_execution_time("nats_message_processing")
    async def _handle_audit_event(self, msg):
        """Handle individual audit event messages."""
        try:
            # Parse message data
            data = json.loads(msg.data.decode())
            
            logger.debug(
                "Processing audit event",
                event_id=data.get("id"),
                event_type=data.get("event_type"),
                tenant_id=data.get("tenant_id"),
            )
            
            # Add to batch buffer for efficient processing
            self.batch_buffer.append({
                "type": "event",
                "data": data,
                "received_at": datetime.now(timezone.utc),
            })
            
            # Process batch if buffer is full
            if len(self.batch_buffer) >= self.batch_size:
                await self._process_batch()
            
            # Acknowledge message
            await msg.ack()
            
            audit_metrics.nats_messages_published.labels(
                subject=msg.subject
            ).inc()
            
        except Exception as e:
            logger.error("Failed to handle audit event", error=str(e))
            audit_metrics.nats_publish_errors.labels(
                error_type="processing_error"
            ).inc()
            
            # Negative acknowledge to retry
            await msg.nak()
    
    @track_execution_time("nats_batch_processing")
    async def _handle_audit_batch(self, msg):
        """Handle batch audit event messages."""
        try:
            # Parse batch data
            batch_data = json.loads(msg.data.decode())
            
            logger.info(
                "Processing audit batch",
                batch_id=batch_data.get("batch_id"),
                count=batch_data.get("count"),
                tenant_id=batch_data.get("tenant_id"),
            )
            
            # Process batch events
            events = batch_data.get("events", [])
            for event in events:
                self.batch_buffer.append({
                    "type": "batch_event",
                    "data": event,
                    "batch_id": batch_data.get("batch_id"),
                    "received_at": datetime.now(timezone.utc),
                })
            
            # Process if buffer is getting full
            if len(self.batch_buffer) >= self.batch_size:
                await self._process_batch()
            
            # Acknowledge message
            await msg.ack()
            
            audit_metrics.batch_operations.labels(
                tenant_id=batch_data.get("tenant_id", "unknown")
            ).inc()
            
        except Exception as e:
            logger.error("Failed to handle audit batch", error=str(e))
            audit_metrics.nats_publish_errors.labels(
                error_type="batch_processing_error"
            ).inc()
            
            # Negative acknowledge to retry
            await msg.nak()
    
    async def _handle_system_event(self, msg):
        """Handle system-level events."""
        try:
            data = json.loads(msg.data.decode())
            event_type = data.get("type")
            
            logger.info("Processing system event", event_type=event_type)
            
            if event_type == "cache_invalidate":
                await self._handle_cache_invalidation(data)
            elif event_type == "metrics_collect":
                await self._handle_metrics_collection(data)
            elif event_type == "health_check":
                await self._handle_health_check(data)
            
            await msg.ack()
            
        except Exception as e:
            logger.error("Failed to handle system event", error=str(e))
            await msg.nak()
    
    async def _process_batch(self):
        """Process the current batch of events."""
        if not self.batch_buffer:
            return
        
        try:
            batch_size = len(self.batch_buffer)
            logger.info("Processing event batch", size=batch_size)
            
            # Group events by tenant for efficient processing
            tenant_groups = {}
            for item in self.batch_buffer:
                tenant_id = item["data"].get("tenant_id", "unknown")
                if tenant_id not in tenant_groups:
                    tenant_groups[tenant_id] = []
                tenant_groups[tenant_id].append(item)
            
            # Process each tenant group
            for tenant_id, events in tenant_groups.items():
                await self._process_tenant_events(tenant_id, events)
            
            # Update metrics
            audit_metrics.batch_size.observe(batch_size)
            
            # Clear buffer
            self.batch_buffer.clear()
            self.last_batch_time = datetime.now(timezone.utc)
            
            logger.info("Batch processing completed", size=batch_size)
            
        except Exception as e:
            logger.error("Failed to process batch", error=str(e))
            # Don't clear buffer on error - will retry
    
    async def _process_tenant_events(self, tenant_id: str, events: List[Dict[str, Any]]):
        """Process events for a specific tenant."""
        try:
            # Aggregate events for analytics
            await self._update_tenant_analytics(tenant_id, events)
            
            # Update cache with recent events
            await self._update_event_cache(tenant_id, events)
            
            # Trigger alerts if needed
            await self._check_alert_conditions(tenant_id, events)
            
            logger.debug(
                "Processed tenant events",
                tenant_id=tenant_id,
                count=len(events),
            )
            
        except Exception as e:
            logger.error(
                "Failed to process tenant events",
                tenant_id=tenant_id,
                error=str(e),
            )
    
    async def _update_tenant_analytics(self, tenant_id: str, events: List[Dict[str, Any]]):
        """Update analytics data for tenant events."""
        try:
            # Count events by type
            event_counts = {}
            severity_counts = {}
            
            for event in events:
                data = event["data"]
                event_type = data.get("event_type", "unknown")
                severity = data.get("severity", "info")
                
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Store analytics in cache
            analytics_key = f"analytics:{tenant_id}:hourly:{datetime.now().strftime('%Y%m%d%H')}"
            analytics_data = {
                "event_counts": event_counts,
                "severity_counts": severity_counts,
                "total_events": len(events),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            await self.cache_service.set(analytics_key, analytics_data, ttl=3600)
            
        except Exception as e:
            logger.warning("Failed to update tenant analytics", error=str(e))
    
    async def _update_event_cache(self, tenant_id: str, events: List[Dict[str, Any]]):
        """Update cache with recent events for fast retrieval."""
        try:
            # Store recent events in cache
            recent_events_key = f"recent_events:{tenant_id}"
            
            # Get existing recent events
            existing_events = await self.cache_service.get(recent_events_key) or []
            
            # Add new events
            for event in events:
                existing_events.append({
                    "id": event["data"].get("id"),
                    "event_type": event["data"].get("event_type"),
                    "timestamp": event["data"].get("timestamp"),
                    "resource_type": event["data"].get("resource_type"),
                    "action": event["data"].get("action"),
                })
            
            # Keep only last 1000 events
            if len(existing_events) > 1000:
                existing_events = existing_events[-1000:]
            
            # Update cache
            await self.cache_service.set(recent_events_key, existing_events, ttl=1800)
            
        except Exception as e:
            logger.warning("Failed to update event cache", error=str(e))
    
    async def _check_alert_conditions(self, tenant_id: str, events: List[Dict[str, Any]]):
        """Check if any events trigger alert conditions."""
        try:
            # Check for high-severity events
            critical_events = [
                e for e in events 
                if e["data"].get("severity") in ["critical", "error"]
            ]
            
            if critical_events:
                await self._trigger_alert(tenant_id, "high_severity_events", {
                    "count": len(critical_events),
                    "events": critical_events[:5],  # Include first 5 events
                })
            
            # Check for unusual activity patterns
            event_types = [e["data"].get("event_type") for e in events]
            if len(set(event_types)) == 1 and len(events) > 100:
                # Many events of the same type might indicate an issue
                await self._trigger_alert(tenant_id, "unusual_activity", {
                    "event_type": event_types[0],
                    "count": len(events),
                })
            
        except Exception as e:
            logger.warning("Failed to check alert conditions", error=str(e))
    
    async def _trigger_alert(self, tenant_id: str, alert_type: str, data: Dict[str, Any]):
        """Trigger an alert for the tenant."""
        try:
            alert_data = {
                "tenant_id": tenant_id,
                "alert_type": alert_type,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "alert_id": str(uuid4()),
            }
            
            # Publish alert to NATS
            await self.nats_service.publish(
                subject=f"alerts.{tenant_id}",
                data=alert_data,
            )
            
            logger.warning(
                "Alert triggered",
                tenant_id=tenant_id,
                alert_type=alert_type,
                alert_id=alert_data["alert_id"],
            )
            
        except Exception as e:
            logger.error("Failed to trigger alert", error=str(e))
    
    async def _batch_timer(self):
        """Timer to process batches periodically."""
        while self.running:
            try:
                await asyncio.sleep(self.batch_timeout)
                
                # Check if batch timeout has been reached
                time_since_last_batch = (
                    datetime.now(timezone.utc) - self.last_batch_time
                ).total_seconds()
                
                if time_since_last_batch >= self.batch_timeout and self.batch_buffer:
                    logger.debug("Processing batch due to timeout")
                    await self._process_batch()
                
            except Exception as e:
                logger.error("Error in batch timer", error=str(e))
    
    async def _handle_cache_invalidation(self, data: Dict[str, Any]):
        """Handle cache invalidation requests."""
        try:
            cache_keys = data.get("keys", [])
            patterns = data.get("patterns", [])
            
            # Invalidate specific keys
            for key in cache_keys:
                await self.cache_service.delete(key)
            
            # Invalidate by patterns
            for pattern in patterns:
                await self.cache_service.delete_pattern(pattern)
            
            logger.info("Cache invalidation completed", keys=len(cache_keys), patterns=len(patterns))
            
        except Exception as e:
            logger.error("Failed to handle cache invalidation", error=str(e))
    
    async def _handle_metrics_collection(self, data: Dict[str, Any]):
        """Handle metrics collection requests."""
        try:
            from app.utils.metrics import collect_periodic_metrics
            await collect_periodic_metrics()
            
            logger.debug("Metrics collection completed")
            
        except Exception as e:
            logger.error("Failed to collect metrics", error=str(e))
    
    async def _handle_health_check(self, data: Dict[str, Any]):
        """Handle health check requests."""
        try:
            # Perform basic health checks
            health_status = {
                "worker_status": "healthy" if self.running else "unhealthy",
                "batch_buffer_size": len(self.batch_buffer),
                "last_batch_time": self.last_batch_time.isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            # Publish health status
            await self.nats_service.publish(
                subject="health.worker.status",
                data=health_status,
            )
            
            logger.debug("Health check completed", status=health_status)
            
        except Exception as e:
            logger.error("Failed to handle health check", error=str(e))


async def main():
    """Main entry point for the worker."""
    # Setup logging
    setup_logging(settings.logging)
    
    logger.info("Starting audit log background worker")
    
    # Create and start worker
    worker = AuditWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error("Worker failed", error=str(e))
        sys.exit(1)
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())