"""
NATS service for the audit log framework.

This module provides NATS-based message queuing functionality with
connection management and basic pub/sub operations.
"""

from typing import Any, Dict, Optional
import structlog

from app.config import NATSSettings
from app.core.exceptions import MessageQueueError

logger = structlog.get_logger(__name__)


class NATSService:
    """NATS message queue service."""
    
    def __init__(self, settings: NATSSettings):
        self.settings = settings
        self._client = None
        self._connected = False
    
    async def initialize(self) -> None:
        """Initialize NATS connection."""
        try:
            # This will be implemented with actual NATS client
            self._connected = True
            logger.info("NATS service initialized (stub)")
        except Exception as e:
            logger.error("Failed to initialize NATS", error=str(e))
            raise MessageQueueError(f"NATS initialization failed: {str(e)}")
    
    async def close(self) -> None:
        """Close NATS connection."""
        self._connected = False
        logger.info("NATS service closed (stub)")
    
    def is_connected(self) -> bool:
        """Check if NATS is connected."""
        return self._connected
    
    async def publish(self, subject: str, data: bytes) -> None:
        """Publish message to NATS subject."""
        logger.debug("NATS publish operation (stub)", subject=subject)
    
    async def subscribe(self, subject: str, callback, queue: Optional[str] = None) -> None:
        """Subscribe to NATS subject."""
        logger.debug("NATS subscribe operation (stub)", subject=subject, queue=queue)
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get NATS server info."""
        return {
            "server_id": "test-server",
            "server_name": "nats-server",
            "version": "2.10.0",
            "max_payload": 1048576,
        }


# Global NATS service instance
_nats_service: Optional[NATSService] = None


def get_nats_service() -> NATSService:
    """Get the global NATS service instance."""
    global _nats_service
    if not _nats_service:
        raise MessageQueueError("NATS service not initialized")
    return _nats_service


async def get_nats_service_async() -> NATSService:
    """Dependency to get NATS service."""
    global _nats_service
    if not _nats_service:
        raise MessageQueueError("NATS service not initialized")
    return _nats_service