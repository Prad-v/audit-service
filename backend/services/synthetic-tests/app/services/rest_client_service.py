"""
REST Client Service for Synthetic Tests

This service handles HTTP requests for synthetic test scenarios.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


@dataclass
class HTTPResponse:
    """Represents an HTTP response"""
    status_code: int
    headers: Dict[str, str]
    text: str
    json_data: Optional[Dict[str, Any]] = None


class RestClientService:
    """Service for making HTTP requests"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def make_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[str] = None,
        timeout_seconds: int = 30
    ) -> HTTPResponse:
        """Make an HTTP request"""
        if aiohttp is None:
            raise ImportError("aiohttp is required for REST client service")
        
        session = await self._get_session()
        
        # Prepare headers
        request_headers = headers or {}
        request_headers.setdefault('User-Agent', 'Synthetic-Test-Framework/1.0')
        
        # Prepare data
        data = None
        if body:
            if request_headers.get('Content-Type') == 'application/json':
                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    data = body
            else:
                data = body
        
        try:
            async with session.request(
                method=method.upper(),
                url=url,
                headers=request_headers,
                json=data if isinstance(data, dict) else None,
                data=data if not isinstance(data, dict) else None,
                timeout=aiohttp.ClientTimeout(total=timeout_seconds)
            ) as response:
                response_text = await response.text()
                
                # Try to parse as JSON
                json_data = None
                try:
                    json_data = await response.json()
                except (json.JSONDecodeError, aiohttp.ContentTypeError):
                    pass
                
                return HTTPResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    text=response_text,
                    json_data=json_data
                )
                
        except asyncio.TimeoutError:
            raise Exception(f"Request timeout after {timeout_seconds} seconds")
        except Exception as e:
            raise Exception(f"HTTP request failed: {e}")
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, timeout_seconds: int = 30) -> HTTPResponse:
        """Make a GET request"""
        return await self.make_request(url, "GET", headers, None, timeout_seconds)
    
    async def post(
        self,
        url: str,
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 30
    ) -> HTTPResponse:
        """Make a POST request"""
        return await self.make_request(url, "POST", headers, body, timeout_seconds)
    
    async def put(
        self,
        url: str,
        body: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 30
    ) -> HTTPResponse:
        """Make a PUT request"""
        return await self.make_request(url, "PUT", headers, body, timeout_seconds)
    
    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None, timeout_seconds: int = 30) -> HTTPResponse:
        """Make a DELETE request"""
        return await self.make_request(url, "DELETE", headers, None, timeout_seconds)
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
