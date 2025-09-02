"""
Webhook Server Manager

This module manages multiple webhook servers based on Vector's HTTP Server source capabilities.
"""

import logging
import asyncio
import json
import hashlib
from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass
from contextlib import asynccontextmanager

import aiohttp
from aiohttp import web, ClientSession
from aiohttp_cors import setup as cors_setup, ResourceOptions

from app.models.events import WebhookSubscriptionResponse, WebhookConfig

logger = logging.getLogger(__name__)


@dataclass
class WebhookServerStatus:
    """Status information for a webhook server"""
    subscription_id: str
    name: str
    address: str
    port: int
    running: bool
    start_time: Optional[datetime] = None
    last_request: Optional[datetime] = None
    total_requests: int = 0
    error_count: int = 0
    active_connections: int = 0


class WebhookServer:
    """Individual webhook server instance"""
    
    def __init__(self, subscription: WebhookSubscriptionResponse):
        self.subscription = subscription
        self.config = subscription.config
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.status = WebhookServerStatus(
            subscription_id=subscription.subscription_id,
            name=subscription.name,
            address=self.config.address,
            port=self.config.port,
            running=False
        )
        self._setup_routes()
        self._setup_cors()
        self._setup_middleware()
    
    def _setup_routes(self):
        """Setup webhook routes"""
        self.app.router.add_route(
            method=self.config.method,
            path=self.config.endpoint,
            handler=self._handle_webhook
        )
        
        # Add health check endpoint
        self.app.router.add_get("/health", self._health_check)
    
    def _setup_cors(self):
        """Setup CORS if enabled"""
        if self.config.cors.enabled:
            cors = cors_setup(self.app, defaults={
                "*": ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods=self.config.cors.methods
                )
            })
            
            # Add CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)
    
    def _setup_middleware(self):
        """Setup middleware for authentication, rate limiting, etc."""
        self.app.middlewares.append(self._auth_middleware)
        self.app.middlewares.append(self._rate_limit_middleware)
        self.app.middlewares.append(self._logging_middleware)
    
    async def _auth_middleware(self, request, handler):
        """Authentication middleware"""
        try:
            if self.config.authentication != "none":
                if not await self._authenticate_request(request):
                    return web.Response(
                        text="Unauthorized",
                        status=401,
                        headers={"WWW-Authenticate": "Basic realm=Webhook"}
                    )
            return await handler(request)
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return web.Response(text="Internal Server Error", status=500)
    
    async def _rate_limit_middleware(self, request, handler):
        """Rate limiting middleware"""
        # Simple in-memory rate limiting
        # In production, use Redis or similar
        current_time = datetime.now()
        if hasattr(self, '_last_request_time'):
            time_diff = (current_time - self._last_request_time).total_seconds()
            if time_diff < 60.0 / self.config.rate_limit:
                return web.Response(text="Rate limit exceeded", status=429)
        
        self._last_request_time = current_time
        return await handler(request)
    
    async def _logging_middleware(self, request, handler):
        """Logging middleware"""
        start_time = datetime.now()
        try:
            response = await handler(request)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Webhook request: {request.method} {request.path} - {response.status} "
                f"({duration:.3f}s)"
            )
            return response
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Webhook request error: {request.method} {request.path} - {e} "
                f"({duration:.3f}s)"
            )
            raise
    
    async def _authenticate_request(self, request: web.Request) -> bool:
        """Authenticate incoming request based on configuration"""
        try:
            if self.config.authentication == "basic":
                return await self._authenticate_basic(request)
            elif self.config.authentication == "bearer":
                return await self._authenticate_bearer(request)
            elif self.config.authentication == "api_key":
                return await self._authenticate_api_key(request)
            elif self.config.authentication == "custom":
                return await self._authenticate_custom(request)
            else:
                return True
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def _authenticate_basic(self, request: web.Request) -> bool:
        """Basic authentication"""
        if not self.config.auth_basic:
            return False
        
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Basic "):
            return False
        
        import base64
        try:
            credentials = base64.b64decode(auth_header[6:]).decode()
            username, password = credentials.split(":", 1)
            return (
                username == self.config.auth_basic.username and
                password == self.config.auth_basic.password
            )
        except Exception:
            return False
    
    async def _authenticate_bearer(self, request: web.Request) -> bool:
        """Bearer token authentication"""
        if not self.config.auth_bearer:
            return False
        
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False
        
        token = auth_header[7:]
        return token == self.config.auth_bearer.token
    
    async def _authenticate_api_key(self, request: web.Request) -> bool:
        """API key authentication"""
        if not self.config.auth_api_key:
            return False
        
        api_key = request.headers.get(self.config.auth_api_key.header_name, "")
        return api_key == self.config.auth_api_key.api_key
    
    async def _authenticate_custom(self, request: web.Request) -> bool:
        """Custom VRL expression authentication"""
        if not self.config.auth_custom:
            return False
        
        # For now, return True as VRL evaluation would need to be implemented
        # In production, this would evaluate the VRL expression against request data
        logger.warning("Custom VRL authentication not yet implemented")
        return True
    
    async def _handle_webhook(self, request: web.Request) -> web.Response:
        """Handle incoming webhook requests"""
        try:
            self.status.last_request = datetime.now()
            self.status.total_requests += 1
            
            # Parse request body based on encoding
            body = await self._parse_request_body(request)
            
            # Extract headers and query parameters
            headers = self._extract_headers(request)
            query_params = self._extract_query_params(request)
            
            # Create event data
            event_data = {
                "message": body,
                "timestamp": datetime.now().isoformat(),
                "source_type": "webhook",
                "subscription_id": self.subscription.subscription_id,
                "path": str(request.path),
                "method": request.method,
                "headers": headers,
                "query_parameters": query_params,
                "remote_addr": request.remote,
                "user_agent": request.headers.get("User-Agent", ""),
                "content_type": request.headers.get("Content-Type", ""),
            }
            
            # Add configured keys
            if self.config.path_key:
                event_data[self.config.path_key] = str(request.path)
            if self.config.host_key:
                event_data[self.config.host_key] = request.headers.get("Host", "")
            
            # Process event (send to event pipeline)
            await self._process_event(event_data)
            
            # Return configured response
            return web.Response(
                text="Event received successfully",
                status=self.config.response_code,
                content_type="text/plain"
            )
            
        except Exception as e:
            self.status.error_count += 1
            logger.error(f"Error handling webhook request: {e}")
            return web.Response(
                text="Internal Server Error",
                status=500,
                content_type="text/plain"
            )
    
    async def _parse_request_body(self, request: web.Request) -> Any:
        """Parse request body based on encoding configuration"""
        try:
            if self.config.encoding == "json":
                return await request.json()
            elif self.config.encoding == "text":
                return await request.text()
            elif self.config.encoding == "binary":
                return await request.read()
            elif self.config.encoding == "avro":
                # Avro parsing would need to be implemented
                return await request.read()
            else:
                return await request.text()
        except Exception as e:
            logger.error(f"Error parsing request body: {e}")
            return await request.text()
    
    def _extract_headers(self, request: web.Request) -> Dict[str, str]:
        """Extract configured headers from request"""
        extracted = {}
        for header_name in self.config.headers:
            if header_name in request.headers:
                extracted[header_name] = request.headers[header_name]
        return extracted
    
    def _extract_query_params(self, request: web.Request) -> Dict[str, str]:
        """Extract configured query parameters from request"""
        extracted = {}
        for param_name in self.config.query_parameters:
            if param_name in request.query:
                extracted[param_name] = request.query[param_name]
        return extracted
    
    async def _process_event(self, event_data: Dict[str, Any]):
        """Process received event (send to event pipeline)"""
        try:
            # In production, this would send the event to the event processing pipeline
            # For now, just log it
            logger.info(f"Processed webhook event: {event_data.get('message', 'No message')}")
            
            # TODO: Send to event processing pipeline
            # await event_pipeline.process_event(event_data)
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
    
    async def _health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "subscription_id": self.subscription.subscription_id,
            "name": self.subscription.name,
            "uptime": (
                (datetime.now() - self.status.start_time).total_seconds()
                if self.status.start_time else 0
            ),
            "total_requests": self.status.total_requests,
            "error_count": self.status.error_count
        })
    
    async def start(self):
        """Start the webhook server"""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(
                self.runner,
                self.config.address,
                self.config.port
            )
            await self.site.start()
            
            self.status.running = True
            self.status.start_time = datetime.now()
            
            logger.info(
                f"Started webhook server for {self.subscription.name} "
                f"on {self.config.address}:{self.config.port}"
            )
            
        except Exception as e:
            logger.error(f"Error starting webhook server: {e}")
            raise
    
    async def stop(self):
        """Stop the webhook server"""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            self.status.running = False
            
            logger.info(f"Stopped webhook server for {self.subscription.name}")
            
        except Exception as e:
            logger.error(f"Error stopping webhook server: {e}")
            raise


