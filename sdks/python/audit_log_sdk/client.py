"""
Client classes for the Audit Log Framework Python SDK.

This module provides both synchronous and asynchronous clients for
interacting with the Audit Log Framework API.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode, urljoin

import httpx

from .exceptions import (
    AuditLogSDKError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    TimeoutError,
    create_exception_from_response,
)
from .models import (
    AuditLogEvent,
    AuditLogEventCreate,
    AuditLogQuery,
    AuditLogSummary,
    AuditLogExport,
    PaginatedAuditLogs,
    BatchAuditLogCreate,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserCreate,
    UserUpdate,
    UserResponse,
    APIKeyCreate,
    APIKeyResponse,
    to_dict,
    from_dict,
)


class BaseClient:
    """Base client with common functionality."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the base client.
        
        Args:
            base_url: Base URL of the Audit Log API
            api_key: API key for authentication (optional)
            tenant_id: Tenant ID (required when using API key)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.tenant_id = tenant_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Validate configuration
        if api_key and not tenant_id:
            raise ConfigurationError("tenant_id is required when using api_key")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "audit-log-sdk-python/1.0.0",
        }
        
        # Add authentication headers
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
            if self.tenant_id:
                headers["X-Tenant-ID"] = self.tenant_id
        
        return headers
    
    def _build_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build full URL with query parameters."""
        url = urljoin(self.base_url, endpoint.lstrip('/'))
        
        if params:
            # Filter out None values and convert to strings
            clean_params = {}
            for key, value in params.items():
                if value is not None:
                    if isinstance(value, list):
                        # Handle list parameters (e.g., event_types)
                        for item in value:
                            clean_params[key] = str(item)
                    else:
                        clean_params[key] = str(value)
            
            if clean_params:
                url += f"?{urlencode(clean_params, doseq=True)}"
        
        return url
    
    def _handle_response_error(self, response: httpx.Response) -> None:
        """Handle HTTP error responses."""
        try:
            error_data = response.json()
        except (json.JSONDecodeError, ValueError):
            error_data = {
                "error": "http_error",
                "message": f"HTTP {response.status_code}: {response.reason_phrase}",
            }
        
        raise create_exception_from_response(response.status_code, error_data)
    
    def _should_retry(self, attempt: int, exception: Exception) -> bool:
        """Determine if request should be retried."""
        if attempt >= self.max_retries:
            return False
        
        # Retry on network errors and 5xx server errors
        if isinstance(exception, (NetworkError, httpx.RequestError)):
            return True
        
        if isinstance(exception, AuditLogSDKError) and exception.status_code:
            return exception.status_code >= 500
        
        return False


class AuditLogClient(BaseClient):
    """Synchronous client for the Audit Log Framework API."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = httpx.Client(timeout=self.timeout)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        if hasattr(self, '_client'):
            self._client.close()
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        url = self._build_url(endpoint, params)
        headers = self._get_headers()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                )
                
                if response.is_success:
                    return response
                
                self._handle_response_error(response)
                
            except httpx.RequestError as e:
                network_error = NetworkError(
                    message=f"Network error: {str(e)}",
                    original_error=e,
                )
                
                if not self._should_retry(attempt, network_error):
                    raise network_error
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
        
        # This should never be reached, but just in case
        raise NetworkError("Max retries exceeded")
    
    # Authentication methods
    def login(self, username: str, password: str, tenant_id: str) -> TokenResponse:
        """Login with username and password."""
        login_request = LoginRequest(
            username=username,
            password=password,
            tenant_id=tenant_id,
        )
        
        response = self._request(
            "POST",
            "/api/v1/auth/login",
            json_data=to_dict(login_request),
        )
        
        token_response = from_dict(response.json(), TokenResponse)
        
        # Store tokens
        self._access_token = token_response.access_token
        self._refresh_token = token_response.refresh_token
        
        return token_response
    
    def refresh_token(self) -> TokenResponse:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")
        
        refresh_request = RefreshTokenRequest(refresh_token=self._refresh_token)
        
        response = self._request(
            "POST",
            "/api/v1/auth/refresh",
            json_data=to_dict(refresh_request),
        )
        
        token_response = from_dict(response.json(), TokenResponse)
        
        # Update tokens
        self._access_token = token_response.access_token
        if token_response.refresh_token:
            self._refresh_token = token_response.refresh_token
        
        return token_response
    
    def logout(self) -> None:
        """Logout and clear tokens."""
        try:
            self._request("POST", "/api/v1/auth/logout")
        finally:
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
    
    # Audit log methods
    def create_event(self, event: AuditLogEventCreate) -> AuditLogEvent:
        """Create a single audit log event."""
        response = self._request(
            "POST",
            "/api/v1/audit/events",
            json_data=to_dict(event),
        )
        
        return from_dict(response.json(), AuditLogEvent)
    
    def create_events_batch(self, events: List[AuditLogEventCreate]) -> List[AuditLogEvent]:
        """Create multiple audit log events in batch."""
        batch_request = BatchAuditLogCreate(audit_logs=events)
        
        response = self._request(
            "POST",
            "/api/v1/audit/events/batch",
            json_data=to_dict(batch_request),
        )
        
        return [from_dict(item, AuditLogEvent) for item in response.json()]
    
    def get_event(self, event_id: str) -> AuditLogEvent:
        """Get a single audit log event by ID."""
        response = self._request("GET", f"/api/v1/audit/events/{event_id}")
        return from_dict(response.json(), AuditLogEvent)
    
    def query_events(
        self,
        query: Optional[AuditLogQuery] = None,
        page: int = 1,
        size: int = 50,
    ) -> PaginatedAuditLogs:
        """Query audit log events with filtering and pagination."""
        params = {"page": page, "size": size}
        
        if query:
            query_dict = to_dict(query)
            params.update(query_dict)
        
        response = self._request("GET", "/api/v1/audit/events", params=params)
        return from_dict(response.json(), PaginatedAuditLogs)
    
    def get_summary(self, query: Optional[AuditLogQuery] = None) -> AuditLogSummary:
        """Get audit log summary statistics."""
        params = {}
        if query:
            params = to_dict(query)
        
        response = self._request("GET", "/api/v1/audit/summary", params=params)
        return from_dict(response.json(), AuditLogSummary)
    
    def export_events(
        self,
        query: Optional[AuditLogQuery] = None,
        format: str = "json",
    ) -> AuditLogExport:
        """Export audit log events."""
        params = {"format": format}
        if query:
            query_dict = to_dict(query)
            params.update(query_dict)
        
        response = self._request("GET", "/api/v1/audit/events/export", params=params)
        return from_dict(response.json(), AuditLogExport)
    
    # User management methods
    def create_user(self, user: UserCreate) -> UserResponse:
        """Create a new user."""
        response = self._request(
            "POST",
            "/api/v1/auth/users",
            json_data=to_dict(user),
        )
        return from_dict(response.json(), UserResponse)
    
    def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID."""
        response = self._request("GET", f"/api/v1/auth/users/{user_id}")
        return from_dict(response.json(), UserResponse)
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        """Update user information."""
        response = self._request(
            "PUT",
            f"/api/v1/auth/users/{user_id}",
            json_data=to_dict(user_update),
        )
        return from_dict(response.json(), UserResponse)
    
    def deactivate_user(self, user_id: str) -> UserResponse:
        """Deactivate a user."""
        response = self._request("DELETE", f"/api/v1/auth/users/{user_id}")
        return from_dict(response.json(), UserResponse)
    
    def create_api_key(self, api_key: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key."""
        response = self._request(
            "POST",
            "/api/v1/auth/api-keys",
            json_data=to_dict(api_key),
        )
        return from_dict(response.json(), APIKeyResponse)
    
    def get_current_user(self) -> UserResponse:
        """Get current user information."""
        response = self._request("GET", "/api/v1/auth/me")
        return from_dict(response.json(), UserResponse)


