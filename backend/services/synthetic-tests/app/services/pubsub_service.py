"""
Pub/Sub Service for Synthetic Tests

This service handles publishing and receiving messages from Google Cloud Pub/Sub
for synthetic test scenarios.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    from google.cloud import pubsub_v1
    from google.cloud.pubsub_v1.subscriber.message import Message
except ImportError:
    # Mock for development
    class Message:
        def __init__(self, data: bytes, attributes: Dict[str, str], message_id: str):
            self.data = data
            self.attributes = attributes
            self.message_id = message_id

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PubSubMessage:
    """Represents a Pub/Sub message"""
    message_id: str
    data: bytes
    attributes: Dict[str, str]
    publish_time: Optional[datetime] = None


class PubSubService:
    """Service for interacting with Google Cloud Pub/Sub"""
    
    def __init__(self):
        self.project_id = settings.GOOGLE_CLOUD_PROJECT
        if not self.project_id:
            logger.warning("GOOGLE_CLOUD_PROJECT not set, using mock Pub/Sub service")
            self._mock_mode = True
        else:
            self._mock_mode = False
            try:
                self.publisher = pubsub_v1.PublisherClient()
                self.subscriber = pubsub_v1.SubscriberClient()
            except Exception as e:
                logger.warning(f"Failed to initialize Pub/Sub client: {e}, using mock mode")
                self._mock_mode = True
    
    async def publish_message(
        self,
        project_id: str,
        topic_name: str,
        message_data: str,
        attributes: Optional[Dict[str, str]] = None,
        ordering_key: Optional[str] = None
    ) -> str:
        """Publish a message to a Pub/Sub topic"""
        topic_path = f"projects/{project_id}/topics/{topic_name}"
        
        if self._mock_mode:
            return await self._mock_publish_message(topic_path, message_data, attributes)
        
        try:
            # Convert message data to bytes
            data = message_data.encode('utf-8')
            
            # Prepare attributes
            attrs = attributes or {}
            attrs['published_at'] = datetime.now(timezone.utc).isoformat()
            
            # Publish message
            future = self.publisher.publish(
                topic_path,
                data,
                **attrs,
                ordering_key=ordering_key
            )
            
            message_id = future.result()
            logger.info(f"Published message {message_id} to topic {topic_name}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to publish message to {topic_name}: {e}")
            raise
    
    async def receive_message(
        self,
        project_id: str,
        subscription_name: str,
        timeout_seconds: int = 30
    ) -> Optional[PubSubMessage]:
        """Receive a message from a Pub/Sub subscription"""
        subscription_path = f"projects/{project_id}/subscriptions/{subscription_name}"
        
        if self._mock_mode:
            return await self._mock_receive_message(subscription_path, timeout_seconds)
        
        try:
            # Use asyncio to handle the synchronous Pub/Sub client
            loop = asyncio.get_event_loop()
            
            def _receive():
                response = self.subscriber.pull(
                    request={"subscription": subscription_path, "max_messages": 1}
                )
                
                if not response.received_messages:
                    return None
                
                message = response.received_messages[0]
                
                # Acknowledge the message
                self.subscriber.acknowledge(
                    request={
                        "subscription": subscription_path,
                        "ack_ids": [message.ack_id]
                    }
                )
                
                return PubSubMessage(
                    message_id=message.message.message_id,
                    data=message.message.data,
                    attributes=dict(message.message.attributes),
                    publish_time=message.message.publish_time
                )
            
            # Run in thread pool to avoid blocking
            message = await loop.run_in_executor(None, _receive)
            
            if message:
                logger.info(f"Received message {message.message_id} from subscription {subscription_name}")
            
            return message
            
        except Exception as e:
            logger.error(f"Failed to receive message from {subscription_name}: {e}")
            raise
    
    async def create_topic(self, project_id: str, topic_name: str) -> bool:
        """Create a Pub/Sub topic"""
        topic_path = f"projects/{project_id}/topics/{topic_name}"
        
        if self._mock_mode:
            logger.info(f"Mock: Created topic {topic_name}")
            return True
        
        try:
            self.publisher.create_topic(request={"name": topic_path})
            logger.info(f"Created topic {topic_name}")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Topic {topic_name} already exists")
                return True
            logger.error(f"Failed to create topic {topic_name}: {e}")
            return False
    
    async def create_subscription(
        self,
        project_id: str,
        topic_name: str,
        subscription_name: str
    ) -> bool:
        """Create a Pub/Sub subscription"""
        topic_path = f"projects/{project_id}/topics/{topic_name}"
        subscription_path = f"projects/{project_id}/subscriptions/{subscription_name}"
        
        if self._mock_mode:
            logger.info(f"Mock: Created subscription {subscription_name}")
            return True
        
        try:
            self.subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path
                }
            )
            logger.info(f"Created subscription {subscription_name}")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Subscription {subscription_name} already exists")
                return True
            logger.error(f"Failed to create subscription {subscription_name}: {e}")
            return False
    
    async def _mock_publish_message(
        self,
        topic_path: str,
        message_data: str,
        attributes: Optional[Dict[str, str]]
    ) -> str:
        """Mock implementation for publishing messages"""
        message_id = f"mock-{datetime.now().timestamp()}"
        logger.info(f"Mock: Published message {message_id} to {topic_path}")
        
        # Store message in memory for mock consumption
        if not hasattr(self, '_mock_messages'):
            self._mock_messages = {}
        
        if topic_path not in self._mock_messages:
            self._mock_messages[topic_path] = []
        
        self._mock_messages[topic_path].append({
            'message_id': message_id,
            'data': message_data.encode('utf-8'),
            'attributes': attributes or {},
            'publish_time': datetime.now(timezone.utc)
        })
        
        return message_id
    
    async def _mock_receive_message(
        self,
        subscription_path: str,
        timeout_seconds: int
    ) -> Optional[PubSubMessage]:
        """Mock implementation for receiving messages"""
        if not hasattr(self, '_mock_messages'):
            self._mock_messages = {}
        
        # Find messages for this subscription
        # In a real implementation, you'd map subscriptions to topics
        topic_path = subscription_path.replace('/subscriptions/', '/topics/')
        
        if topic_path not in self._mock_messages or not self._mock_messages[topic_path]:
            # Wait for a message to arrive
            await asyncio.sleep(min(timeout_seconds, 1))
            return None
        
        # Return the first available message
        message_data = self._mock_messages[topic_path].pop(0)
        
        return PubSubMessage(
            message_id=message_data['message_id'],
            data=message_data['data'],
            attributes=message_data['attributes'],
            publish_time=message_data['publish_time']
        )
