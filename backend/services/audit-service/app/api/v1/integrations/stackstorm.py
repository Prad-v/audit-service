"""
StackStorm Integration API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import httpx
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class StackStormConfig(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    timeout: int = 30
    retry_count: int = 3
    ignore_ssl: bool = False

class StackStormActionRequest(BaseModel):
    incident_id: str
    incident_data: Dict[str, Any]
    pack_name: str
    action_name: str
    action_parameters: Optional[Dict[str, Any]] = {}

class StackStormActionResponse(BaseModel):
    success: bool
    execution_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None

class StackStormAlertRequest(BaseModel):
    alert_id: str
    alert_data: Dict[str, Any]
    pack_name: str
    action_name: str
    action_parameters: Optional[Dict[str, Any]] = {}

class StackStormAlertResponse(BaseModel):
    success: bool
    execution_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None

# In-memory storage for configuration (in production, use database)
stackstorm_config_storage = {
    "enabled": False,
    "base_url": "",
    "api_key": "",
    "timeout": 30,
    "retry_count": 3,
    "ignore_ssl": False
}

@router.get("/config")
async def get_stackstorm_config():
    """Get current StackStorm configuration"""
    return stackstorm_config_storage

@router.post("/config")
async def save_stackstorm_config(config: StackStormConfig):
    """Save StackStorm configuration"""
    try:
        # Update the configuration
        stackstorm_config_storage.update(config.dict())
        
        # Log the configuration change for auditing
        logger.info(f"StackStorm configuration updated: enabled={config.enabled}, base_url={config.base_url}")
        
        return {"success": True, "message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save StackStorm configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@router.post("/test")
async def test_stackstorm_connection(config: StackStormConfig):
    """Test StackStorm connection"""
    try:
        if not config.base_url or not config.api_key:
            raise HTTPException(status_code=400, detail="Base URL and API key are required")
        
        # Test connection by getting action list
        headers = {
            "X-Auth-Token": config.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=config.timeout, verify=not config.ignore_ssl) as client:
            response = await client.get(
                f"{config.base_url}/api/v1/actions",
                headers=headers
            )
            
            if response.status_code == 200:
                return {"success": True, "message": "StackStorm connection successful"}
            else:
                return {"success": False, "message": f"Connection failed: {response.status_code}"}
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Connection timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to StackStorm")
    except Exception as e:
        logger.error(f"StackStorm connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/execute-action", response_model=StackStormActionResponse)
async def execute_stackstorm_action(request: StackStormActionRequest):
    """Execute a StackStorm action for an incident"""
    try:
        # Get current configuration
        config = stackstorm_config_storage
        if not config.get("enabled"):
            raise HTTPException(status_code=400, detail="StackStorm integration is not enabled")
        
        if not config.get("base_url") or not config.get("api_key"):
            raise HTTPException(status_code=400, detail="StackStorm configuration is incomplete")
        
        # Prepare action execution payload
        action_payload = {
            "action": f"{request.pack_name}.{request.action_name}",
            "parameters": {
                "incident_id": request.incident_id,
                "incident_data": request.incident_data,
                **request.action_parameters
            }
        }
        
        headers = {
            "X-Auth-Token": config["api_key"],
            "Content-Type": "application/json"
        }
        
        # Execute the action
        async with httpx.AsyncClient(timeout=config["timeout"], verify=not config["ignore_ssl"]) as client:
            response = await client.post(
                f"{config['base_url']}/api/v1/executions",
                headers=headers,
                json=action_payload
            )
            
            if response.status_code == 201:
                result = response.json()
                return StackStormActionResponse(
                    success=True,
                    execution_id=result.get("id"),
                    message="StackStorm action executed successfully",
                    details=result
                )
            else:
                error_detail = response.text
                return StackStormActionResponse(
                    success=False,
                    message=f"Failed to execute action: {response.status_code}",
                    details={"error": error_detail}
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Action execution timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to StackStorm")
    except Exception as e:
        logger.error(f"StackStorm action execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Action execution failed: {str(e)}")

@router.get("/actions")
async def list_stackstorm_actions():
    """List available StackStorm actions"""
    try:
        config = stackstorm_config_storage
        if not config.get("enabled") or not config.get("base_url") or not config.get("api_key"):
            raise HTTPException(status_code=400, detail="StackStorm integration is not configured")
        
        headers = {
            "X-Auth-Token": config["api_key"],
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=config["timeout"], verify=not config["ignore_ssl"]) as client:
            response = await client.get(
                f"{config['base_url']}/api/v1/actions",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch actions")
                
    except Exception as e:
        logger.error(f"Failed to list StackStorm actions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list actions: {str(e)}")

@router.post("/send-alert", response_model=StackStormAlertResponse)
async def send_stackstorm_alert(request: StackStormAlertRequest):
    """Send alert to StackStorm as an alert provider"""
    try:
        # Get current configuration
        config = stackstorm_config_storage
        if not config.get("enabled"):
            raise HTTPException(status_code=400, detail="StackStorm integration is not enabled")
        
        if not config.get("base_url") or not config.get("api_key"):
            raise HTTPException(status_code=400, detail="StackStorm configuration is incomplete")
        
        # Prepare alert execution payload
        alert_payload = {
            "action": f"{request.pack_name}.{request.action_name}",
            "parameters": {
                "alert_id": request.alert_id,
                "alert_data": request.alert_data,
                **request.action_parameters
            }
        }
        
        headers = {
            "X-Auth-Token": config["api_key"],
            "Content-Type": "application/json"
        }
        
        # Execute the alert action
        async with httpx.AsyncClient(timeout=config["timeout"], verify=not config["ignore_ssl"]) as client:
            response = await client.post(
                f"{config['base_url']}/api/v1/executions",
                headers=headers,
                json=alert_payload
            )
            
            if response.status_code == 201:
                result = response.json()
                return StackStormAlertResponse(
                    success=True,
                    execution_id=result.get("id"),
                    message="StackStorm alert sent successfully",
                    details=result
                )
            else:
                error_detail = response.text
                return StackStormAlertResponse(
                    success=False,
                    message=f"Failed to send alert: {response.status_code}",
                    details={"error": error_detail}
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Alert sending timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to StackStorm")
    except Exception as e:
        logger.error(f"StackStorm alert sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Alert sending failed: {str(e)}")
