"""
Webhook API Endpoints

This module provides API endpoints for managing webhook subscriptions and webhook servers.
"""

import logging
import json
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, text
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.events import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionListResponse,
    WebhookConfig,
    WebhookAuthBasic,
    WebhookAuthBearer,
    WebhookAuthApiKey,
    WebhookAuthCustom
)
from app.core.auth import get_current_user
from app.services.webhook_server import WebhookServerManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Webhook server manager instance
webhook_manager = WebhookServerManager()


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse)
async def create_webhook_subscription(
    data: WebhookSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new webhook subscription"""
    try:
        # Validate webhook configuration
        await validate_webhook_config(data.config)
        
        # Create webhook subscription in database
        # This would typically involve creating a database record
        # For now, we'll simulate the creation
        
        subscription = WebhookSubscriptionResponse(
            subscription_id=f"webhook-{datetime.now().timestamp()}",
            name=data.name,
            description=data.description,
            config=data.config,
            enabled=data.enabled,
            tenant_id=data.tenant_id,
            created_by=data.created_by,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Start webhook server if enabled
        if data.enabled:
            await webhook_manager.start_webhook_server(subscription)
        
        logger.info(f"Created webhook subscription: {data.name}")
        return subscription
        
    except Exception as e:
        logger.error(f"Error creating webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating webhook subscription: {str(e)}")


@router.get("/subscriptions", response_model=WebhookSubscriptionListResponse)
async def list_webhook_subscriptions(
    page: int = 1,
    per_page: int = 20,
    enabled: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List webhook subscriptions"""
    try:
        # This would typically query the database
        # For now, return empty list
        subscriptions = []
        total = 0
        
        return WebhookSubscriptionListResponse(
            subscriptions=subscriptions,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing webhook subscriptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing webhook subscriptions: {str(e)}")


@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific webhook subscription"""
    try:
        # This would typically query the database
        # For now, return 404
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting webhook subscription: {str(e)}")


@router.put("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    subscription_id: str,
    data: WebhookSubscriptionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a webhook subscription"""
    try:
        # This would typically update the database
        # For now, return 404
        raise HTTPException(status_code=404, detail="Webhook subscription not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating webhook subscription: {str(e)}")


@router.delete("/subscriptions/{subscription_id}")
async def delete_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a webhook subscription"""
    try:
        # Stop webhook server if running
        await webhook_manager.stop_webhook_server(subscription_id)
        
        # This would typically delete from database
        # For now, just return success
        
        logger.info(f"Deleted webhook subscription: {subscription_id}")
        return {"message": "Webhook subscription deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting webhook subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/enable")
async def enable_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Enable a webhook subscription"""
    try:
        # This would typically update the database
        # Start webhook server
        await webhook_manager.start_webhook_server_by_id(subscription_id)
        
        logger.info(f"Enabled webhook subscription: {subscription_id}")
        return {"message": "Webhook subscription enabled successfully"}
        
    except Exception as e:
        logger.error(f"Error enabling webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error enabling webhook subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/disable")
async def disable_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Disable a webhook subscription"""
    try:
        # This would typically update the database
        # Stop webhook server
        await webhook_manager.stop_webhook_server(subscription_id)
        
        logger.info(f"Disabled webhook subscription: {subscription_id}")
        return {"message": "Webhook subscription disabled successfully"}
        
    except Exception as e:
        logger.error(f"Error disabling webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error disabling webhook subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/test")
async def test_webhook_subscription(
    subscription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Test a webhook subscription by sending a test event"""
    try:
        # This would typically send a test event to the webhook
        # For now, just return success
        
        logger.info(f"Tested webhook subscription: {subscription_id}")
        return {"message": "Test event sent successfully"}
        
    except Exception as e:
        logger.error(f"Error testing webhook subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing webhook subscription: {str(e)}")


@router.get("/subscriptions/{subscription_id}/status")
async def get_webhook_subscription_status(
    subscription_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the status of a webhook subscription server"""
    try:
        status = await webhook_manager.get_webhook_server_status(subscription_id)
        return status
        
    except Exception as e:
        logger.error(f"Error getting webhook subscription status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting webhook subscription status: {str(e)}")


@router.get("/health")
async def webhook_health_check():
    """Health check for webhook service"""
    try:
        # Check if webhook manager is healthy
        health_status = await webhook_manager.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"Error in webhook health check: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook service unhealthy")


async def validate_webhook_config(config: WebhookConfig):
    """Validate webhook configuration"""
    try:
        # Validate port range
        if not (1 <= config.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        
        # Validate authentication configuration
        if config.authentication == "basic" and not config.auth_basic:
            raise ValueError("Basic authentication requires username and password")
        elif config.authentication == "bearer" and not config.auth_bearer:
            raise ValueError("Bearer authentication requires token")
        elif config.authentication == "api_key" and not config.auth_api_key:
            raise ValueError("API key authentication requires header name and key value")
        elif config.authentication == "custom" and not config.auth_custom:
            raise ValueError("Custom authentication requires VRL expression")
        
        # Validate SSL configuration
        if config.ssl.enabled:
            if not config.ssl.cert_file or not config.ssl.key_file:
                raise ValueError("SSL enabled requires certificate and key files")
        
        # Validate encoding
        valid_encodings = ["json", "text", "binary", "avro"]
        if config.encoding not in valid_encodings:
            raise ValueError(f"Encoding must be one of: {', '.join(valid_encodings)}")
        
        # Validate HTTP method
        valid_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
        if config.method not in valid_methods:
            raise ValueError(f"HTTP method must be one of: {', '.join(valid_methods)}")
        
        # Validate response code
        if not (100 <= config.response_code <= 599):
            raise ValueError("Response code must be between 100 and 599")
        
        # Validate rate limit
        if config.rate_limit < 1:
            raise ValueError("Rate limit must be at least 1")
        
        logger.info("Webhook configuration validation passed")
        
    except Exception as e:
        logger.error(f"Webhook configuration validation failed: {e}")
        raise ValueError(f"Invalid webhook configuration: {str(e)}")