class WebhookServerManager:
    """Manages multiple webhook servers"""
    
    def __init__(self):
        self.servers: Dict[str, WebhookServer] = {}
        self._lock = asyncio.Lock()
    
    async def start_webhook_server(self, subscription: WebhookSubscriptionResponse):
        """Start a webhook server for a subscription"""
        async with self._lock:
            try:
                if subscription.subscription_id in self.servers:
                    logger.warning(f"Webhook server already exists for {subscription.subscription_id}")
                    return
                
                server = WebhookServer(subscription)
                await server.start()
                self.servers[subscription.subscription_id] = server
                
                logger.info(f"Started webhook server for subscription {subscription.subscription_id}")
                
            except Exception as e:
                logger.error(f"Error starting webhook server: {e}")
                raise
    
    async def start_webhook_server_by_id(self, subscription_id: str):
        """Start a webhook server by subscription ID"""
        # This would typically load the subscription from database
        # For now, just log the attempt
        logger.info(f"Attempting to start webhook server for subscription {subscription_id}")
    
    async def stop_webhook_server(self, subscription_id: str):
        """Stop a webhook server"""
        async with self._lock:
            try:
                if subscription_id in self.servers:
                    server = self.servers[subscription_id]
                    await server.stop()
                    del self.servers[subscription_id]
                    
                    logger.info(f"Stopped webhook server for subscription {subscription_id}")
                else:
                    logger.warning(f"No webhook server found for subscription {subscription_id}")
                    
            except Exception as e:
                logger.error(f"Error stopping webhook server: {e}")
                raise
    
    async def get_webhook_server_status(self, subscription_id: str) -> Optional[WebhookServerStatus]:
        """Get status of a webhook server"""
        if subscription_id in self.servers:
            return self.servers[subscription_id].status
        return None
    
    async def get_all_webhook_server_statuses(self) -> List[WebhookServerStatus]:
        """Get status of all webhook servers"""
        return [server.status for server in self.servers.values()]
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for webhook manager"""
        try:
            total_servers = len(self.servers)
            running_servers = sum(1 for server in self.servers.values() if server.status.running)
            
            return {
                "status": "healthy",
                "total_servers": total_servers,
                "running_servers": running_servers,
                "stopped_servers": total_servers - running_servers,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def stop_all_servers(self):
        """Stop all webhook servers"""
        async with self._lock:
            try:
                for subscription_id in list(self.servers.keys()):
                    await self.stop_webhook_server(subscription_id)
                    
                logger.info("Stopped all webhook servers")
                
            except Exception as e:
                logger.error(f"Error stopping all webhook servers: {e}")
                raise
