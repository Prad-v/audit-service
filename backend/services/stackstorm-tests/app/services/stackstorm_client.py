"""
StackStorm API Client for Synthetic Tests

This service handles communication with StackStorm API for test management,
execution, and monitoring.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StackStormExecution:
    """Represents a StackStorm execution"""
    id: str
    status: str
    start_timestamp: str
    end_timestamp: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None
    action: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class StackStormClient:
    """Client for interacting with StackStorm API"""
    
    def __init__(self):
        self.api_url = settings.STACKSTORM_API_URL
        self.auth_url = settings.STACKSTORM_AUTH_URL
        self.username = settings.STACKSTORM_USERNAME
        self.password = settings.STACKSTORM_PASSWORD
        self.api_key = settings.STACKSTORM_API_KEY
        self.verify_ssl = settings.STACKSTORM_VERIFY_SSL
        self.timeout = settings.STACKSTORM_TIMEOUT
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_token: Optional[str] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if aiohttp is None:
            raise ImportError("aiohttp is required for StackStorm client")
        
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def authenticate(self) -> bool:
        """Authenticate with StackStorm and get auth token"""
        try:
            session = await self._get_session()
            
            auth_data = {
                "username": self.username,
                "password": self.password
            }
            
            async with session.post(
                f"{self.auth_url}/auth/v1/tokens",
                json=auth_data,
                ssl=self.verify_ssl
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self._auth_token = result.get("token")
                    logger.info("Successfully authenticated with StackStorm")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        headers = {"Content-Type": "application/json"}
        
        if self._auth_token:
            headers["X-Auth-Token"] = self._auth_token
        elif self.api_key:
            headers["St2-Api-Key"] = self.api_key
        
        return headers
    
    async def create_pack(self, pack_data: Dict[str, Any]) -> bool:
        """Create a StackStorm pack"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.post(
                f"{self.api_url}/api/v1/packs",
                json=pack_data,
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Successfully created pack: {pack_data.get('name')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create pack: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error creating pack: {e}")
            return False
    
    async def create_action(self, action_data: Dict[str, Any]) -> bool:
        """Create a StackStorm action"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.post(
                f"{self.api_url}/api/v1/actions",
                json=action_data,
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Successfully created action: {action_data.get('name')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create action: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error creating action: {e}")
            return False
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> bool:
        """Create a StackStorm workflow"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.post(
                f"{self.api_url}/api/v1/actions",
                json=workflow_data,
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Successfully created workflow: {workflow_data.get('name')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create workflow: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return False
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> bool:
        """Create a StackStorm rule"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.post(
                f"{self.api_url}/api/v1/rules",
                json=rule_data,
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Successfully created rule: {rule_data.get('name')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create rule: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error creating rule: {e}")
            return False
    
    async def execute_action(self, action_ref: str, parameters: Dict[str, Any]) -> Optional[str]:
        """Execute a StackStorm action"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            execution_data = {
                "action": action_ref,
                "parameters": parameters
            }
            
            async with session.post(
                f"{self.api_url}/api/v1/executions",
                json=execution_data,
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    execution_id = result.get("id")
                    logger.info(f"Successfully executed action {action_ref}: {execution_id}")
                    return execution_id
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to execute action: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return None
    
    async def get_execution(self, execution_id: str) -> Optional[StackStormExecution]:
        """Get execution details"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.get(
                f"{self.api_url}/api/v1/executions/{execution_id}",
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return StackStormExecution(
                        id=data.get("id"),
                        status=data.get("status"),
                        start_timestamp=data.get("start_timestamp"),
                        end_timestamp=data.get("end_timestamp"),
                        result=data.get("result"),
                        context=data.get("context"),
                        action=data.get("action", {}).get("ref") if data.get("action") else None,
                        parameters=data.get("parameters")
                    )
                else:
                    logger.error(f"Failed to get execution: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting execution: {e}")
            return None
    
    async def list_executions(self, limit: int = 50, status: Optional[str] = None) -> List[StackStormExecution]:
        """List executions"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            params = {"limit": limit}
            if status:
                params["status"] = status
            
            async with session.get(
                f"{self.api_url}/api/v1/executions",
                headers=headers,
                params=params,
                ssl=self.verify_ssl
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    executions = []
                    for item in data:
                        executions.append(StackStormExecution(
                            id=item.get("id"),
                            status=item.get("status"),
                            start_timestamp=item.get("start_timestamp"),
                            end_timestamp=item.get("end_timestamp"),
                            result=item.get("result"),
                            context=item.get("context"),
                            action=item.get("action", {}).get("ref") if item.get("action") else None,
                            parameters=item.get("parameters")
                        ))
                    return executions
                else:
                    logger.error(f"Failed to list executions: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error listing executions: {e}")
            return []
    
    async def delete_action(self, action_ref: str) -> bool:
        """Delete a StackStorm action"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.delete(
                f"{self.api_url}/api/v1/actions/{action_ref}",
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Successfully deleted action: {action_ref}")
                    return True
                else:
                    logger.error(f"Failed to delete action: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting action: {e}")
            return False
    
    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a StackStorm rule"""
        try:
            session = await self._get_session()
            headers = await self._get_headers()
            
            async with session.delete(
                f"{self.api_url}/api/v1/rules/{rule_id}",
                headers=headers,
                ssl=self.verify_ssl
            ) as response:
                if response.status in [200, 204]:
                    logger.info(f"Successfully deleted rule: {rule_id}")
                    return True
                else:
                    logger.error(f"Failed to delete rule: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error deleting rule: {e}")
            return False
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
