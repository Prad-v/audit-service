"""
Alerting API Endpoints for Events Service

This module contains FastAPI endpoints for managing alert policies, providers, and alerts for cloud events.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.schemas import AlertPolicy, AlertProvider, Alert, AlertThrottle, AlertSuppression
from app.models.events import (
    AlertPolicyCreate, AlertPolicyUpdate, AlertPolicyResponse, AlertPolicyListResponse,
    AlertProviderCreate, AlertProviderUpdate, AlertProviderResponse, AlertProviderListResponse,
    AlertResponse, AlertListResponse, AlertSeverity, AlertStatus, AlertProviderType
)
from app.core.database import get_db
from app.core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


# Alert Policies Endpoints
@router.post("/policies", response_model=AlertPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_policy(
    policy_data: AlertPolicyCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert policy"""
    try:
        # Generate policy ID
        policy_id = f"policy-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user[:8]}"
        
        # Create policy
        policy = AlertPolicy(
            policy_id=policy_id,
            name=policy_data.name,
            description=policy_data.description,
            enabled=policy_data.enabled,
            rules=[rule.dict() for rule in policy_data.rules],
            match_all=policy_data.match_all,
            severity=policy_data.severity,
            message_template=policy_data.message_template,
            summary_template=policy_data.summary_template,
            time_window=policy_data.time_window.dict() if policy_data.time_window else None,
            throttle_minutes=policy_data.throttle_minutes,
            max_alerts_per_hour=policy_data.max_alerts_per_hour,
            providers=policy_data.providers,
            tenant_id="default",  # TODO: Get from user context
            created_by=current_user
        )
        
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
        
        return AlertPolicyResponse.from_orm(policy)
        
    except Exception as e:
        logger.error(f"Error creating alert policy: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating alert policy: {str(e)}")


