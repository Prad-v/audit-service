"""
Multi-Cloud Outage Monitoring Service

This service monitors cloud provider status pages, RSS feeds, and APIs to detect outages
and stream them to the normalized event framework.
"""

import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.schemas import CloudEvent, EventSubscription, CloudProject
from app.models.events import CloudEventCreate, EventType, EventSeverity, EventStatus, CloudProvider

logger = logging.getLogger(__name__)


class OutageSource(str, Enum):
    """Sources for outage monitoring"""
    STATUS_PAGE = "status_page"
    RSS_FEED = "rss_feed"
    API_ENDPOINT = "api_endpoint"
    WEBHOOK = "webhook"


class OutageStatus(str, Enum):
    """Outage status levels"""
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    POSTPONED = "postponed"


@dataclass
class OutageEvent:
    """Represents a detected outage event"""
    provider: CloudProvider
    service: str
    region: Optional[str]
    status: OutageStatus
    title: str
    description: str
    severity: EventSeverity
    start_time: datetime
    end_time: Optional[datetime]
    affected_services: List[str]
    affected_regions: List[str]
    source: OutageSource
    external_id: Optional[str]
    raw_data: Dict[str, Any]


class CloudProviderMonitor:
    """Base class for cloud provider monitoring"""
    
    def __init__(self, provider: CloudProvider, session: AsyncSession):
        self.provider = provider
        self.session = session
        self.last_check = None
        self.known_outages: Set[str] = set()
    
    async def check_status(self) -> List[OutageEvent]:
        """Check provider status and return any new outages"""
        raise NotImplementedError
    
    async def parse_rss_feed(self, feed_url: str) -> List[OutageEvent]:
        """Parse RSS feed for outage information"""
        raise NotImplementedError
    
    async def check_api_status(self, api_url: str) -> List[OutageEvent]:
        """Check API endpoint for status information"""
        raise NotImplementedError


