"""
Pub/Sub Subscriptions API Endpoints

This module contains FastAPI endpoints for managing Google Cloud Pub/Sub subscriptions
with support for service account encryption and workload identity.
"""

import logging
import json
from typing import List, Optional
from datetime import datetime
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import PubSubSubscription
from app.models.events import (
    PubSubSubscriptionCreate, PubSubSubscriptionUpdate, 
    PubSubSubscriptionResponse, PubSubSubscriptionListResponse
)
from app.core.database import get_db
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize encryption key (in production, this should come from secure environment)
ENCRYPTION_KEY = Fernet.generate_key()
cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_service_account_key(key_data: str) -> str:
    """Encrypt service account key data"""
    try:
        encrypted_data = cipher_suite.encrypt(key_data.encode())
        return encrypted_data.decode()
    except Exception as e:
        logger.error(f"Failed to encrypt service account key: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt service account key")


def decrypt_service_account_key(encrypted_data: str) -> str:
    """Decrypt service account key data"""
    try:
        decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Failed to decrypt service account key: {e}")
        raise HTTPException(status_code=500, detail="Failed to decrypt service account key")


@router.post("/subscriptions", response_model=PubSubSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_pubsub_subscription(
    subscription_data: PubSubSubscriptionCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new Pub/Sub subscription"""
    try:
        # Generate subscription ID
        subscription_id = f"pubsub-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user[:8]}"
        
        # Encrypt service account key if provided
        config = subscription_data.config.dict()
        if config.get('service_account_key'):
            config['service_account_key'] = encrypt_service_account_key(config['service_account_key'])
        
        # Create subscription
        subscription = PubSubSubscription(
            subscription_id=subscription_id,
            name=subscription_data.name,
            description=subscription_data.description,
            config=config,
            enabled=subscription_data.enabled,
            tenant_id=subscription_data.tenant_id,
            created_by=current_user
        )
        
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        
        return PubSubSubscriptionResponse.from_orm(subscription)
        
    except Exception as e:
        logger.error(f"Error creating Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating Pub/Sub subscription: {str(e)}")


@router.get("/subscriptions", response_model=PubSubSubscriptionListResponse)
async def list_pubsub_subscriptions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    enabled: Optional[bool] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List Pub/Sub subscriptions"""
    try:
        # Build query
        query = select(PubSubSubscription).where(PubSubSubscription.tenant_id == "default")
        
        if enabled is not None:
            query = query.where(PubSubSubscription.enabled == enabled)
        
        # Get total count
        count_query = select(func.count(PubSubSubscription.subscription_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        subscriptions = result.scalars().all()
        
        return PubSubSubscriptionListResponse(
            subscriptions=[PubSubSubscriptionResponse.from_orm(sub) for sub in subscriptions],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing Pub/Sub subscriptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing Pub/Sub subscriptions: {str(e)}")


@router.get("/subscriptions/{subscription_id}", response_model=PubSubSubscriptionResponse)
async def get_pubsub_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific Pub/Sub subscription"""
    try:
        query = select(PubSubSubscription).where(
            PubSubSubscription.subscription_id == subscription_id,
            PubSubSubscription.tenant_id == "default"
        )
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Pub/Sub subscription not found")
        
        return PubSubSubscriptionResponse.from_orm(subscription)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting Pub/Sub subscription: {str(e)}")


@router.put("/subscriptions/{subscription_id}", response_model=PubSubSubscriptionResponse)
async def update_pubsub_subscription(
    subscription_id: str,
    subscription_data: PubSubSubscriptionUpdate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a Pub/Sub subscription"""
    try:
        query = select(PubSubSubscription).where(
            PubSubSubscription.subscription_id == subscription_id,
            PubSubSubscription.tenant_id == "default"
        )
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Pub/Sub subscription not found")
        
        # Update fields
        if subscription_data.name is not None:
            subscription.name = subscription_data.name
        if subscription_data.description is not None:
            subscription.description = subscription_data.description
        if subscription_data.enabled is not None:
            subscription.enabled = subscription_data.enabled
        if subscription_data.config is not None:
            # Encrypt service account key if provided
            config = subscription_data.config.dict()
            if config.get('service_account_key'):
                config['service_account_key'] = encrypt_service_account_key(config['service_account_key'])
            subscription.config = config
        
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(subscription)
        
        return PubSubSubscriptionResponse.from_orm(subscription)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating Pub/Sub subscription: {str(e)}")


@router.delete("/subscriptions/{subscription_id}")
async def delete_pubsub_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a Pub/Sub subscription"""
    try:
        query = select(PubSubSubscription).where(
            PubSubSubscription.subscription_id == subscription_id,
            PubSubSubscription.tenant_id == "default"
        )
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Pub/Sub subscription not found")
        
        await db.delete(subscription)
        await db.commit()
        
        return {"message": "Pub/Sub subscription deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting Pub/Sub subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/test")
async def test_pubsub_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test a Pub/Sub subscription connection"""
    try:
        query = select(PubSubSubscription).where(
            PubSubSubscription.subscription_id == subscription_id,
            PubSubSubscription.tenant_id == "default"
        )
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Pub/Sub subscription not found")
        
        config = subscription.config
        
        # Test connection based on authentication method
        if config.get('authentication_method') == 'service_account':
            if not config.get('service_account_key'):
                raise HTTPException(status_code=400, detail="Service account key is required for service account authentication")
            
            # Decrypt and validate service account key
            try:
                service_account_data = decrypt_service_account_key(config['service_account_key'])
                service_account_json = json.loads(service_account_data)
                
                # Basic validation
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                for field in required_fields:
                    if field not in service_account_json:
                        raise ValueError(f"Missing required field: {field}")
                
                return {
                    "status": "success",
                    "message": "Service account key is valid",
                    "project_id": service_account_json.get('project_id'),
                    "client_email": service_account_json.get('client_email')
                }
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid service account key: {str(e)}")
        
        elif config.get('authentication_method') == 'workload_identity':
            workload_identity = config.get('workload_identity', {})
            if not workload_identity.get('enabled'):
                raise HTTPException(status_code=400, detail="Workload identity is not enabled")
            
            if not workload_identity.get('service_account'):
                raise HTTPException(status_code=400, detail="Service account email is required for workload identity")
            
            return {
                "status": "success",
                "message": "Workload identity configuration is valid",
                "service_account": workload_identity.get('service_account'),
                "audience": workload_identity.get('audience')
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid authentication method")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing Pub/Sub subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/enable")
async def enable_pubsub_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enable a Pub/Sub subscription"""
    try:
        query = select(PubSubSubscription).where(
            PubSubSubscription.subscription_id == subscription_id,
            PubSubSubscription.tenant_id == "default"
        )
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Pub/Sub subscription not found")
        
        subscription.enabled = True
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Pub/Sub subscription enabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error enabling Pub/Sub subscription: {str(e)}")


@router.post("/subscriptions/{subscription_id}/disable")
async def disable_pubsub_subscription(
    subscription_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disable a Pub/Sub subscription"""
    try:
        query = select(PubSubSubscription).where(
            PubSubSubscription.subscription_id == subscription_id,
            PubSubSubscription.tenant_id == "default"
        )
        
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Pub/Sub subscription not found")
        
        subscription.enabled = False
        subscription.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return {"message": "Pub/Sub subscription disabled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling Pub/Sub subscription: {e}")
        raise HTTPException(status_code=500, detail=f"Error disabling Pub/Sub subscription: {str(e)}")