@router.get("/policies", response_model=AlertPolicyListResponse)
async def list_alert_policies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    enabled: Optional[bool] = None,
    severity: Optional[AlertSeverity] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List alert policies"""
    try:
        # Build query
        query = select(AlertPolicy).where(AlertPolicy.tenant_id == "default")
        
        if enabled is not None:
            query = query.where(AlertPolicy.enabled == enabled)
        if severity:
            query = query.where(AlertPolicy.severity == severity)
        
        # Get total count
        count_query = select(func.count(AlertPolicy.policy_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        policies = result.scalars().all()
        
        return AlertPolicyListResponse(
            policies=[AlertPolicyResponse.from_orm(policy) for policy in policies],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing alert policies: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing alert policies: {str(e)}")


@router.get("/policies/{policy_id}", response_model=AlertPolicyResponse)
async def get_alert_policy(
    policy_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert policy"""
    try:
        result = await db.execute(
            select(AlertPolicy).where(
                and_(
                    AlertPolicy.policy_id == policy_id,
                    AlertPolicy.tenant_id == "default"
                )
            )
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Alert policy not found")
        
        return AlertPolicyResponse.from_orm(policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert policy: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting alert policy: {str(e)}")


@router.put("/policies/{policy_id}", response_model=AlertPolicyResponse)
async def update_alert_policy(
    policy_id: str,
    policy_data: AlertPolicyUpdate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an alert policy"""
    try:
        result = await db.execute(
            select(AlertPolicy).where(
                and_(
                    AlertPolicy.policy_id == policy_id,
                    AlertPolicy.tenant_id == "default"
                )
            )
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Alert policy not found")
        
        # Update fields
        update_data = policy_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == "time_window" and value:
                setattr(policy, field, value.dict())
            elif field == "rules" and value:
                setattr(policy, field, [rule.dict() for rule in value])
            else:
                setattr(policy, field, value)
        
        policy.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(policy)
        
        return AlertPolicyResponse.from_orm(policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert policy: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating alert policy: {str(e)}")


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_policy(
    policy_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert policy"""
    try:
        result = await db.execute(
            select(AlertPolicy).where(
                and_(
                    AlertPolicy.policy_id == policy_id,
                    AlertPolicy.tenant_id == "default"
                )
            )
        )
        policy = result.scalar_one_or_none()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Alert policy not found")
        
        await db.delete(policy)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert policy: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting alert policy: {str(e)}")


# Alert Providers Endpoints
@router.post("/providers", response_model=AlertProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_alert_provider(
    provider_data: AlertProviderCreate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert provider"""
    try:
        # Generate provider ID
        provider_id = f"{provider_data.provider_type.value}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{current_user[:8]}"
        
        # Create provider
        provider = AlertProvider(
            provider_id=provider_id,
            name=provider_data.name,
            provider_type=provider_data.provider_type,
            enabled=provider_data.enabled,
            config=provider_data.config,
            tenant_id="default",  # TODO: Get from user context
            created_by=current_user
        )
        
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
        
        return AlertProviderResponse.from_orm(provider)
        
    except Exception as e:
        logger.error(f"Error creating alert provider: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating alert provider: {str(e)}")


@router.get("/providers", response_model=AlertProviderListResponse)
async def list_alert_providers(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    provider_type: Optional[AlertProviderType] = None,
    enabled: Optional[bool] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List alert providers"""
    try:
        # Build query
        query = select(AlertProvider).where(AlertProvider.tenant_id == "default")
        
        if provider_type:
            query = query.where(AlertProvider.provider_type == provider_type)
        if enabled is not None:
            query = query.where(AlertProvider.enabled == enabled)
        
        # Get total count
        count_query = select(func.count(AlertProvider.provider_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        providers = result.scalars().all()
        
        return AlertProviderListResponse(
            providers=[AlertProviderResponse.from_orm(provider) for provider in providers],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing alert providers: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing alert providers: {str(e)}")


@router.get("/providers/{provider_id}", response_model=AlertProviderResponse)
async def get_alert_provider(
    provider_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert provider"""
    try:
        result = await db.execute(
            select(AlertProvider).where(
                and_(
                    AlertProvider.provider_id == provider_id,
                    AlertProvider.tenant_id == "default"
                )
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Alert provider not found")
        
        return AlertProviderResponse.from_orm(provider)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert provider: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting alert provider: {str(e)}")


@router.put("/providers/{provider_id}", response_model=AlertProviderResponse)
async def update_alert_provider(
    provider_id: str,
    provider_data: AlertProviderUpdate,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an alert provider"""
    try:
        result = await db.execute(
            select(AlertProvider).where(
                and_(
                    AlertProvider.provider_id == provider_id,
                    AlertProvider.tenant_id == "default"
                )
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Alert provider not found")
        
        # Update fields
        update_data = provider_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(provider, field, value)
        
        provider.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(provider)
        
        return AlertProviderResponse.from_orm(provider)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert provider: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating alert provider: {str(e)}")


@router.delete("/providers/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert_provider(
    provider_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert provider"""
    try:
        result = await db.execute(
            select(AlertProvider).where(
                and_(
                    AlertProvider.provider_id == provider_id,
                    AlertProvider.tenant_id == "default"
                )
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Alert provider not found")
        
        await db.delete(provider)
        await db.commit()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert provider: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting alert provider: {str(e)}")


# Alerts Endpoints
@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    policy_id: Optional[str] = None,
    event_id: Optional[str] = None,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List alerts"""
    try:
        # Build query
        query = select(Alert).where(Alert.tenant_id == "default")
        
        if policy_id:
            query = query.where(Alert.policy_id == policy_id)
        if event_id:
            query = query.where(Alert.event_id == event_id)
        if severity:
            query = query.where(Alert.severity == severity)
        if status:
            query = query.where(Alert.status == status)
        
        # Order by triggered_at desc
        query = query.order_by(Alert.triggered_at.desc())
        
        # Get total count
        count_query = select(func.count(Alert.alert_id)).select_from(query.subquery())
        total = await db.scalar(count_query)
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)
        
        result = await db.execute(query)
        alerts = result.scalars().all()
        
        return AlertListResponse(
            alerts=[AlertResponse.from_orm(alert) for alert in alerts],
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing alerts: {str(e)}")


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert"""
    try:
        result = await db.execute(
            select(Alert).where(
                and_(
                    Alert.alert_id == alert_id,
                    Alert.tenant_id == "default"
                )
            )
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse.from_orm(alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting alert: {str(e)}")


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert"""
    try:
        result = await db.execute(
            select(Alert).where(
                and_(
                    Alert.alert_id == alert_id,
                    Alert.tenant_id == "default"
                )
            )
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = current_user
        alert.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(alert)
        
        return AlertResponse.from_orm(alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=f"Error acknowledging alert: {str(e)}")


@router.put("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert"""
    try:
        result = await db.execute(
            select(Alert).where(
                and_(
                    Alert.alert_id == alert_id,
                    Alert.tenant_id == "default"
                )
            )
        )
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(alert)
        
        return AlertResponse.from_orm(alert)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")


# Event Processing Endpoint
@router.post("/process-event", status_code=status.HTTP_200_OK)
async def process_event(
    event_data: Dict[str, Any],
    tenant_id: str = Query("default", description="Tenant ID"),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process an event and trigger alerts based on policies"""
    try:
        from app.services.alert_engine import AlertEngine
        
        # Create alert engine
        alert_engine = AlertEngine(db)
        
        # Process event
        triggered_alerts = await alert_engine.process_event(event_data, tenant_id)
        
        return {
            "success": True,
            "message": f"Event processed, {len(triggered_alerts)} alerts triggered",
            "triggered_alerts": triggered_alerts
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing event: {str(e)}")


# Test Provider Endpoint
@router.post("/providers/{provider_id}/test")
async def test_alert_provider(
    provider_id: str,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Test an alert provider by sending a test alert"""
    try:
        result = await db.execute(
            select(AlertProvider).where(
                and_(
                    AlertProvider.provider_id == provider_id,
                    AlertProvider.tenant_id == "default"
                )
            )
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            raise HTTPException(status_code=404, detail="Alert provider not found")
        
        # Create test alert data
        test_alert = {
            "title": "Test Alert",
            "message": "This is a test alert to verify provider configuration",
            "summary": "Test alert for provider verification",
            "severity": "info",
            "event_data": {
                "test": True,
                "provider_id": provider_id
            }
        }
        
        # Send test alert
        from app.services.alert_providers import create_provider
        alert_provider = create_provider(provider.provider_type, provider.config)
        
        try:
            result = await alert_provider.send_alert(test_alert)
            return {
                "success": True,
                "message": "Test alert sent successfully",
                "provider_id": provider_id,
                "provider_type": provider.provider_type.value,
                "result": result
            }
        except Exception as send_error:
            return {
                "success": False,
                "message": f"Failed to send test alert: {str(send_error)}",
                "provider_id": provider_id,
                "provider_type": provider.provider_type.value,
                "error": str(send_error)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing alert provider: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing alert provider: {str(e)}")