class AsyncAuditLogClient(BaseClient):
    """Asynchronous client for the Audit Log Framework API."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client = httpx.AsyncClient(timeout=self.timeout)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        if hasattr(self, '_client'):
            await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """Make async HTTP request with retry logic."""
        url = self._build_url(endpoint, params)
        headers = self._get_headers()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                )
                
                if response.is_success:
                    return response
                
                self._handle_response_error(response)
                
            except httpx.RequestError as e:
                network_error = NetworkError(
                    message=f"Network error: {str(e)}",
                    original_error=e,
                )
                
                if not self._should_retry(attempt, network_error):
                    raise network_error
                
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
        
        raise NetworkError("Max retries exceeded")
    
    # Authentication methods (async versions)
    async def login(self, username: str, password: str, tenant_id: str) -> TokenResponse:
        """Login with username and password."""
        login_request = LoginRequest(
            username=username,
            password=password,
            tenant_id=tenant_id,
        )
        
        response = await self._request(
            "POST",
            "/api/v1/auth/login",
            json_data=to_dict(login_request),
        )
        
        token_response = from_dict(response.json(), TokenResponse)
        
        # Store tokens
        self._access_token = token_response.access_token
        self._refresh_token = token_response.refresh_token
        
        return token_response
    
    async def refresh_token(self) -> TokenResponse:
        """Refresh access token using refresh token."""
        if not self._refresh_token:
            raise AuthenticationError("No refresh token available")
        
        refresh_request = RefreshTokenRequest(refresh_token=self._refresh_token)
        
        response = await self._request(
            "POST",
            "/api/v1/auth/refresh",
            json_data=to_dict(refresh_request),
        )
        
        token_response = from_dict(response.json(), TokenResponse)
        
        # Update tokens
        self._access_token = token_response.access_token
        if token_response.refresh_token:
            self._refresh_token = token_response.refresh_token
        
        return token_response
    
    async def logout(self) -> None:
        """Logout and clear tokens."""
        try:
            await self._request("POST", "/api/v1/auth/logout")
        finally:
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
    
    # Audit log methods (async versions)
    async def create_event(self, event: AuditLogEventCreate) -> AuditLogEvent:
        """Create a single audit log event."""
        response = await self._request(
            "POST",
            "/api/v1/audit/events",
            json_data=to_dict(event),
        )
        
        return from_dict(response.json(), AuditLogEvent)
    
    async def create_events_batch(self, events: List[AuditLogEventCreate]) -> List[AuditLogEvent]:
        """Create multiple audit log events in batch."""
        batch_request = BatchAuditLogCreate(audit_logs=events)
        
        response = await self._request(
            "POST",
            "/api/v1/audit/events/batch",
            json_data=to_dict(batch_request),
        )
        
        return [from_dict(item, AuditLogEvent) for item in response.json()]
    
    async def get_event(self, event_id: str) -> AuditLogEvent:
        """Get a single audit log event by ID."""
        response = await self._request("GET", f"/api/v1/audit/events/{event_id}")
        return from_dict(response.json(), AuditLogEvent)
    
    async def query_events(
        self,
        query: Optional[AuditLogQuery] = None,
        page: int = 1,
        size: int = 50,
    ) -> PaginatedAuditLogs:
        """Query audit log events with filtering and pagination."""
        params = {"page": page, "size": size}
        
        if query:
            query_dict = to_dict(query)
            params.update(query_dict)
        
        response = await self._request("GET", "/api/v1/audit/events", params=params)
        return from_dict(response.json(), PaginatedAuditLogs)
    
    async def get_summary(self, query: Optional[AuditLogQuery] = None) -> AuditLogSummary:
        """Get audit log summary statistics."""
        params = {}
        if query:
            params = to_dict(query)
        
        response = await self._request("GET", "/api/v1/audit/summary", params=params)
        return from_dict(response.json(), AuditLogSummary)
    
    async def export_events(
        self,
        query: Optional[AuditLogQuery] = None,
        format: str = "json",
    ) -> AuditLogExport:
        """Export audit log events."""
        params = {"format": format}
        if query:
            query_dict = to_dict(query)
            params.update(query_dict)
        
        response = await self._request("GET", "/api/v1/audit/events/export", params=params)
        return from_dict(response.json(), AuditLogExport)
    
    # User management methods (async versions)
    async def create_user(self, user: UserCreate) -> UserResponse:
        """Create a new user."""
        response = await self._request(
            "POST",
            "/api/v1/auth/users",
            json_data=to_dict(user),
        )
        return from_dict(response.json(), UserResponse)
    
    async def get_user(self, user_id: str) -> UserResponse:
        """Get user by ID."""
        response = await self._request("GET", f"/api/v1/auth/users/{user_id}")
        return from_dict(response.json(), UserResponse)
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> UserResponse:
        """Update user information."""
        response = await self._request(
            "PUT",
            f"/api/v1/auth/users/{user_id}",
            json_data=to_dict(user_update),
        )
        return from_dict(response.json(), UserResponse)
    
    async def deactivate_user(self, user_id: str) -> UserResponse:
        """Deactivate a user."""
        response = await self._request("DELETE", f"/api/v1/auth/users/{user_id}")
        return from_dict(response.json(), UserResponse)
    
    async def create_api_key(self, api_key: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key."""
        response = await self._request(
            "POST",
            "/api/v1/auth/api-keys",
            json_data=to_dict(api_key),
        )
        return from_dict(response.json(), APIKeyResponse)
    
    async def get_current_user(self) -> UserResponse:
        """Get current user information."""
        response = await self._request("GET", "/api/v1/auth/me")
        return from_dict(response.json(), UserResponse)