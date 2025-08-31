"""
Grafana Webhook Handler

This module handles processing Grafana alert webhooks.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import CloudEvent
from app.models.events import EventType, EventSeverity, EventStatus
from app.services.event_processor import EventProcessor

logger = logging.getLogger(__name__)


class GrafanaWebhookHandler:
    """Handler for Grafana webhook events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_processor = EventProcessor(db)
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> List[CloudEvent]:
        """Process Grafana webhook data"""
        try:
            logger.info(f"Processing Grafana webhook with {len(webhook_data.get('alerts', []))} alerts")
            
            # Process each alert in the webhook
            events = []
            for alert in webhook_data.get("alerts", []):
                try:
                    event = await self._process_alert(alert, webhook_data)
                    if event:
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error processing individual alert: {e}")
                    continue
            
            return events
            
        except Exception as e:
            logger.error(f"Error processing Grafana webhook: {e}")
            raise
    
    async def _process_alert(self, alert: Dict[str, Any], webhook_data: Dict[str, Any]) -> CloudEvent:
        """Process individual Grafana alert"""
        try:
            # Extract alert information
            alert_id = alert.get("fingerprint", alert.get("id"))
            status = alert.get("status", "firing")
            severity = self._map_severity(alert.get("labels", {}).get("severity", "info"))
            
            # Create event data
            event_data = {
                "external_id": alert_id,
                "event_type": EventType.GRAFANA_ALERT,
                "severity": severity,
                "status": EventStatus.ACTIVE if status == "firing" else EventStatus.RESOLVED,
                "cloud_provider": "grafana",
                "title": alert.get("annotations", {}).get("summary", "Grafana Alert"),
                "description": alert.get("annotations", {}).get("description", ""),
                "summary": alert.get("annotations", {}).get("summary", "Grafana Alert"),
                "service_name": alert.get("labels", {}).get("service", "grafana"),
                "event_time": self._parse_time(alert.get("startsAt", datetime.utcnow().isoformat())),
                "raw_data": {
                    "alert": alert,
                    "webhook_data": webhook_data
                }
            }
            
            # Create cloud event
            event = CloudEvent(
                event_id=f"grafana-{alert_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                external_id=alert_id,
                event_type=event_data["event_type"],
                severity=event_data["severity"],
                status=event_data["status"],
                cloud_provider=event_data["cloud_provider"],
                title=event_data["title"],
                description=event_data["description"],
                summary=event_data["summary"],
                service_name=event_data["service_name"],
                event_time=event_data["event_time"],
                raw_data=event_data["raw_data"],
                tenant_id="default"
            )
            
            # Save to database
            self.db.add(event)
            await self.db.commit()
            await self.db.refresh(event)
            
            # Process for subscriptions and alerting
            await self.event_processor._process_subscriptions(event)
            await self.event_processor._process_for_alerting(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error processing Grafana alert: {e}")
            raise
    
    def _map_severity(self, severity: str) -> EventSeverity:
        """Map Grafana severity to EventSeverity"""
        mapping = {
            "critical": EventSeverity.CRITICAL,
            "high": EventSeverity.HIGH,
            "medium": EventSeverity.MEDIUM,
            "low": EventSeverity.LOW,
            "info": EventSeverity.INFO,
            "warning": EventSeverity.MEDIUM,
            "error": EventSeverity.HIGH
        }
        return mapping.get(severity.lower(), EventSeverity.INFO)
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime"""
        try:
            # Handle different time formats
            if time_str.endswith("Z"):
                time_str = time_str.replace("Z", "+00:00")
            return datetime.fromisoformat(time_str)
        except Exception:
            return datetime.utcnow()
    
    def extract_alert_metadata(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Grafana alert"""
        try:
            labels = alert.get("labels", {})
            annotations = alert.get("annotations", {})
            
            return {
                "alert_name": labels.get("alertname"),
                "instance": labels.get("instance"),
                "job": labels.get("job"),
                "service": labels.get("service"),
                "environment": labels.get("environment"),
                "severity": labels.get("severity"),
                "summary": annotations.get("summary"),
                "description": annotations.get("description"),
                "dashboard_url": annotations.get("dashboardURL"),
                "panel_url": annotations.get("panelURL"),
                "value": annotations.get("value"),
                "metric": labels.get("__name__"),
                "namespace": labels.get("namespace"),
                "pod": labels.get("pod"),
                "container": labels.get("container"),
                "node": labels.get("node"),
                "cluster": labels.get("cluster")
            }
        except Exception as e:
            logger.error(f"Error extracting alert metadata: {e}")
            return {}
