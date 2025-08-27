"""
Google Cloud Pub/Sub service with NATS fallback.

This service provides Pub/Sub integration for cloud-based message processing
with automatic fallback to NATS for local development and hybrid deployments.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

import structlog
from google.cloud import pubsub_v1
from google.cloud.exceptions import GoogleCloudError
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.nats_service import NATSService

logger = structlog.get_logger(__name__)

settings = get_settings()


class PubSubConfig(BaseModel):
    """Pub/Sub configuration."""
    project_id: str
    topic_name: str
    subscription_name: str
    max_messages: int = 100
    ack_deadline_seconds: int = 60
    message_retention_duration: int = 604800  # 7 days
    enable_message_ordering: bool = False
    enable_exactly_once_delivery: bool = False


class PubSubMessage(BaseModel):
    """Pub/Sub message wrapper."""
    data: Dict[str, Any]
    attributes: Optional[Dict[str, str]] = None
    message_id: Optional[str] = None
    publish_time: Optional[str] = None
    ordering_key: Optional[str] = None


class PubSubService:
    """
    Google Cloud Pub/Sub service with NATS fallback.
    
    Provides high-performance message publishing and subscription using
    Google Cloud Pub/Sub with automatic fallback to NATS for local development.
    """
    
    def __init__(
        self,
        config: Optional[PubSubConfig] = None,
        fallback_service: Optional[NATSService] = None
    ):
        self.config = config or self._get_default_config()
        self.fallback_service = fallback_service
        self.publisher_client: Optional[pubsub_v1.PublisherClient] = None
        self.subscriber_client: Optional[pubsub_v1.SubscriberClient] = None
        self.topic_path: Optional[str] = None
        self.subscription_path: Optional[str] = None
        self._is_available = False
        self._message_handlers: Dict[str, Callable] = {}
        
        # Initialize Pub/Sub clients if configuration is available
        if self._should_use_pubsub():
            self._initialize_clients()
    
    def _get_default_config(self) -> PubSubConfig:
        """Get default Pub/Sub configuration from settings."""
        return PubSubConfig(
            project_id=getattr(settings, 'gcp_project_id', ''),
            topic_name=getattr(settings, 'pubsub_topic_name', 'audit-events'),
            subscription_name=getattr(settings, 'pubsub_subscription_name', 'audit-processor'),
            max_messages=getattr(settings, 'pubsub_max_messages', 100),
            ack_deadline_seconds=getattr(settings, 'pubsub_ack_deadline', 60),
            message_retention_duration=getattr(settings, 'pubsub_retention', 604800),
            enable_message_ordering=getattr(settings, 'pubsub_ordering', False),
            enable_exactly_once_delivery=getattr(settings, 'pubsub_exactly_once', False)
        )
    
    def _should_use_pubsub(self) -> bool:
        """Check if Pub/Sub should be used based on configuration."""
        return (
            bool(self.config.project_id) and
            settings.environment in ['staging', 'production'] and
            getattr(settings, 'use_pubsub', False)
        )
    
    def _initialize_clients(self) -> None:
        """Initialize Pub/Sub clients and topic/subscription paths."""
        try:
            # Initialize clients
            self.publisher_client = pubsub_v1.PublisherClient()
            self.subscriber_client = pubsub_v1.SubscriberClient()
            
            # Create topic and subscription paths
            self.topic_path = self.publisher_client.topic_path(
                self.config.project_id, self.config.topic_name
            )
            self.subscription_path = self.subscriber_client.subscription_path(
                self.config.project_id, self.config.subscription_name
            )
            
            # Ensure topic and subscription exist
            self._ensure_topic_exists()
            self._ensure_subscription_exists()
            self._is_available = True
            
            logger.info(
                "Pub/Sub clients initialized",
                project_id=self.config.project_id,
                topic_name=self.config.topic_name,
                subscription_name=self.config.subscription_name
            )
            
        except Exception as e:
            logger.warning(
                "Failed to initialize Pub/Sub clients",
                error=str(e),
                fallback_enabled=self.fallback_service is not None
            )
            self._is_available = False
    
    def _ensure_topic_exists(self) -> None:
        """Ensure the Pub/Sub topic exists."""
        if not self.publisher_client or not self.topic_path:
            return
        
        try:
            # Try to get the topic
            self.publisher_client.get_topic(request={"topic": self.topic_path})
            logger.info("Pub/Sub topic exists", topic_name=self.config.topic_name)
            
        except Exception:
            # Create the topic if it doesn't exist
            logger.info("Creating Pub/Sub topic", topic_name=self.config.topic_name)
            
            topic_config = {}
            if self.config.enable_message_ordering:
                topic_config["message_storage_policy"] = {
                    "allowed_persistence_regions": [settings.region]
                }
            
            self.publisher_client.create_topic(
                request={
                    "name": self.topic_path,
                    **topic_config
                }
            )
            logger.info("Pub/Sub topic created", topic_name=self.config.topic_name)
    
    def _ensure_subscription_exists(self) -> None:
        """Ensure the Pub/Sub subscription exists."""
        if not self.subscriber_client or not self.subscription_path or not self.topic_path:
            return
        
        try:
            # Try to get the subscription
            self.subscriber_client.get_subscription(
                request={"subscription": self.subscription_path}
            )
            logger.info("Pub/Sub subscription exists", subscription_name=self.config.subscription_name)
            
        except Exception:
            # Create the subscription if it doesn't exist
            logger.info("Creating Pub/Sub subscription", subscription_name=self.config.subscription_name)
            
            subscription_config = {
                "name": self.subscription_path,
                "topic": self.topic_path,
                "ack_deadline_seconds": self.config.ack_deadline_seconds,
                "message_retention_duration": {
                    "seconds": self.config.message_retention_duration
                },
            }
            
            if self.config.enable_exactly_once_delivery:
                subscription_config["enable_exactly_once_delivery"] = True
            
            if self.config.enable_message_ordering:
                subscription_config["enable_message_ordering"] = True
            
            self.subscriber_client.create_subscription(request=subscription_config)
            logger.info("Pub/Sub subscription created", subscription_name=self.config.subscription_name)
    
    async def publish_message(
        self,
        data: Dict[str, Any],
        attributes: Optional[Dict[str, str]] = None,
        ordering_key: Optional[str] = None
    ) -> str:
        """
        Publish a message to the topic.
        
        Args:
            data: Message data
            attributes: Message attributes
            ordering_key: Ordering key for message ordering
            
        Returns:
            Message ID
        """
        if self._is_available and self.publisher_client:
            try:
                return await self._publish_message_pubsub(data, attributes, ordering_key)
            except Exception as e:
                logger.error(
                    "Failed to publish message to Pub/Sub",
                    error=str(e),
                    data_keys=list(data.keys()) if data else []
                )
                
                # Fall back to NATS if available
                if self.fallback_service:
                    logger.info("Falling back to NATS for message publishing")
                    return await self.fallback_service.publish_message(
                        self.config.topic_name, data
                    )
                raise
        
        # Use fallback service if Pub/Sub is not available
        if self.fallback_service:
            return await self.fallback_service.publish_message(
                self.config.topic_name, data
            )
        
        raise RuntimeError("No message publishing backend available")
    
    async def _publish_message_pubsub(
        self,
        data: Dict[str, Any],
        attributes: Optional[Dict[str, str]] = None,
        ordering_key: Optional[str] = None
    ) -> str:
        """Publish message to Pub/Sub."""
        if not self.publisher_client or not self.topic_path:
            raise RuntimeError("Pub/Sub publisher not initialized")
        
        # Prepare message data
        message_data = json.dumps(data).encode('utf-8')
        message_attributes = attributes or {}
        
        def _publish():
            publish_kwargs = {
                "topic": self.topic_path,
                "data": message_data,
                "attributes": message_attributes,
            }
            
            if ordering_key and self.config.enable_message_ordering:
                publish_kwargs["ordering_key"] = ordering_key
            
            future = self.publisher_client.publish(**publish_kwargs)
            return future.result()  # Wait for publish to complete
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        message_id = await loop.run_in_executor(None, _publish)
        
        logger.info(
            "Published message to Pub/Sub",
            message_id=message_id,
            topic_name=self.config.topic_name,
            data_size=len(message_data)
        )
        
        return message_id
    
    async def publish_messages_batch(
        self,
        messages: List[PubSubMessage]
    ) -> List[str]:
        """
        Publish multiple messages in batch.
        
        Args:
            messages: List of messages to publish
            
        Returns:
            List of message IDs
        """
        if self._is_available and self.publisher_client:
            try:
                return await self._publish_messages_batch_pubsub(messages)
            except Exception as e:
                logger.error(
                    "Failed to publish messages batch to Pub/Sub",
                    error=str(e),
                    batch_size=len(messages)
                )
                
                # Fall back to NATS if available
                if self.fallback_service:
                    logger.info("Falling back to NATS for batch publishing")
                    message_ids = []
                    for message in messages:
                        message_id = await self.fallback_service.publish_message(
                            self.config.topic_name, message.data
                        )
                        message_ids.append(message_id)
                    return message_ids
                raise
        
        # Use fallback service if Pub/Sub is not available
        if self.fallback_service:
            message_ids = []
            for message in messages:
                message_id = await self.fallback_service.publish_message(
                    self.config.topic_name, message.data
                )
                message_ids.append(message_id)
            return message_ids
        
        raise RuntimeError("No message publishing backend available")
    
    async def _publish_messages_batch_pubsub(
        self,
        messages: List[PubSubMessage]
    ) -> List[str]:
        """Publish messages batch to Pub/Sub."""
        if not self.publisher_client or not self.topic_path:
            raise RuntimeError("Pub/Sub publisher not initialized")
        
        def _publish_batch():
            futures = []
            
            for message in messages:
                message_data = json.dumps(message.data).encode('utf-8')
                message_attributes = message.attributes or {}
                
                publish_kwargs = {
                    "topic": self.topic_path,
                    "data": message_data,
                    "attributes": message_attributes,
                }
                
                if message.ordering_key and self.config.enable_message_ordering:
                    publish_kwargs["ordering_key"] = message.ordering_key
                
                future = self.publisher_client.publish(**publish_kwargs)
                futures.append(future)
            
            # Wait for all publishes to complete
            return [future.result() for future in futures]
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        message_ids = await loop.run_in_executor(None, _publish_batch)
        
        logger.info(
            "Published messages batch to Pub/Sub",
            batch_size=len(messages),
            topic_name=self.config.topic_name
        )
        
        return message_ids
    
    def register_message_handler(
        self,
        handler_name: str,
        handler_func: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a message handler function.
        
        Args:
            handler_name: Name of the handler
            handler_func: Handler function that processes messages
        """
        self._message_handlers[handler_name] = handler_func
        logger.info("Registered message handler", handler_name=handler_name)
    
    async def start_subscriber(self) -> None:
        """Start the message subscriber."""
        if self._is_available and self.subscriber_client:
            try:
                await self._start_subscriber_pubsub()
            except Exception as e:
                logger.error(
                    "Failed to start Pub/Sub subscriber",
                    error=str(e)
                )
                
                # Fall back to NATS if available
                if self.fallback_service:
                    logger.info("Falling back to NATS for message subscription")
                    await self._start_subscriber_nats()
                raise
        
        # Use fallback service if Pub/Sub is not available
        if self.fallback_service:
            await self._start_subscriber_nats()
        else:
            logger.warning("No message subscription backend available")
    
    async def _start_subscriber_pubsub(self) -> None:
        """Start Pub/Sub subscriber."""
        if not self.subscriber_client or not self.subscription_path:
            raise RuntimeError("Pub/Sub subscriber not initialized")
        
        def callback(message):
            """Process received message."""
            try:
                # Parse message data
                data = json.loads(message.data.decode('utf-8'))
                
                # Process with registered handlers
                for handler_name, handler_func in self._message_handlers.items():
                    try:
                        handler_func(data)
                    except Exception as e:
                        logger.error(
                            "Message handler failed",
                            handler_name=handler_name,
                            error=str(e),
                            message_id=message.message_id
                        )
                
                # Acknowledge message
                message.ack()
                
                logger.debug(
                    "Processed Pub/Sub message",
                    message_id=message.message_id,
                    handlers_count=len(self._message_handlers)
                )
                
            except Exception as e:
                logger.error(
                    "Failed to process Pub/Sub message",
                    error=str(e),
                    message_id=message.message_id
                )
                # Don't acknowledge failed messages
                message.nack()
        
        # Configure flow control
        flow_control = pubsub_v1.types.FlowControl(
            max_messages=self.config.max_messages
        )
        
        def _start_pulling():
            # Start pulling messages
            streaming_pull_future = self.subscriber_client.subscribe(
                self.subscription_path,
                callback=callback,
                flow_control=flow_control
            )
            
            logger.info(
                "Started Pub/Sub subscriber",
                subscription_name=self.config.subscription_name,
                max_messages=self.config.max_messages
            )
            
            try:
                # Keep the subscriber running
                streaming_pull_future.result()
            except KeyboardInterrupt:
                streaming_pull_future.cancel()
                logger.info("Pub/Sub subscriber stopped")
        
        # Run subscriber in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _start_pulling)
    
    async def _start_subscriber_nats(self) -> None:
        """Start NATS subscriber as fallback."""
        if not self.fallback_service:
            return
        
        async def message_handler(subject: str, data: Dict[str, Any]) -> None:
            """Handle NATS messages."""
            # Process with registered handlers
            for handler_name, handler_func in self._message_handlers.items():
                try:
                    handler_func(data)
                except Exception as e:
                    logger.error(
                        "Message handler failed",
                        handler_name=handler_name,
                        error=str(e),
                        subject=subject
                    )
        
        # Subscribe to NATS topic
        await self.fallback_service.subscribe_to_subject(
            self.config.topic_name, message_handler
        )
        
        logger.info(
            "Started NATS subscriber as fallback",
            topic_name=self.config.topic_name
        )
    
    async def stop_subscriber(self) -> None:
        """Stop the message subscriber."""
        if self._is_available and self.subscriber_client:
            # Pub/Sub subscriber cleanup is handled automatically
            logger.info("Stopped Pub/Sub subscriber")
        
        if self.fallback_service:
            # NATS cleanup is handled by the NATS service
            logger.info("Stopped NATS subscriber")
    
    def is_available(self) -> bool:
        """Check if Pub/Sub service is available."""
        return self._is_available
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status information."""
        return {
            "service": "Pub/Sub",
            "available": self._is_available,
            "config": {
                "project_id": self.config.project_id,
                "topic_name": self.config.topic_name,
                "subscription_name": self.config.subscription_name,
                "max_messages": self.config.max_messages,
                "ack_deadline_seconds": self.config.ack_deadline_seconds,
                "message_ordering": self.config.enable_message_ordering,
                "exactly_once_delivery": self.config.enable_exactly_once_delivery,
            },
            "fallback_enabled": self.fallback_service is not None,
            "handlers_registered": len(self._message_handlers),
        }
    
    async def get_subscription_info(self) -> Dict[str, Any]:
        """Get subscription information."""
        if not self._is_available or not self.subscriber_client or not self.subscription_path:
            return {"error": "Pub/Sub not available"}
        
        try:
            def _get_info():
                subscription = self.subscriber_client.get_subscription(
                    request={"subscription": self.subscription_path}
                )
                return {
                    "name": subscription.name,
                    "topic": subscription.topic,
                    "ack_deadline_seconds": subscription.ack_deadline_seconds,
                    "message_retention_duration": subscription.message_retention_duration.seconds,
                    "enable_message_ordering": subscription.enable_message_ordering,
                    "enable_exactly_once_delivery": subscription.enable_exactly_once_delivery,
                }
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _get_info)
            return info
            
        except Exception as e:
            logger.error("Failed to get subscription info", error=str(e))
            return {"error": str(e)}


# Global Pub/Sub service instance
_pubsub_service: Optional[PubSubService] = None


def get_pubsub_service(fallback_service: Optional[NATSService] = None) -> PubSubService:
    """Get or create Pub/Sub service instance."""
    global _pubsub_service
    
    if _pubsub_service is None:
        _pubsub_service = PubSubService(fallback_service=fallback_service)
    
    return _pubsub_service