class GCPMonitor(CloudProviderMonitor):
    """Google Cloud Platform outage monitor"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CloudProvider.GCP, session)
        self.status_page_url = "https://status.cloud.google.com/en/feed.atom"
        self.api_url = "https://status.cloud.google.com/api/v1/status"
        self.incidents_json_url = "https://status.cloud.google.com/incidents.json"
    
    async def check_status(self) -> List[OutageEvent]:
        """Check GCP status page and RSS feed"""
        outages = []
        
        try:
            # Check RSS feed
            rss_outages = await self.parse_rss_feed(self.status_page_url)
            if rss_outages:
                outages.extend(rss_outages)
            
            # Check API status
            api_outages = await self.check_api_status(self.api_url)
            if api_outages:
                outages.extend(api_outages)
            
            # Check incidents JSON API (comprehensive data)
            json_outages = await self.check_incidents_json()
            if json_outages:
                outages.extend(json_outages)
        except Exception as e:
            logger.error(f"Error in GCP check_status: {e}")
        
        return outages
    
    async def parse_rss_feed(self, feed_url: str) -> List[OutageEvent]:
        """Parse GCP RSS feed for outages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        # Check if feed.entries exists and is iterable
                        if hasattr(feed, 'entries') and feed.entries is not None and isinstance(feed.entries, list):
                            for entry in feed.entries:
                                try:
                                    # Check if this is an outage-related entry
                                    if self._is_outage_entry(entry):
                                        outage = await self._parse_gcp_rss_entry(entry)
                                        if outage and outage.external_id not in self.known_outages:
                                            self.known_outages.add(outage.external_id)
                                            outages.append(outage)
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing GCP RSS entry: {entry_error}")
                                    continue
                        
                        return outages
                    else:
                        logger.warning(f"GCP RSS feed returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error parsing GCP RSS feed: {e}")
            return []
    
    async def check_api_status(self, api_url: str) -> List[OutageEvent]:
        """Check GCP API for status information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_gcp_api_response(data)
        except Exception as e:
            logger.error(f"Error checking GCP API: {e}")
            return []
    
    async def check_incidents_json(self) -> List[OutageEvent]:
        """Check GCP incidents JSON API for comprehensive incident data"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.incidents_json_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"GCP incidents JSON API returned {len(data)} incidents")
                        return await self._parse_gcp_incidents_json(data)
        except Exception as e:
            logger.error(f"Error checking GCP incidents JSON: {e}")
            return []
    
    async def get_historical_outages(self, days: int = 365) -> List[OutageEvent]:
        """Get historical outages from GCP incidents JSON API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Use GCP incidents JSON API for comprehensive historical data
                async with session.get(self.incidents_json_url) as response:
                    if response.status == 200:
                        incidents = await response.json()
                        
                        outages = []
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                        
                        logger.info(f"GCP incidents JSON API returned {len(incidents)} total incidents")
                        
                        for incident in incidents:
                            try:
                                # Check if incident is within the time window
                                begin_time = incident.get('begin')
                                if begin_time:
                                    incident_date = datetime.fromisoformat(begin_time.replace('Z', '+00:00'))
                                    if incident_date >= cutoff_date:
                                        # Parse the incident
                                        outage = await self._parse_gcp_incidents_json([incident])
                                        if outage:
                                            outages.extend(outage)
                                            logger.info(f"Added historical incident: {incident.get('external_desc', 'Unknown')}")
                                    else:
                                        logger.info(f"Incident {incident.get('id', 'unknown')} is too old: {incident_date}")
                                else:
                                    logger.warning(f"Incident {incident.get('id', 'unknown')} has no begin time")
                                    
                            except Exception as incident_error:
                                logger.warning(f"Error parsing GCP historical incident {incident.get('id', 'unknown')}: {incident_error}")
                                continue
                        
                        logger.info(f"GCP historical outages found: {len(outages)} (within {days} days)")
                        if len(outages) == 0:
                            logger.info("No GCP incidents found within the specified time window")
                        return outages
        except Exception as e:
            logger.error(f"Error fetching GCP historical outages: {e}")
            return []
    
    async def get_active_outages(self) -> List[OutageEvent]:
        """Get currently active (non-resolved) outages from GCP"""
        try:
            # Use GCP incidents JSON API for active incidents
            async with aiohttp.ClientSession() as session:
                async with session.get(self.incidents_json_url) as response:
                    if response.status == 200:
                        incidents = await response.json()
                        
                        active_outages = []
                        
                        for incident in incidents:
                            try:
                                # Check if incident is active (not resolved)
                                end_time = incident.get('end')
                                if not end_time:  # No end time means incident is active
                                    # Parse the incident
                                    outage = await self._parse_gcp_incidents_json([incident])
                                    if outage:
                                        active_outages.extend(outage)
                                        logger.info(f"Found active GCP incident: {incident.get('external_desc', 'Unknown')}")
                            except Exception as incident_error:
                                logger.warning(f"Error parsing GCP active incident {incident.get('id', 'unknown')}: {incident_error}")
                                continue
                        
                        logger.info(f"GCP active outages found: {len(active_outages)}")
                        return active_outages
        except Exception as e:
            logger.error(f"Error fetching GCP active outages: {e}")
            return []
    
    def _is_outage_entry(self, entry) -> bool:
        """Check if RSS entry represents an outage"""
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        
        outage_keywords = [
            'outage', 'issue', 'problem', 'degraded', 'investigating',
            'incident', 'disruption', 'unavailable', 'error'
        ]
        
        return any(keyword in title or keyword in description for keyword in outage_keywords)
    
    async def _parse_gcp_rss_entry(self, entry) -> Optional[OutageEvent]:
        """Parse GCP RSS entry into outage event"""
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            published = entry.get('published_parsed')
            
            # Extract severity from title/description
            severity = self._extract_severity(title, description)
            
            # Extract affected services and regions
            services, regions = self._extract_affected_areas(description)
            
            # Determine outage status
            status = self._determine_outage_status(title, description)
            
            return OutageEvent(
                provider=CloudProvider.GCP,
                service=services[0] if services else "unknown",
                region=regions[0] if regions else None,
                status=status,
                title=title,
                description=description,
                severity=severity,
                start_time=datetime.fromtimestamp(published, tz=timezone.utc) if published else datetime.now(timezone.utc),
                end_time=None,
                affected_services=services,
                affected_regions=regions,
                source=OutageSource.RSS_FEED,
                external_id=entry.get('id'),
                raw_data=dict(entry)
            )
        except Exception as e:
            logger.error(f"Error parsing GCP RSS entry: {e}")
            return None
    
    async def _parse_gcp_api_response(self, data: Dict[str, Any]) -> List[OutageEvent]:
        """Parse GCP API response for outages"""
        outages = []
        try:
            # Parse GCP API response structure
            # This would need to be adapted based on actual GCP API response format
            pass
        except Exception as e:
            logger.error(f"Error parsing GCP API response: {e}")
        return outages
    
    async def _parse_gcp_incidents_json(self, incidents: List[Dict[str, Any]]) -> List[OutageEvent]:
        """Parse GCP incidents JSON data"""
        outages = []
        try:
            for incident in incidents:
                try:
                    # Extract basic incident information
                    incident_id = incident.get('id', '')
                    external_desc = incident.get('external_desc', '')
                    begin_time = incident.get('begin')
                    end_time = incident.get('end')
                    severity = incident.get('severity', 'medium')
                    status_impact = incident.get('status_impact', 'SERVICE_INFORMATION')
                    service_name = incident.get('service_name', 'Multiple Products')
                    
                    # Convert severity to our enum
                    if severity == 'high':
                        event_severity = EventSeverity.HIGH
                    elif severity == 'medium':
                        event_severity = EventSeverity.MEDIUM
                    elif severity == 'low':
                        event_severity = EventSeverity.LOW
                    else:
                        event_severity = EventSeverity.INFO
                    
                    # Determine outage status
                    if status_impact == 'SERVICE_OUTAGE':
                        outage_status = OutageStatus.INVESTIGATING
                    elif status_impact == 'SERVICE_DISRUPTION':
                        outage_status = OutageStatus.INVESTIGATING
                    else:
                        outage_status = OutageStatus.MONITORING
                    
                    # Parse timestamps
                    start_time = None
                    if begin_time:
                        start_time = datetime.fromisoformat(begin_time.replace('Z', '+00:00'))
                    
                    end_time_parsed = None
                    if end_time:
                        end_time_parsed = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    
                    # Extract affected products and locations
                    affected_products = incident.get('affected_products', [])
                    affected_locations = incident.get('affected_locations', [])
                    
                    product_names = [p.get('title', '') for p in affected_products if p.get('title')]
                    location_names = [l.get('title', '') for l in affected_locations if l.get('title')]
                    
                    # Get the most recent update for description
                    most_recent_update = incident.get('most_recent_update', {})
                    description = most_recent_update.get('text', external_desc)
                    
                    # Create outage event
                    outage = OutageEvent(
                        provider=CloudProvider.GCP,
                        service=product_names[0] if product_names else service_name,
                        region=location_names[0] if location_names else None,
                        status=outage_status,
                        title=external_desc,
                        description=description,
                        severity=event_severity,
                        start_time=start_time or datetime.now(timezone.utc),
                        end_time=end_time_parsed,
                        affected_services=product_names,
                        affected_regions=location_names,
                        source=OutageSource.API_ENDPOINT,
                        external_id=incident_id,
                        raw_data=incident
                    )
                    
                    outages.append(outage)
                    
                except Exception as incident_error:
                    logger.warning(f"Error parsing GCP incident {incident.get('id', 'unknown')}: {incident_error}")
                    continue
            
            logger.info(f"Successfully parsed {len(outages)} incidents from GCP JSON API")
            return outages
            
        except Exception as e:
            logger.error(f"Error parsing GCP incidents JSON: {e}")
            return []
    
    def _extract_severity(self, title: str, description: str) -> EventSeverity:
        """Extract severity from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['critical', 'severe', 'major']):
            return EventSeverity.CRITICAL
        elif any(word in text for word in ['high', 'significant']):
            return EventSeverity.HIGH
        elif any(word in text for word in ['medium', 'moderate']):
            return EventSeverity.MEDIUM
        elif any(word in text for word in ['low', 'minor']):
            return EventSeverity.LOW
        else:
            return EventSeverity.INFO
    
    def _extract_affected_areas(self, description: str) -> tuple[List[str], List[str]]:
        """Extract affected services and regions from description"""
        services = []
        regions = []
        
        # Handle None or empty description
        if not description:
            return services, regions
        
        # Common GCP services
        gcp_services = [
            'compute engine', 'cloud storage', 'cloud sql', 'bigquery',
            'cloud functions', 'cloud run', 'kubernetes engine', 'load balancing',
            'cloud networking', 'cloud dns', 'cloud cdn', 'cloud monitoring'
        ]
        
        # Common GCP regions
        gcp_regions = [
            'us-central1', 'us-east1', 'us-west1', 'us-west2', 'us-west3', 'us-west4',
            'europe-west1', 'europe-west2', 'europe-west3', 'europe-west4',
            'asia-east1', 'asia-southeast1', 'australia-southeast1'
        ]
        
        text = description.lower()
        
        for service in gcp_services:
            if service in text:
                services.append(service)
        
        for region in gcp_regions:
            if region in text:
                regions.append(region)
        
        return services, regions
    
    def _determine_outage_status(self, title: str, description: str) -> OutageStatus:
        """Determine outage status from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['resolved', 'fixed', 'restored']):
            return OutageStatus.RESOLVED
        elif any(word in text for word in ['identified', 'root cause']):
            return OutageStatus.IDENTIFIED
        elif any(word in text for word in ['monitoring', 'watching']):
            return OutageStatus.MONITORING
        elif any(word in text for word in ['investigating', 'looking into']):
            return OutageStatus.INVESTIGATING
        else:
            return OutageStatus.INVESTIGATING


class AWSMonitor(CloudProviderMonitor):
    """AWS outage monitor"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CloudProvider.AWS, session)
        self.status_page_url = "https://status.aws.amazon.com/rss/all.rss"
        self.api_url = "https://status.aws.amazon.com/data.json"
        self.health_dashboard_url = "https://health.aws.amazon.com/health/status"
    
    async def check_status(self) -> List[OutageEvent]:
        """Check AWS status page and RSS feed"""
        outages = []
        
        # Check RSS feed
        rss_outages = await self.parse_rss_feed(self.status_page_url)
        outages.extend(rss_outages)
        
        # Check API status
        api_outages = await self.check_api_status(self.api_url)
        outages.extend(api_outages)
        
        # Check Health Dashboard (limited without authentication)
        health_outages = await self.check_health_dashboard()
        outages.extend(health_outages)
        
        return outages
    
    async def parse_rss_feed(self, feed_url: str) -> List[OutageEvent]:
        """Parse AWS RSS feed for outages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        # Check if feed.entries exists and is iterable
                        if hasattr(feed, 'entries') and feed.entries is not None:
                            for entry in feed.entries:
                                if self._is_outage_entry(entry):
                                    outage = await self._parse_aws_rss_entry(entry)
                                    if outage and outage.external_id not in self.known_outages:
                                        self.known_outages.add(outage.external_id)
                                        outages.append(outage)
                        
                        return outages
        except Exception as e:
            logger.error(f"Error parsing AWS RSS feed: {e}")
            return []
    
    async def check_api_status(self, api_url: str) -> List[OutageEvent]:
        """Check AWS API for status information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_aws_api_response(data)
        except Exception as e:
            logger.error(f"Error checking AWS API: {e}")
            return []
    
    async def check_health_dashboard(self) -> List[OutageEvent]:
        """Check AWS Health Dashboard for incidents (limited without authentication)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.health_dashboard_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info("AWS Health Dashboard is accessible but requires authentication for full data access")
                        logger.info("For real-time AWS incident data, use the AWS Health API with proper credentials")
                        # Note: Full parsing would require authentication and API access
                        return []
        except Exception as e:
            logger.error(f"Error checking AWS Health Dashboard: {e}")
            return []
    
    async def get_historical_outages(self, days: int = 365) -> List[OutageEvent]:
        """Get historical outages from AWS status page"""
        try:
            async with aiohttp.ClientSession() as session:
                # AWS status page provides historical data
                async with session.get(self.status_page_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                        
                        logger.info(f"AWS RSS feed has {len(feed.entries) if hasattr(feed, 'entries') and feed.entries else 0} entries")
                        
                        if hasattr(feed, 'entries') and feed.entries is not None and isinstance(feed.entries, list):
                            for i, entry in enumerate(feed.entries):
                                try:
                                    title = entry.get('title', '')
                                    logger.info(f"AWS Entry {i}: {title}")
                                    
                                    published = entry.get('published_parsed')
                                    if published:
                                        entry_date = datetime.fromtimestamp(published, tz=timezone.utc)
                                        logger.info(f"AWS Entry date: {entry_date}, cutoff: {cutoff_date}")
                                        if entry_date >= cutoff_date:
                                            if self._is_outage_entry(entry):
                                                logger.info(f"AWS Entry {i} is an outage entry")
                                                outage = await self._parse_aws_rss_entry(entry)
                                                if outage:
                                                    outages.append(outage)
                                                    logger.info(f"Added AWS outage: {outage.title}")
                                            else:
                                                logger.info(f"AWS Entry {i} is not an outage entry")
                                        else:
                                            logger.info(f"AWS Entry {i} is too old")
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing AWS historical entry: {entry_error}")
                                    continue
                        
                        logger.info(f"AWS historical outages found: {len(outages)}")
                        if len(outages) == 0:
                            logger.info("AWS RSS feed is empty - no recent incidents found")
                            logger.info(f"Note: AWS incidents are now reported on the Health Dashboard: {self.health_dashboard_url}")
                            logger.info("The RSS feeds are no longer updated. Consider using AWS Health API for real-time data.")
                        return outages
        except Exception as e:
            logger.error(f"Error fetching AWS historical outages: {e}")
            return []
    
    async def get_active_outages(self) -> List[OutageEvent]:
        """Get currently active (non-resolved) outages from AWS"""
        try:
            # Check RSS feed for active incidents
            async with aiohttp.ClientSession() as session:
                async with session.get(self.status_page_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        active_outages = []
                        
                        if hasattr(feed, 'entries') and feed.entries is not None and isinstance(feed.entries, list):
                            for entry in feed.entries:
                                try:
                                    if self._is_outage_entry(entry):
                                        outage = await self._parse_aws_rss_entry(entry)
                                        if outage and outage.status != OutageStatus.RESOLVED:
                                            active_outages.append(outage)
                                            logger.info(f"Found active AWS incident: {outage.title}")
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing AWS active entry: {entry_error}")
                                    continue
                        
                        logger.info(f"AWS active outages found: {len(active_outages)}")
                        return active_outages
        except Exception as e:
            logger.error(f"Error fetching AWS active outages: {e}")
            return []
    
    def _is_outage_entry(self, entry) -> bool:
        """Check if RSS entry represents an outage"""
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        
        outage_keywords = [
            'service disruption', 'increased error rates', 'degraded performance',
            'investigating', 'issue', 'problem', 'outage'
        ]
        
        return any(keyword in title or keyword in description for keyword in outage_keywords)
    
    async def _parse_aws_rss_entry(self, entry) -> Optional[OutageEvent]:
        """Parse AWS RSS entry into outage event"""
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            published = entry.get('published_parsed')
            
            severity = self._extract_severity(title, description)
            services, regions = self._extract_affected_areas(description)
            status = self._determine_outage_status(title, description)
            
            return OutageEvent(
                provider=CloudProvider.AWS,
                service=services[0] if services else "unknown",
                region=regions[0] if regions else None,
                status=status,
                title=title,
                description=description,
                severity=severity,
                start_time=datetime.fromtimestamp(published, tz=timezone.utc) if published else datetime.now(timezone.utc),
                end_time=None,
                affected_services=services,
                affected_regions=regions,
                source=OutageSource.RSS_FEED,
                external_id=entry.get('id'),
                raw_data=dict(entry)
            )
        except Exception as e:
            logger.error(f"Error parsing AWS RSS entry: {e}")
            return None
    
    async def _parse_aws_api_response(self, data: Dict[str, Any]) -> List[OutageEvent]:
        """Parse AWS API response for outages"""
        outages = []
        try:
            # Parse AWS API response structure
            # This would need to be adapted based on actual AWS API response format
            pass
        except Exception as e:
            logger.error(f"Error parsing AWS API response: {e}")
        return outages
    
    def _extract_severity(self, title: str, description: str) -> EventSeverity:
        """Extract severity from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['critical', 'severe', 'major']):
            return EventSeverity.CRITICAL
        elif any(word in text for word in ['high', 'significant']):
            return EventSeverity.HIGH
        elif any(word in text for word in ['medium', 'moderate']):
            return EventSeverity.MEDIUM
        elif any(word in text for word in ['low', 'minor']):
            return EventSeverity.LOW
        else:
            return EventSeverity.INFO
    
    def _extract_affected_areas(self, description: str) -> tuple[List[str], List[str]]:
        """Extract affected services and regions from description"""
        services = []
        regions = []
        
        # Handle None or empty description
        if not description:
            return services, regions
        
        # Common AWS services
        aws_services = [
            'ec2', 's3', 'rds', 'lambda', 'dynamodb', 'cloudfront',
            'route 53', 'elastic load balancing', 'auto scaling',
            'cloudwatch', 'sns', 'sqs', 'api gateway'
        ]
        
        # Common AWS regions
        aws_regions = [
            'us-east-1', 'us-west-1', 'us-west-2', 'us-east-2',
            'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'
        ]
        
        text = description.lower()
        
        for service in aws_services:
            if service in text:
                services.append(service)
        
        for region in aws_regions:
            if region in text:
                regions.append(region)
        
        return services, regions
    
    def _determine_outage_status(self, title: str, description: str) -> OutageStatus:
        """Determine outage status from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['resolved', 'fixed', 'restored']):
            return OutageStatus.RESOLVED
        elif any(word in text for word in ['identified', 'root cause']):
            return OutageStatus.IDENTIFIED
        elif any(word in text for word in ['monitoring', 'watching']):
            return OutageStatus.MONITORING
        elif any(word in text for word in ['investigating', 'looking into']):
            return OutageStatus.INVESTIGATING
        else:
            return OutageStatus.INVESTIGATING


class AzureMonitor(CloudProviderMonitor):
    """Azure outage monitor"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CloudProvider.AZURE, session)
        self.status_page_url = "https://status.azure.com/en-us/status/feed/"
        self.api_url = "https://status.azure.com/api/status"
    
    async def check_status(self) -> List[OutageEvent]:
        """Check Azure status page and RSS feed"""
        outages = []
        
        try:
            # Check RSS feed
            rss_outages = await self.parse_rss_feed(self.status_page_url)
            if rss_outages:
                outages.extend(rss_outages)
            
            # Check API status
            api_outages = await self.check_api_status(self.api_url)
            if api_outages:
                outages.extend(api_outages)
        except Exception as e:
            logger.error(f"Error in Azure check_status: {e}")
        
        return outages
    
    async def parse_rss_feed(self, feed_url: str) -> List[OutageEvent]:
        """Parse Azure RSS feed for outages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        # Check if feed.entries exists and is iterable
                        if hasattr(feed, 'entries') and feed.entries is not None and isinstance(feed.entries, list):
                            for entry in feed.entries:
                                try:
                                    if self._is_outage_entry(entry):
                                        outage = await self._parse_azure_rss_entry(entry)
                                        if outage and outage.external_id not in self.known_outages:
                                            self.known_outages.add(outage.external_id)
                                            outages.append(outage)
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing Azure RSS entry: {entry_error}")
                                    continue
                        
                        return outages
                    else:
                        logger.warning(f"Azure RSS feed returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error parsing Azure RSS feed: {e}")
            return []
    
    async def check_api_status(self, api_url: str) -> List[OutageEvent]:
        """Check Azure API for status information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_azure_api_response(data)
        except Exception as e:
            logger.error(f"Error checking Azure API: {e}")
            return []
    
    async def get_historical_outages(self, days: int = 365) -> List[OutageEvent]:
        """Get historical outages from Azure status page"""
        try:
            async with aiohttp.ClientSession() as session:
                # Azure status page provides historical data
                async with session.get(self.status_page_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                        
                        if hasattr(feed, 'entries') and feed.entries is not None and isinstance(feed.entries, list):
                            for entry in feed.entries:
                                try:
                                    published = entry.get('published_parsed')
                                    if published:
                                        entry_date = datetime.fromtimestamp(published, tz=timezone.utc)
                                        if entry_date >= cutoff_date:
                                            if self._is_outage_entry(entry):
                                                outage = await self._parse_azure_rss_entry(entry)
                                                if outage:
                                                    outages.append(outage)
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing Azure historical entry: {entry_error}")
                                    continue
                        
                        logger.info(f"Azure historical outages found: {len(outages)}")
                        if len(outages) == 0:
                            logger.info("Azure RSS feed is empty - no recent incidents found")
                        return outages
        except Exception as e:
            logger.error(f"Error fetching Azure historical outages: {e}")
            return []
    
    async def get_active_outages(self) -> List[OutageEvent]:
        """Get currently active (non-resolved) outages from Azure"""
        try:
            # Check RSS feed for active incidents
            async with aiohttp.ClientSession() as session:
                async with session.get(self.status_page_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        active_outages = []
                        
                        if hasattr(feed, 'entries') and feed.entries is not None and isinstance(feed.entries, list):
                            for entry in feed.entries:
                                try:
                                    if self._is_outage_entry(entry):
                                        outage = await self._parse_azure_rss_entry(entry)
                                        if outage and outage.status != OutageStatus.RESOLVED:
                                            active_outages.append(outage)
                                            logger.info(f"Found active Azure incident: {outage.title}")
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing Azure active entry: {entry_error}")
                                    continue
                        
                        logger.info(f"Azure active outages found: {len(active_outages)}")
                        return active_outages
        except Exception as e:
            logger.error(f"Error fetching Azure active outages: {e}")
            return []
    
    def _is_outage_entry(self, entry) -> bool:
        """Check if RSS entry represents an outage"""
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        
        outage_keywords = [
            'service disruption', 'degraded performance', 'investigating',
            'issue', 'problem', 'outage', 'unavailable'
        ]
        
        return any(keyword in title or keyword in description for keyword in outage_keywords)
    
    async def _parse_azure_rss_entry(self, entry) -> Optional[OutageEvent]:
        """Parse Azure RSS entry into outage event"""
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            published = entry.get('published_parsed')
            
            severity = self._extract_severity(title, description)
            services, regions = self._extract_affected_areas(description)
            status = self._determine_outage_status(title, description)
            
            return OutageEvent(
                provider=CloudProvider.AZURE,
                service=services[0] if services else "unknown",
                region=regions[0] if regions else None,
                status=status,
                title=title,
                description=description,
                severity=severity,
                start_time=datetime.fromtimestamp(published, tz=timezone.utc) if published else datetime.now(timezone.utc),
                end_time=None,
                affected_services=services,
                affected_regions=regions,
                source=OutageSource.RSS_FEED,
                external_id=entry.get('id'),
                raw_data=dict(entry)
            )
        except Exception as e:
            logger.error(f"Error parsing Azure RSS entry: {e}")
            return None
    
    async def _parse_azure_api_response(self, data: Dict[str, Any]) -> List[OutageEvent]:
        """Parse Azure API response for outages"""
        outages = []
        try:
            # Parse Azure API response structure
            # This would need to be adapted based on actual Azure API response format
            pass
        except Exception as e:
            logger.error(f"Error parsing Azure API response: {e}")
        return outages
    
    def _extract_severity(self, title: str, description: str) -> EventSeverity:
        """Extract severity from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['critical', 'severe', 'major']):
            return EventSeverity.CRITICAL
        elif any(word in text for word in ['high', 'significant']):
            return EventSeverity.HIGH
        elif any(word in text for word in ['medium', 'moderate']):
            return EventSeverity.MEDIUM
        elif any(word in text for word in ['low', 'minor']):
            return EventSeverity.LOW
        else:
            return EventSeverity.INFO
    
    def _extract_affected_areas(self, description: str) -> tuple[List[str], List[str]]:
        """Extract affected services and regions from description"""
        services = []
        regions = []
        
        # Handle None or empty description
        if not description:
            return services, regions
        
        # Common Azure services
        azure_services = [
            'virtual machines', 'app service', 'storage', 'sql database',
            'functions', 'kubernetes service', 'load balancer',
            'virtual network', 'dns', 'cdn', 'monitor'
        ]
        
        # Common Azure regions
        azure_regions = [
            'east us', 'west us', 'central us', 'north central us',
            'west europe', 'north europe', 'east asia', 'southeast asia'
        ]
        
        text = description.lower()
        
        for service in azure_services:
            if service in text:
                services.append(service)
        
        for region in azure_regions:
            if region in text:
                regions.append(region)
        
        return services, regions
    
    def _determine_outage_status(self, title: str, description: str) -> OutageStatus:
        """Determine outage status from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['resolved', 'fixed', 'restored']):
            return OutageStatus.RESOLVED
        elif any(word in text for word in ['identified', 'root cause']):
            return OutageStatus.IDENTIFIED
        elif any(word in text for word in ['monitoring', 'watching']):
            return OutageStatus.MONITORING
        elif any(word in text for word in ['investigating', 'looking into']):
            return OutageStatus.INVESTIGATING
        else:
            return OutageStatus.INVESTIGATING


class OCIMonitor(CloudProviderMonitor):
    """Oracle Cloud Infrastructure outage monitor"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CloudProvider.OCI, session)
        self.status_page_url = "https://ocistatus.oraclecloud.com/api/v2/incident-summary.rss"
        self.api_url = "https://ocistatus.oraclecloud.com/api/v1/status"
    
    async def check_status(self) -> List[OutageEvent]:
        """Check OCI status page and RSS feed"""
        outages = []
        
        try:
            # Check RSS feed
            rss_outages = await self.parse_rss_feed(self.status_page_url)
            if rss_outages:
                outages.extend(rss_outages)
            
            # Check API status
            api_outages = await self.check_api_status(self.api_url)
            if api_outages:
                outages.extend(api_outages)
        except Exception as e:
            logger.error(f"Error in OCI check_status: {e}")
        
        return outages
    
    async def parse_rss_feed(self, feed_url: str) -> List[OutageEvent]:
        """Parse OCI RSS feed for outages"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        # Check if feed.entries exists and is iterable
                        if hasattr(feed, 'entries') and feed.entries is not None:
                            for entry in feed.entries:
                                # Check if this is an outage-related entry
                                if self._is_outage_entry(entry):
                                    outage = await self._parse_oci_rss_entry(entry)
                                    if outage and outage.external_id not in self.known_outages:
                                        self.known_outages.add(outage.external_id)
                                        outages.append(outage)
                        
                        return outages
        except Exception as e:
            logger.error(f"Error parsing OCI RSS feed: {e}")
            return []
    
    async def check_api_status(self, api_url: str) -> List[OutageEvent]:
        """Check OCI API for status information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_oci_api_response(data)
        except Exception as e:
            logger.error(f"Error checking OCI API: {e}")
            return []
    
    async def get_historical_outages(self, days: int = 365) -> List[OutageEvent]:
        """Get historical outages from OCI RSS feed"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.status_page_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        outages = []
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                        
                        if hasattr(feed, 'entries') and feed.entries:
                            for entry in feed.entries:
                                try:
                                    # Check if this is an outage-related entry
                                    if self._is_outage_entry(entry):
                                        outage = await self._parse_oci_rss_entry(entry)
                                        if outage:
                                            # Check if incident is within the time window
                                            if outage.start_time >= cutoff_date:
                                                outages.append(outage)
                                                logger.info(f"Added OCI historical incident: {outage.title}")
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing OCI historical entry: {entry_error}")
                                    continue
                        
                        logger.info(f"OCI RSS feed returned {len(outages)} historical incidents")
                        return outages
                    else:
                        logger.warning(f"OCI RSS feed returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting OCI historical outages: {e}")
            return []
    
    async def get_active_outages(self) -> List[OutageEvent]:
        """Get currently active (non-resolved) outages from OCI"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.status_page_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        feed = feedparser.parse(content)
                        
                        active_outages = []
                        
                        if hasattr(feed, 'entries') and feed.entries:
                            for entry in feed.entries:
                                try:
                                    # Check if this is an outage-related entry
                                    if self._is_outage_entry(entry):
                                        outage = await self._parse_oci_rss_entry(entry)
                                        if outage and outage.status != OutageStatus.RESOLVED:
                                            active_outages.append(outage)
                                            logger.info(f"Found active OCI incident: {outage.title}")
                                except Exception as entry_error:
                                    logger.warning(f"Error parsing OCI active entry: {entry_error}")
                                    continue
                        
                        logger.info(f"OCI RSS feed returned {len(active_outages)} active incidents")
                        return active_outages
                    else:
                        logger.warning(f"OCI RSS feed returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error getting OCI active outages: {e}")
            return []
    
    def _is_outage_entry(self, entry) -> bool:
        """Check if RSS entry represents an outage"""
        title = entry.get('title', '').lower()
        description = entry.get('description', '').lower()
        
        outage_keywords = [
            'outage', 'issue', 'problem', 'degraded', 'investigating',
            'incident', 'disruption', 'unavailable', 'error'
        ]
        
        return any(keyword in title or keyword in description for keyword in outage_keywords)
    
    async def _parse_oci_rss_entry(self, entry) -> Optional[OutageEvent]:
        """Parse OCI RSS entry into outage event"""
        try:
            title = entry.get('title', '')
            description = entry.get('description', '')
            published = entry.get('published_parsed')
            
            # Extract severity from title/description
            severity = self._extract_severity(title, description)
            
            # Extract affected services and regions
            services, regions = self._extract_affected_areas(description)
            
            # Determine outage status
            status = self._determine_outage_status(title, description)
            
            # Extract start and end times from description
            start_time = None
            end_time = None
            
            # Look for start time patterns like "Start Time : April 28, 2025 10:35 UTC"
            start_match = re.search(r'Start Time\s*:\s*([^<]+?)(?:\s|$)', description, re.IGNORECASE)
            if start_match:
                start_time_str = start_match.group(1).strip()
                try:
                    start_time = datetime.strptime(start_time_str, "%B %d, %Y %H:%M UTC")
                    start_time = start_time.replace(tzinfo=timezone.utc)
                except ValueError:
                    start_time = datetime.now(timezone.utc)
            
            # Look for end time patterns like "End Time : April 28, 2025 22:29 UTC"
            end_match = re.search(r'End Time\s*:\s*([^<]+?)(?:\s|$)', description, re.IGNORECASE)
            if end_match:
                end_time_str = end_match.group(1).strip()
                try:
                    end_time = datetime.strptime(end_time_str, "%B %d, %Y %H:%M UTC")
                    end_time = end_time.replace(tzinfo=timezone.utc)
                except ValueError:
                    end_time = None
            
            # If no start time found, use published time
            if not start_time and published:
                start_time = datetime.fromtimestamp(published, tz=timezone.utc)
            elif not start_time:
                start_time = datetime.now(timezone.utc)
            
            return OutageEvent(
                provider=CloudProvider.OCI,
                service=services[0] if services else "unknown",
                region=regions[0] if regions else None,
                status=status,
                title=title,
                description=description,
                severity=severity,
                start_time=datetime.fromtimestamp(published, tz=timezone.utc) if published else datetime.now(timezone.utc),
                end_time=None,
                affected_services=services,
                affected_regions=regions,
                source=OutageSource.RSS_FEED,
                external_id=entry.get('id'),
                raw_data=dict(entry)
            )
        except Exception as e:
            logger.error(f"Error parsing OCI RSS entry: {e}")
            return None
    
    async def _parse_oci_api_response(self, data: Dict[str, Any]) -> List[OutageEvent]:
        """Parse OCI API response for outages"""
        outages = []
        try:
            # Parse OCI API response structure
            # This would need to be adapted based on actual OCI API response format
            pass
        except Exception as e:
            logger.error(f"Error parsing OCI API response: {e}")
        
        return outages
    
    def _extract_severity(self, title: str, description: str) -> EventSeverity:
        """Extract severity from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['critical', 'severe', 'major']):
            return EventSeverity.CRITICAL
        elif any(word in text for word in ['high', 'significant']):
            return EventSeverity.HIGH
        elif any(word in text for word in ['medium', 'moderate']):
            return EventSeverity.MEDIUM
        else:
            return EventSeverity.LOW
    
    def _extract_affected_areas(self, description: str) -> tuple[List[str], List[str]]:
        """Extract affected services and regions from description"""
        if not description:
            return [], []
        
        services = []
        regions = []
        
        # Common OCI services
        oci_services = [
            'compute', 'storage', 'database', 'network', 'identity',
            'monitoring', 'logging', 'analytics', 'ai', 'ml'
        ]
        
        # Common OCI regions
        oci_regions = [
            'us-ashburn-1', 'us-phoenix-1', 'us-sanjose-1', 'us-frankfurt-1',
            'uk-london-1', 'uk-gov-london-1', 'ca-toronto-1', 'ca-montreal-1',
            'ap-tokyo-1', 'ap-seoul-1', 'ap-sydney-1', 'ap-mumbai-1',
            'ap-singapore-1', 'ap-osaka-1', 'eu-frankfurt-1', 'eu-zurich-1'
        ]
        
        text = description.lower()
        
        for service in oci_services:
            if service in text:
                services.append(service)
        
        for region in oci_regions:
            if region in text:
                regions.append(region)
        
        return services, regions
    
    def _determine_outage_status(self, title: str, description: str) -> OutageStatus:
        """Determine outage status from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['resolved', 'fixed', 'restored']):
            return OutageStatus.RESOLVED
        elif any(word in text for word in ['investigating', 'identified']):
            return OutageStatus.IDENTIFIED
        elif any(word in text for word in ['monitoring', 'watching']):
            return OutageStatus.MONITORING
        else:
            return OutageStatus.INVESTIGATING


class OutageMonitoringService:
    """Main outage monitoring service"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.monitors = {
            CloudProvider.GCP: GCPMonitor(session),
            CloudProvider.AWS: AWSMonitor(session),
            CloudProvider.AZURE: AzureMonitor(session),
            CloudProvider.OCI: OCIMonitor(session),
        }
        self.running = True  # Start monitoring by default
        self.check_interval = 300  # 5 minutes
        self.last_check_time = None
        self.monitoring_task = None
    
    async def start_monitoring(self):
        """Start the outage monitoring service"""
        self.running = True
        logger.info("Starting outage monitoring service")
        
        # Run initial check immediately
        await self.check_all_providers()
        
        while self.running:
            try:
                await asyncio.sleep(self.check_interval)
                if self.running:  # Check again in case we were stopped during sleep
                    await self.check_all_providers()
            except Exception as e:
                logger.error(f"Error in outage monitoring: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error
    
    async def stop_monitoring(self):
        """Stop the outage monitoring service"""
        self.running = False
        logger.info("Stopping outage monitoring service")
    
    async def pause_monitoring(self):
        """Pause the outage monitoring service"""
        self.running = False
        logger.info("Pausing outage monitoring service")
    
    async def resume_monitoring(self):
        """Resume the outage monitoring service"""
        self.running = True
        logger.info("Resuming outage monitoring service")
        # Start monitoring in background
        asyncio.create_task(self.start_monitoring())
    
    async def check_all_providers(self):
        """Check all cloud providers for outages"""
        self.last_check_time = datetime.now(timezone.utc)
        
        for provider, monitor in self.monitors.items():
            try:
                logger.info(f"Checking {provider.value} for outages...")
                monitor.last_check = datetime.now(timezone.utc)  # Update last check time for each provider
                outages = await monitor.check_status()
                
                for outage in outages:
                    await self.process_outage(outage)
                    
            except Exception as e:
                logger.error(f"Error checking {provider.value}: {e}")
    
    async def process_outage(self, outage: OutageEvent):
        """Process detected outage and create events"""
        try:
            # Check if this outage already exists to prevent duplicates
            if outage.external_id:
                existing_query = select(CloudEvent).where(
                    and_(
                        CloudEvent.external_id == outage.external_id,
                        CloudEvent.event_type == EventType.OUTAGE_STATUS,
                        CloudEvent.cloud_provider == outage.provider
                    )
                )
                existing_result = await self.session.execute(existing_query)
                existing_event = existing_result.scalar_one_or_none()
                
                if existing_event:
                    logger.info(f"Outage already exists: {outage.external_id} for {outage.provider.value}")
                    return
            
            # Create cloud event
            event = CloudEvent(
                event_id=f"outage-{outage.provider.value}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                external_id=outage.external_id,
                event_type=EventType.OUTAGE_STATUS,
                severity=outage.severity,
                status=EventStatus.ACTIVE if outage.status != OutageStatus.RESOLVED else EventStatus.RESOLVED,
                cloud_provider=outage.provider,
                project_id=None,  # Will be set by subscription matching
                subscription_id=None,
                title=outage.title,
                description=outage.description,
                summary=f"{outage.provider.value.upper()} {outage.service} outage detected",
                service_name=outage.service,
                resource_type="cloud_service",
                resource_id=outage.service,
                region=outage.region,
                event_time=outage.start_time,
                resolved_at=outage.end_time,
                raw_data={
                    "outage_status": outage.status.value,
                    "affected_services": outage.affected_services,
                    "affected_regions": outage.affected_regions,
                    "source": outage.source.value,
                    "raw_outage_data": outage.raw_data
                },
                tenant_id="default"
            )
            
            self.session.add(event)
            await self.session.commit()
            await self.session.refresh(event)
            
            logger.info(f"Created outage event: {event.event_id} for {outage.provider.value}")
            
            # Process subscriptions and trigger webhooks
            await self._process_outage_subscriptions(event)
            
        except Exception as e:
            logger.error(f"Error processing outage: {e}")
    
    async def _process_outage_subscriptions(self, event: CloudEvent):
        """Process outage event against subscriptions and trigger webhooks"""
        try:
            # Get subscriptions that match this outage
            query = select(EventSubscription).where(
                and_(
                    EventSubscription.enabled == True,
                    EventSubscription.tenant_id == "default",
                    EventSubscription.event_types.contains([EventType.OUTAGE_STATUS.value])
                )
            )
            
            result = await self.session.execute(query)
            subscriptions = result.scalars().all()
            
            for subscription in subscriptions:
                if await self._check_outage_matches_subscription(event, subscription):
                    # Trigger webhook for this subscription
                    await self._trigger_outage_webhook(event, subscription)
                    
        except Exception as e:
            logger.error(f"Error processing outage subscriptions: {e}")
    
    async def _check_outage_matches_subscription(self, event: CloudEvent, subscription: EventSubscription) -> bool:
        """Check if outage event matches subscription criteria"""
        try:
            # Check if subscription is for this cloud provider
            if subscription.services and event.service_name:
                if event.service_name not in subscription.services:
                    return False
            
            # Check regions
            if subscription.regions and event.region:
                if event.region not in subscription.regions:
                    return False
            
            # Check severity levels
            if subscription.severity_levels and event.severity:
                if event.severity not in subscription.severity_levels:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking outage match: {e}")
            return False
    
    async def _trigger_outage_webhook(self, event: CloudEvent, subscription: EventSubscription):
        """Trigger webhook for outage event"""
        try:
            if not subscription.webhook_url:
                return
            
            webhook_data = {
                "event_type": "outage_detected",
                "subscription_id": subscription.subscription_id,
                "subscription_name": subscription.name,
                "outage": {
                    "event_id": event.event_id,
                    "provider": event.cloud_provider.value,
                    "service": event.service_name,
                    "region": event.region,
                    "severity": event.severity.value,
                    "status": event.raw_data.get("outage_status"),
                    "title": event.title,
                    "description": event.description,
                    "start_time": event.event_time.isoformat(),
                    "affected_services": event.raw_data.get("affected_services", []),
                    "affected_regions": event.raw_data.get("affected_regions", [])
                },
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Audit-Service-Outage-Monitor/1.0"
            }
            
            # Add custom headers if configured
            if subscription.webhook_headers:
                try:
                    custom_headers = json.loads(subscription.webhook_headers)
                    headers.update(custom_headers)
                except:
                    pass
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    subscription.webhook_url,
                    json=webhook_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status in [200, 201, 202]:
                        logger.info(f"Outage webhook sent successfully to {subscription.webhook_url}")
                    else:
                        logger.warning(f"Outage webhook failed with status {response.status}")
                        
        except Exception as e:
            logger.error(f"Error triggering outage webhook: {e}")
    
    async def manual_check(self, provider: CloudProvider) -> List[OutageEvent]:
        """Manually check a specific provider for outages"""
        if provider in self.monitors:
            monitor = self.monitors[provider]
            monitor.last_check = datetime.now(timezone.utc)  # Update last check time
            return await monitor.check_status()
        return []
    
    async def get_historical_outages_from_providers(self, days: int = 365, provider: Optional[CloudProvider] = None) -> List[OutageEvent]:
        """Get historical outages directly from cloud provider APIs"""
        all_outages = []
        
        if provider:
            # Get historical data for specific provider
            if provider in self.monitors:
                monitor = self.monitors[provider]
                outages = await monitor.get_historical_outages(days)
                all_outages.extend(outages)
        else:
            # Get historical data for all providers
            for provider, monitor in self.monitors.items():
                try:
                    outages = await monitor.get_historical_outages(days)
                    all_outages.extend(outages)
                except Exception as e:
                    logger.error(f"Error getting historical outages for {provider.value}: {e}")
        
        return all_outages
    
    async def get_all_active_outages(self) -> List[OutageEvent]:
        """Get all currently active (non-resolved) outages across all providers"""
        active_outages = []
        
        for provider, monitor in self.monitors.items():
            try:
                logger.info(f"Getting active outages from {provider.value}...")
                provider_active_outages = await monitor.get_active_outages()
                active_outages.extend(provider_active_outages)
                logger.info(f"Found {len(provider_active_outages)} active outages from {provider.value}")
            except Exception as e:
                logger.error(f"Error getting active outages from {provider.value}: {e}")
                continue
        
        logger.info(f"Total active outages across all providers: {len(active_outages)}")
        return active_outages
    
    def get_monitoring_status(self) -> dict:
        """Get current monitoring status"""
        return {
            "service_status": "running" if self.running else "paused",
            "check_interval_seconds": self.check_interval,
            "last_check_time": self.last_check_time.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00" if self.last_check_time else None,
            "monitored_providers": [
                {
                    "provider": provider.value,
                    "last_check": monitor.last_check.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00" if monitor.last_check else None,
                    "known_outages_count": len(monitor.known_outages)
                }
                for provider, monitor in self.monitors.items()
            ]
        }
    
    async def add_custom_monitor(self, provider: CloudProvider, monitor: CloudProviderMonitor):
        """Add a custom monitor for a provider"""
        self.monitors[provider] = monitor
        logger.info(f"Added custom monitor for {provider.value}")
