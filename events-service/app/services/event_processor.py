"""
Event Processor Service

This module handles processing events from various sources and applying subscription logic.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.schemas import CloudEvent, EventSubscription, CloudProject
from app.models.events import CloudEventCreate, EventType, EventSeverity

logger = logging.getLogger(__name__)


class EventProcessor:
    """Service for processing cloud events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def process_webhook_event(self, webhook_data: Dict[str, Any], source: str) -> List[CloudEvent]:
        """Process event from webhook and create cloud events"""
        try:
            # Create cloud event
            event = await self._create_cloud_event(webhook_data, source)
            
            # Check subscriptions and create events
            events = await self._process_subscriptions(event)
            
            # Process for alerting
            await self._process_for_alerting(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            raise
    
    async def _create_cloud_event(self, webhook_data: Dict[str, Any], source: str) -> CloudEvent:
        """Create a cloud event from webhook data"""
        try:
            # Extract event data based on source
            if source == "grafana":
                event_data = self._parse_grafana_webhook(webhook_data)
            elif source == "gcp":
                event_data = self._parse_gcp_webhook(webhook_data)
            elif source == "aws":
                event_data = self._parse_aws_webhook(webhook_data)
            elif source == "azure":
                event_data = self._parse_azure_webhook(webhook_data)
            elif source == "oci":
                event_data = self._parse_oci_webhook(webhook_data)
            else:
                event_data = self._parse_generic_webhook(webhook_data)
            
            # Create event
            event = CloudEvent(
                event_id=f"event-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{source}",
                external_id=event_data.get("external_id"),
                event_type=event_data["event_type"],
                severity=event_data["severity"],
                status=event_data["status"],
                cloud_provider=event_data["cloud_provider"],
                project_id=event_data.get("project_id"),
                subscription_id=event_data.get("subscription_id"),
                title=event_data["title"],
                description=event_data["description"],
                summary=event_data["summary"],
                service_name=event_data.get("service_name"),
                resource_type=event_data.get("resource_type"),
                resource_id=event_data.get("resource_id"),
                region=event_data.get("region"),
                event_time=event_data.get("event_time", datetime.utcnow()),
                raw_data=webhook_data,
                tenant_id="default"
            )
            
            self.db.add(event)
            await self.db.commit()
            await self.db.refresh(event)
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating cloud event: {e}")
            raise
    
    async def _process_subscriptions(self, event: CloudEvent) -> List[CloudEvent]:
        """Process event against subscriptions"""
        try:
            # Get relevant subscriptions
            subscriptions = await self._get_matching_subscriptions(event)
            
            events = []
            for subscription in subscriptions:
                if await self._check_event_matches_subscription(event, subscription):
                    # Create event for this subscription
                    subscription_event = CloudEvent(
                        event_id=f"sub-{event.event_id}-{subscription.subscription_id}",
                        external_id=event.external_id,
                        event_type=event.event_type,
                        severity=event.severity,
                        status=event.status,
                        cloud_provider=event.cloud_provider,
                        project_id=event.project_id,
                        subscription_id=subscription.subscription_id,
                        title=event.title,
                        description=event.description,
                        summary=event.summary,
                        service_name=event.service_name,
                        resource_type=event.resource_type,
                        resource_id=event.resource_id,
                        region=event.region,
                        event_time=event.event_time,
                        raw_data=event.raw_data,
                        tenant_id=event.tenant_id
                    )
                    
                    self.db.add(subscription_event)
                    events.append(subscription_event)
            
            await self.db.commit()
            return events
            
        except Exception as e:
            logger.error(f"Error processing subscriptions: {e}")
            raise
    
    async def _get_matching_subscriptions(self, event: CloudEvent) -> List[EventSubscription]:
        """Get subscriptions that might match this event"""
        try:
            query = select(EventSubscription).where(
                and_(
                    EventSubscription.enabled == True,
                    EventSubscription.tenant_id == "default"
                )
            )
            
            # Filter by project if available
            if event.project_id:
                query = query.where(EventSubscription.project_id == event.project_id)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting matching subscriptions: {e}")
            raise
    
    async def _check_event_matches_subscription(self, event: CloudEvent, subscription: EventSubscription) -> bool:
        """Check if event matches subscription criteria"""
        try:
            # Check event types
            if subscription.event_types and event.event_type not in subscription.event_types:
                return False
            
            # Check services
            if subscription.services and event.service_name and event.service_name not in subscription.services:
                return False
            
            # Check regions
            if subscription.regions and event.region and event.region not in subscription.regions:
                return False
            
            # Check severity levels
            if subscription.severity_levels and event.severity not in subscription.severity_levels:
                return False
            
            # Check custom filters
            if subscription.custom_filters:
                if not self._check_custom_filters(event, subscription.custom_filters):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking event match: {e}")
            return False
    
    def _check_custom_filters(self, event: CloudEvent, filters: Dict[str, Any]) -> bool:
        """Check custom filters against event"""
        try:
            for field, value in filters.items():
                event_value = self._get_nested_value(event.raw_data, field)
                if event_value != value:
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking custom filters: {e}")
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from dictionary using dot notation"""
        try:
            keys = field_path.split('.')
            value = data
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return None
    
    async def _process_for_alerting(self, event: CloudEvent):
        """Process event for alerting"""
        try:
            logger.info(f"Processing event {event.event_id} for alerting")
            import httpx
            
            # Convert event to alerting service format
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "user_id": event.user_id or "system",
                "ip_address": event.ip_address or "0.0.0.0",
                "status": event.status,
                "timestamp": event.event_time.isoformat(),
                "service_name": event.service_name,
                "tenant_id": event.tenant_id,
                "severity": event.severity,
                "title": event.title,
                "description": event.description,
                "summary": event.summary,
                "raw_data": event.raw_data
            }
            
            logger.info(f"Sending event {event.event_id} to alerting service")
            
            # Send to alerting service
            alerting_url = "http://alerting:8001/api/v1/alerts/process-event"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    alerting_url,
                    headers={"Authorization": "Bearer test-token"},
                    json=event_data,
                    params={"tenant_id": event.tenant_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Event {event.event_id} sent to alerting service: {result.get('message', 'processed')}")
                else:
                    logger.warning(f"Failed to send event {event.event_id} to alerting service: {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error processing for alerting: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def check_event_matches_subscription(self, event_data: Dict[str, Any], subscription: EventSubscription) -> bool:
        """Check if a test event would match a subscription"""
        try:
            # Create a temporary event for testing
            temp_event = CloudEvent(
                event_id="test-event",
                event_type=event_data.get("event_type"),
                severity=event_data.get("severity"),
                status=event_data.get("status"),
                cloud_provider=event_data.get("cloud_provider"),
                service_name=event_data.get("service_name"),
                region=event_data.get("region"),
                raw_data=event_data,
                title="Test Event",
                description="Test event for subscription validation",
                summary="Test event",
                tenant_id="default"
            )
            
            return await self._check_event_matches_subscription(temp_event, subscription)
            
        except Exception as e:
            logger.error(f"Error checking test event match: {e}")
            return False
    
    def _parse_grafana_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Grafana webhook data"""
        try:
            # Extract alert information
            alert = data.get("alerts", [{}])[0] if data.get("alerts") else {}
            
            return {
                "external_id": alert.get("fingerprint"),
                "event_type": EventType.GRAFANA_ALERT,
                "severity": self._map_grafana_severity(alert.get("labels", {}).get("severity", "info")),
                "status": "active" if alert.get("status") == "firing" else "resolved",
                "cloud_provider": "grafana",
                "title": alert.get("annotations", {}).get("summary", "Grafana Alert"),
                "description": alert.get("annotations", {}).get("description", ""),
                "summary": alert.get("annotations", {}).get("summary", "Grafana Alert"),
                "service_name": alert.get("labels", {}).get("service", "grafana"),
                "event_time": datetime.fromisoformat(alert.get("startsAt", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error parsing Grafana webhook: {e}")
            return self._parse_generic_webhook(data)
    
    def _parse_gcp_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GCP webhook data"""
        try:
            return {
                "external_id": data.get("incident", {}).get("incident_id"),
                "event_type": EventType.CLOUD_ALERT,
                "severity": self._map_gcp_severity(data.get("incident", {}).get("severity", "info")),
                "status": "active" if data.get("incident", {}).get("state") == "open" else "resolved",
                "cloud_provider": "gcp",
                "title": data.get("incident", {}).get("summary", "GCP Alert"),
                "description": data.get("incident", {}).get("documentation", {}).get("content", ""),
                "summary": data.get("incident", {}).get("summary", "GCP Alert"),
                "service_name": data.get("incident", {}).get("resource_type_display_name", "gcp"),
                "event_time": datetime.fromisoformat(data.get("incident", {}).get("started_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error parsing GCP webhook: {e}")
            return self._parse_generic_webhook(data)
    
    def _parse_aws_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AWS webhook data"""
        try:
            return {
                "external_id": data.get("detail", {}).get("id"),
                "event_type": EventType.CLOUD_ALERT,
                "severity": self._map_aws_severity(data.get("detail", {}).get("severity", "info")),
                "status": "active",
                "cloud_provider": "aws",
                "title": data.get("detail", {}).get("title", "AWS Alert"),
                "description": data.get("detail", {}).get("description", ""),
                "summary": data.get("detail", {}).get("title", "AWS Alert"),
                "service_name": data.get("detail", {}).get("service", "aws"),
                "event_time": datetime.fromisoformat(data.get("time", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error parsing AWS webhook: {e}")
            return self._parse_generic_webhook(data)
    
    def _parse_azure_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Azure webhook data"""
        try:
            return {
                "external_id": data.get("data", {}).get("essentials", {}).get("alertId"),
                "event_type": EventType.CLOUD_ALERT,
                "severity": self._map_azure_severity(data.get("data", {}).get("essentials", {}).get("severity", "info")),
                "status": "active" if data.get("data", {}).get("essentials", {}).get("monitorCondition") == "Fired" else "resolved",
                "cloud_provider": "azure",
                "title": data.get("data", {}).get("essentials", {}).get("alertRule", "Azure Alert"),
                "description": data.get("data", {}).get("essentials", {}).get("description", ""),
                "summary": data.get("data", {}).get("essentials", {}).get("alertRule", "Azure Alert"),
                "service_name": data.get("data", {}).get("essentials", {}).get("monitoringService", "azure"),
                "event_time": datetime.fromisoformat(data.get("data", {}).get("essentials", {}).get("firedDateTime", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error parsing Azure webhook: {e}")
            return self._parse_generic_webhook(data)
    
    def _parse_oci_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse OCI webhook data"""
        try:
            return {
                "external_id": data.get("id"),
                "event_type": EventType.CLOUD_ALERT,
                "severity": self._map_oci_severity(data.get("severity", "info")),
                "status": "active",
                "cloud_provider": "oci",
                "title": data.get("title", "OCI Alert"),
                "description": data.get("body", ""),
                "summary": data.get("title", "OCI Alert"),
                "service_name": data.get("service", "oci"),
                "event_time": datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                "raw_data": data
            }
        except Exception as e:
            logger.error(f"Error parsing OCI webhook: {e}")
            return self._parse_generic_webhook(data)
    
    def _parse_generic_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generic webhook data"""
        return {
            "external_id": data.get("id") or data.get("event_id"),
            "event_type": EventType.CUSTOM_EVENT,
            "severity": EventSeverity.INFO,
            "status": "active",
            "cloud_provider": "unknown",
            "title": data.get("title") or data.get("summary") or "Generic Event",
            "description": data.get("description") or data.get("message") or "",
            "summary": data.get("summary") or data.get("title") or "Generic Event",
            "service_name": data.get("service") or "unknown",
            "event_time": datetime.utcnow(),
            "raw_data": data
        }
    
    def _map_grafana_severity(self, severity: str) -> EventSeverity:
        """Map Grafana severity to EventSeverity"""
        mapping = {
            "critical": EventSeverity.CRITICAL,
            "high": EventSeverity.HIGH,
            "medium": EventSeverity.MEDIUM,
            "low": EventSeverity.LOW,
            "info": EventSeverity.INFO
        }
        return mapping.get(severity.lower(), EventSeverity.INFO)
    
    def _map_gcp_severity(self, severity: str) -> EventSeverity:
        """Map GCP severity to EventSeverity"""
        mapping = {
            "critical": EventSeverity.CRITICAL,
            "high": EventSeverity.HIGH,
            "medium": EventSeverity.MEDIUM,
            "low": EventSeverity.LOW,
            "info": EventSeverity.INFO
        }
        return mapping.get(severity.lower(), EventSeverity.INFO)
    
    def _map_aws_severity(self, severity: str) -> EventSeverity:
        """Map AWS severity to EventSeverity"""
        mapping = {
            "critical": EventSeverity.CRITICAL,
            "high": EventSeverity.HIGH,
            "medium": EventSeverity.MEDIUM,
            "low": EventSeverity.LOW,
            "info": EventSeverity.INFO
        }
        return mapping.get(severity.lower(), EventSeverity.INFO)
    
    def _map_azure_severity(self, severity: str) -> EventSeverity:
        """Map Azure severity to EventSeverity"""
        mapping = {
            "critical": EventSeverity.CRITICAL,
            "high": EventSeverity.HIGH,
            "medium": EventSeverity.MEDIUM,
            "low": EventSeverity.LOW,
            "info": EventSeverity.INFO
        }
        return mapping.get(severity.lower(), EventSeverity.INFO)
    
    def _map_oci_severity(self, severity: str) -> EventSeverity:
        """Map OCI severity to EventSeverity"""
        mapping = {
            "critical": EventSeverity.CRITICAL,
            "high": EventSeverity.HIGH,
            "medium": EventSeverity.MEDIUM,
            "low": EventSeverity.LOW,
            "info": EventSeverity.INFO
        }
        return mapping.get(severity.lower(), EventSeverity.INFO)
