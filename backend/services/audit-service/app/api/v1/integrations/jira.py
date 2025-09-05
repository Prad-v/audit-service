"""
Jira Integration API endpoints
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
class JiraConfig(BaseModel):
    enabled: bool = False
    instance_type: str = "cloud"  # "cloud" or "onprem"
    base_url: str = ""
    username: str = ""
    api_token: str = ""
    project_key: str = ""
    issue_type: str = "Bug"
    priority_mapping: Dict[str, str] = {
        "critical": "Highest",
        "high": "High", 
        "medium": "Medium",
        "low": "Low"
    }
    custom_fields: Dict[str, str] = {}

class JiraTicketRequest(BaseModel):
    incident_id: str
    incident_data: Dict[str, Any]

class JiraTicketResponse(BaseModel):
    jira_ticket_id: str
    jira_ticket_url: str
    success: bool = True

# In-memory storage for demo (in production, use database)
jira_config_storage = {
    "enabled": False,
    "instance_type": "cloud",
    "base_url": "",
    "username": "",
    "api_token": "",
    "project_key": "",
    "issue_type": "Bug",
    "priority_mapping": {
        "critical": "Highest",
        "high": "High",
        "medium": "Medium", 
        "low": "Low"
    },
    "custom_fields": {}
}

@router.get("/config")
async def get_jira_config():
    """Get current Jira configuration"""
    return jira_config_storage

@router.post("/config")
async def save_jira_config(config: JiraConfig):
    """Save Jira configuration"""
    try:
        # Update the configuration
        jira_config_storage.update(config.dict())
        
        # Log the configuration change for auditing
        logger.info(f"Jira configuration updated: enabled={config.enabled}, instance_type={config.instance_type}")
        
        return {"success": True, "message": "Configuration saved successfully"}
    except Exception as e:
        logger.error(f"Failed to save Jira configuration: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save configuration")

@router.post("/test")
async def test_jira_connection(config: JiraConfig):
    """Test Jira connection"""
    try:
        if not config.base_url or not config.username or not config.api_token:
            raise HTTPException(status_code=400, detail="Missing required configuration fields")
        
        # Test connection by making a simple API call
        auth = (config.username, config.api_token)
        url = f"{config.base_url}/rest/api/3/myself"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth, timeout=10.0)
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    "success": True,
                    "message": f"Connection successful! Connected as {user_info.get('displayName', 'Unknown User')}"
                }
            else:
                return {
                    "success": False,
                    "message": f"Connection failed with status {response.status_code}: {response.text}"
                }
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Connection timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=400, detail="Unable to connect to Jira instance")
    except Exception as e:
        logger.error(f"Jira connection test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/create-ticket", response_model=JiraTicketResponse)
async def create_jira_ticket(request: JiraTicketRequest):
    """Create a Jira ticket from an incident"""
    try:
        # Get current configuration
        config = jira_config_storage
        if not config.get("enabled"):
            raise HTTPException(status_code=400, detail="Jira integration is not enabled")
        
        if not config.get("base_url") or not config.get("username") or not config.get("api_token"):
            raise HTTPException(status_code=400, detail="Jira configuration is incomplete")
        
        # Prepare Jira ticket data
        incident = request.incident_data
        severity = incident.get("severity", "medium").lower()
        priority = config["priority_mapping"].get(severity, "Medium")
        
        # Create the Jira issue payload
        issue_data = {
            "fields": {
                "project": {"key": config["project_key"]},
                "summary": f"Incident: {incident.get('title', 'Untitled Incident')}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": incident.get("description", "No description provided")
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"\n\n**Public Message:** {incident.get('public_message', 'N/A')}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"\n**Internal Notes:** {incident.get('internal_notes', 'N/A')}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"\n**Affected Services:** {', '.join(incident.get('affected_services', []))}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"\n**Affected Regions:** {', '.join(incident.get('affected_regions', []))}"
                                }
                            ]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"\n**Tags:** {', '.join(incident.get('tags', []))}"
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": config["issue_type"]},
                "priority": {"name": priority},
                "labels": [
                    "incident",
                    f"severity-{severity}",
                    f"type-{incident.get('incident_type', 'unknown')}"
                ] + incident.get("tags", [])
            }
        }
        
        # Add custom fields if configured
        for field_id, field_value in config.get("custom_fields", {}).items():
            if field_value:
                issue_data["fields"][field_id] = field_value
        
        # Create the Jira ticket
        auth = (config["username"], config["api_token"])
        url = f"{config['base_url']}/rest/api/3/issue"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=issue_data,
                auth=auth,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            if response.status_code == 201:
                result = response.json()
                ticket_id = result["key"]
                ticket_url = f"{config['base_url']}/browse/{ticket_id}"
                
                # Log the ticket creation for auditing
                logger.info(f"Jira ticket created: {ticket_id} for incident {request.incident_id}")
                
                return JiraTicketResponse(
                    jira_ticket_id=ticket_id,
                    jira_ticket_url=ticket_url
                )
            else:
                error_detail = response.text
                logger.error(f"Failed to create Jira ticket: {response.status_code} - {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to create Jira ticket: {error_detail}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout while creating Jira ticket")
    except httpx.ConnectError:
        raise HTTPException(status_code=400, detail="Unable to connect to Jira instance")
    except Exception as e:
        logger.error(f"Failed to create Jira ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Jira ticket: {str(e)}")

@router.get("/projects")
async def get_jira_projects():
    """Get available Jira projects (for configuration)"""
    try:
        config = jira_config_storage
        if not config.get("enabled") or not config.get("base_url"):
            raise HTTPException(status_code=400, detail="Jira integration is not configured")
        
        auth = (config["username"], config["api_token"])
        url = f"{config['base_url']}/rest/api/3/project"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth, timeout=10.0)
            
            if response.status_code == 200:
                projects = response.json()
                return {
                    "projects": [
                        {
                            "key": project["key"],
                            "name": project["name"],
                            "projectTypeKey": project["projectTypeKey"]
                        }
                        for project in projects
                    ]
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch projects: {response.text}"
                )
                
    except Exception as e:
        logger.error(f"Failed to fetch Jira projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch projects: {str(e)}")

@router.get("/issue-types")
async def get_jira_issue_types():
    """Get available issue types for the configured project"""
    try:
        config = jira_config_storage
        if not config.get("enabled") or not config.get("project_key"):
            raise HTTPException(status_code=400, detail="Jira integration is not configured")
        
        auth = (config["username"], config["api_token"])
        url = f"{config['base_url']}/rest/api/3/project/{config['project_key']}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, auth=auth, timeout=10.0)
            
            if response.status_code == 200:
                project_data = response.json()
                return {
                    "issue_types": [
                        {
                            "id": issue_type["id"],
                            "name": issue_type["name"],
                            "description": issue_type.get("description", "")
                        }
                        for issue_type in project_data.get("issueTypes", [])
                    ]
                }
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch issue types: {response.text}"
                )
                
    except Exception as e:
        logger.error(f"Failed to fetch Jira issue types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch issue types: {str(e)}")
