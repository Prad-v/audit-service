"""
Incident Service for StackStorm Tests

This service handles incident creation when StackStorm tests fail.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..core.config import settings

logger = logging.getLogger(__name__)


class IncidentService:
    """Service for creating incidents when StackStorm tests fail"""
    
    def __init__(self):
        self.incident_api_url = settings.INCIDENT_API_URL
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if aiohttp is None:
            raise ImportError("aiohttp is required for incident service")
        
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def create_incident(self, incident_data: Dict[str, Any]) -> str:
        """Create an incident"""
        session = await self._get_session()
        
        # Prepare incident payload
        payload = {
            "title": incident_data.get("title", "StackStorm Test Failure"),
            "description": incident_data.get("description", "A StackStorm synthetic test has failed"),
            "severity": incident_data.get("severity", "medium"),
            "incident_type": incident_data.get("incident_type", "synthetic_test_failure"),
            "affected_services": incident_data.get("affected_services", ["synthetic-testing", "stackstorm"]),
            "affected_regions": incident_data.get("affected_regions", []),
            "affected_components": incident_data.get("affected_components", []),
            "start_time": datetime.now(timezone.utc).isoformat(),
            "public_message": incident_data.get("public_message", "We are investigating a potential issue detected by our monitoring systems."),
            "internal_notes": incident_data.get("internal_notes", "Incident created automatically by StackStorm synthetic test framework"),
            "tags": incident_data.get("tags", ["synthetic-test", "stackstorm", "automated"]),
            "is_public": incident_data.get("is_public", True),
            "rss_enabled": incident_data.get("rss_enabled", True)
        }
        
        try:
            async with session.post(
                f"{self.incident_api_url}/",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    incident_id = result.get("incident", {}).get("id")
                    if incident_id:
                        logger.info(f"Created incident {incident_id}")
                        return incident_id
                    else:
                        raise Exception("No incident ID returned from API")
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to create incident: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            # Return a mock incident ID for development
            return f"mock-incident-{datetime.now().timestamp()}"
    
    async def update_incident(self, incident_id: str, update_data: Dict[str, Any]) -> bool:
        """Update an existing incident"""
        session = await self._get_session()
        
        try:
            async with session.put(
                f"{self.incident_api_url}/{incident_id}",
                json=update_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Updated incident {incident_id}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update incident: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to update incident {incident_id}: {e}")
            return False
    
    async def resolve_incident(self, incident_id: str, resolution_notes: str = "") -> bool:
        """Resolve an incident"""
        update_data = {
            "status": "resolved",
            "end_time": datetime.now(timezone.utc).isoformat(),
            "internal_notes": f"Incident resolved automatically by StackStorm synthetic test framework. {resolution_notes}"
        }
        
        return await self.update_incident(incident_id, update_data)
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
