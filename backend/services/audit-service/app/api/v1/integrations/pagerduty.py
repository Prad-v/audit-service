"""
PagerDuty Integration API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class PagerDutyConfig(BaseModel):
    enabled: bool = False
    integration_key: str = ""
    service_id: str = ""
    escalation_policy_id: str = ""
    severity_mapping: Dict[str, str] = {
        "critical": "critical",
        "high": "error",
        "medium": "warning",
        "low": "info"
    }

class PagerDutyIncidentRequest(BaseModel):
    incident_id: str
    incident_data: Dict[str, Any]
    severity: str = "medium"
    summary: str = ""
    source: str = "audit-service"

class PagerDutyIncidentResponse(BaseModel):
    success: bool
    incident_key: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None

# In-memory storage for configuration (in production, use database)
pagerduty_config_storage = {
    "enabled": False,
    "integration_key": "",
    "service_id": "",
    "escalation_policy_id": "",
    "severity_mapping": {
        "critical": "critical",
        "high": "error",
        "medium": "warning",
        "low": "info"
    }
}

@router.get("/config")
async def get_pagerduty_config():
    """Get current PagerDuty configuration"""
    return pagerduty_config_storage

@router.post("/config")
async def save_pagerduty_config(config: PagerDutyConfig):
    """Save PagerDuty configuration"""
    try:
        # Update the configuration
        pagerduty_config_storage.update(config.dict())
        
        # Log the configuration change for auditing
        logger.info(f"PagerDuty configuration updated: enabled={config.enabled}, service_id={config.service_id}")
        
        return {"success": True, "message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save PagerDuty configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@router.post("/test")
async def test_pagerduty_connection(config: PagerDutyConfig):
    """Test PagerDuty connection"""
    try:
        if not config.integration_key:
            raise HTTPException(status_code=400, detail="Integration key is required")
        
        # Test connection by creating a test incident
        test_payload = {
            "routing_key": config.integration_key,
            "event_action": "trigger",
            "dedup_key": f"test-{datetime.now().isoformat()}",
            "payload": {
                "summary": "Test incident from audit service",
                "source": "audit-service-test",
                "severity": "info",
                "timestamp": datetime.now().isoformat(),
                "component": "integration-test",
                "group": "test",
                "class": "test"
            }
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=test_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 202:
                return {"success": True, "message": "PagerDuty connection successful"}
            else:
                return {"success": False, "message": f"Connection failed: {response.status_code}"}
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Connection timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to PagerDuty")
    except Exception as e:
        logger.error(f"PagerDuty connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/create-incident", response_model=PagerDutyIncidentResponse)
async def create_pagerduty_incident(request: PagerDutyIncidentRequest):
    """Create a PagerDuty incident from an alert"""
    try:
        # Get current configuration
        config = pagerduty_config_storage
        if not config.get("enabled"):
            raise HTTPException(status_code=400, detail="PagerDuty integration is not enabled")
        
        if not config.get("integration_key"):
            raise HTTPException(status_code=400, detail="PagerDuty configuration is incomplete")
        
        # Map severity to PagerDuty severity
        severity = request.severity.lower()
        pagerduty_severity = config["severity_mapping"].get(severity, "warning")
        
        # Prepare incident payload
        incident_payload = {
            "routing_key": config["integration_key"],
            "event_action": "trigger",
            "dedup_key": f"audit-{request.incident_id}",
            "payload": {
                "summary": request.summary or f"Incident {request.incident_id}",
                "source": request.source,
                "severity": pagerduty_severity,
                "timestamp": datetime.now().isoformat(),
                "component": request.incident_data.get("component", "audit-service"),
                "group": request.incident_data.get("group", "incidents"),
                "class": request.incident_data.get("class", "incident"),
                "custom_details": {
                    "incident_id": request.incident_id,
                    "incident_data": request.incident_data,
                    "original_severity": severity
                }
            }
        }
        
        # Create the incident
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=incident_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 202:
                result = response.json()
                return PagerDutyIncidentResponse(
                    success=True,
                    incident_key=result.get("dedup_key"),
                    message="PagerDuty incident created successfully",
                    details=result
                )
            else:
                error_detail = response.text
                return PagerDutyIncidentResponse(
                    success=False,
                    message=f"Failed to create incident: {response.status_code}",
                    details={"error": error_detail}
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Incident creation timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to PagerDuty")
    except Exception as e:
        logger.error(f"PagerDuty incident creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Incident creation failed: {str(e)}")

@router.post("/resolve-incident")
async def resolve_pagerduty_incident(incident_id: str):
    """Resolve a PagerDuty incident"""
    try:
        config = pagerduty_config_storage
        if not config.get("enabled") or not config.get("integration_key"):
            raise HTTPException(status_code=400, detail="PagerDuty integration is not configured")
        
        # Prepare resolve payload
        resolve_payload = {
            "routing_key": config["integration_key"],
            "event_action": "resolve",
            "dedup_key": f"audit-{incident_id}",
            "payload": {
                "summary": f"Incident {incident_id} resolved",
                "source": "audit-service",
                "severity": "info",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=resolve_payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 202:
                return {"success": True, "message": "Incident resolved successfully"}
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to resolve incident")
                
    except Exception as e:
        logger.error(f"Failed to resolve PagerDuty incident: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve incident: {str(e)}")

@router.get("/services")
async def list_pagerduty_services():
    """List PagerDuty services (requires API token)"""
    try:
        config = pagerduty_config_storage
        if not config.get("enabled"):
            raise HTTPException(status_code=400, detail="PagerDuty integration is not enabled")
        
        # Note: This would require a PagerDuty API token, not just integration key
        # For now, return a placeholder response
        return {
            "message": "Service listing requires PagerDuty API token configuration",
            "services": []
        }
        
    except Exception as e:
        logger.error(f"Failed to list PagerDuty services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list services: {str(e)}")
