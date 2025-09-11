"""
Webhook Integration API endpoints
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
class WebhookConfig(BaseModel):
    enabled: bool = False
    url: str = ""
    method: str = "POST"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    timeout: int = 30
    retry_count: int = 3
    verify_ssl: bool = True

class WebhookRequest(BaseModel):
    incident_id: str
    incident_data: Dict[str, Any]
    event_type: str = "incident"
    custom_payload: Optional[Dict[str, Any]] = None

class WebhookResponse(BaseModel):
    success: bool
    status_code: Optional[int] = None
    message: str
    details: Optional[Dict[str, Any]] = None

# In-memory storage for configuration (in production, use database)
webhook_config_storage = {
    "enabled": False,
    "url": "",
    "method": "POST",
    "headers": {"Content-Type": "application/json"},
    "timeout": 30,
    "retry_count": 3,
    "verify_ssl": True
}

@router.get("/config")
async def get_webhook_config():
    """Get current Webhook configuration"""
    return webhook_config_storage

@router.post("/config")
async def save_webhook_config(config: WebhookConfig):
    """Save Webhook configuration"""
    try:
        # Update the configuration
        webhook_config_storage.update(config.dict())
        
        # Log the configuration change for auditing
        logger.info(f"Webhook configuration updated: enabled={config.enabled}, url={config.url}")
        
        return {"success": True, "message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save Webhook configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@router.post("/test")
async def test_webhook_connection(config: WebhookConfig):
    """Test Webhook connection"""
    try:
        if not config.url:
            raise HTTPException(status_code=400, detail="Webhook URL is required")
        
        # Prepare test payload
        test_payload = {
            "event_type": "test",
            "timestamp": datetime.now().isoformat(),
            "message": "Test webhook from audit service",
            "incident_id": "test-webhook",
            "incident_data": {
                "test": True,
                "source": "audit-service"
            }
        }
        
        # Prepare headers
        headers = dict(config.headers)
        
        # Test the webhook
        async with httpx.AsyncClient(
            timeout=config.timeout,
            verify=config.verify_ssl
        ) as client:
            response = await client.request(
                method=config.method,
                url=config.url,
                json=test_payload,
                headers=headers
            )
            
            if response.status_code in [200, 201, 202, 204]:
                return {"success": True, "message": "Webhook connection successful"}
            else:
                return {"success": False, "message": f"Webhook test failed: {response.status_code}"}
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Webhook connection timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Unable to connect to webhook URL")
    except httpx.SSLError:
        raise HTTPException(status_code=400, detail="SSL verification failed")
    except Exception as e:
        logger.error(f"Webhook connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/send", response_model=WebhookResponse)
async def send_webhook(request: WebhookRequest):
    """Send data to webhook"""
    try:
        # Get current configuration
        config = webhook_config_storage
        if not config.get("enabled"):
            raise HTTPException(status_code=400, detail="Webhook integration is not enabled")
        
        if not config.get("url"):
            raise HTTPException(status_code=400, detail="Webhook configuration is incomplete")
        
        # Prepare webhook payload
        webhook_payload = {
            "event_type": request.event_type,
            "timestamp": datetime.now().isoformat(),
            "incident_id": request.incident_id,
            "incident_data": request.incident_data,
            "source": "audit-service"
        }
        
        # Add custom payload if provided
        if request.custom_payload:
            webhook_payload.update(request.custom_payload)
        
        # Prepare headers
        headers = dict(config["headers"])
        
        # Send webhook with retry logic
        last_exception = None
        for attempt in range(config["retry_count"] + 1):
            try:
                async with httpx.AsyncClient(
                    timeout=config["timeout"],
                    verify=config["verify_ssl"]
                ) as client:
                    response = await client.request(
                        method=config["method"],
                        url=config["url"],
                        json=webhook_payload,
                        headers=headers
                    )
                    
                    if response.status_code in [200, 201, 202, 204]:
                        return WebhookResponse(
                            success=True,
                            status_code=response.status_code,
                            message="Webhook sent successfully",
                            details={"response": response.text}
                        )
                    else:
                        last_exception = Exception(f"HTTP {response.status_code}: {response.text}")
                        
            except Exception as e:
                last_exception = e
                if attempt < config["retry_count"]:
                    logger.warning(f"Webhook attempt {attempt + 1} failed, retrying: {str(e)}")
                    continue
                else:
                    break
        
        # All retries failed
        return WebhookResponse(
            success=False,
            status_code=getattr(last_exception, 'response', {}).get('status_code') if hasattr(last_exception, 'response') else None,
            message=f"Webhook failed after {config['retry_count'] + 1} attempts: {str(last_exception)}",
            details={"error": str(last_exception)}
        )
                
    except Exception as e:
        logger.error(f"Webhook send failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook send failed: {str(e)}")

@router.post("/send-incident")
async def send_incident_webhook(request: WebhookRequest):
    """Send incident data to webhook (convenience endpoint)"""
    request.event_type = "incident"
    return await send_webhook(request)

@router.post("/send-alert")
async def send_alert_webhook(request: WebhookRequest):
    """Send alert data to webhook (convenience endpoint)"""
    request.event_type = "alert"
    return await send_webhook(request)

@router.get("/history")
async def get_webhook_history():
    """Get webhook execution history (placeholder)"""
    # In a real implementation, this would query a database
    return {
        "message": "Webhook history not implemented yet",
        "history": []
    }

@router.post("/validate-url")
async def validate_webhook_url(url: str):
    """Validate webhook URL format and accessibility"""
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
        
        # Test URL accessibility
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.head(url)
                return {
                    "valid": True,
                    "status_code": response.status_code,
                    "message": "URL is accessible"
                }
            except httpx.ConnectError:
                return {
                    "valid": False,
                    "message": "URL is not accessible"
                }
            except httpx.TimeoutException:
                return {
                    "valid": False,
                    "message": "URL connection timeout"
                }
                
    except Exception as e:
        logger.error(f"URL validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"URL validation failed: {str(e)}")
