"""
Webhook Service for Synthetic Tests

This service handles webhook reception and validation for synthetic test scenarios.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger(__name__)


@dataclass
class WebhookData:
    """Represents webhook data"""
    headers: Dict[str, str]
    body: str
    query_params: Dict[str, str]
    received_at: datetime
    source_ip: Optional[str] = None


class WebhookService:
    """Service for handling webhooks in synthetic tests"""
    
    def __init__(self):
        self._webhook_app = FastAPI(title="Synthetic Test Webhook Receiver")
        self._pending_webhooks: Dict[str, asyncio.Queue] = {}
        self._setup_webhook_routes()
        self._server_task: Optional[asyncio.Task] = None
    
    def _setup_webhook_routes(self):
        """Setup webhook receiver routes"""
        
        @self._webhook_app.post("/webhook/{webhook_id}")
        async def receive_webhook(webhook_id: str, request: Request):
            """Receive webhook data"""
            try:
                # Get headers
                headers = dict(request.headers)
                
                # Get query parameters
                query_params = dict(request.query_params)
                
                # Get body
                body = await request.body()
                body_text = body.decode('utf-8')
                
                # Get client IP
                client_ip = request.client.host if request.client else None
                
                webhook_data = WebhookData(
                    headers=headers,
                    body=body_text,
                    query_params=query_params,
                    received_at=datetime.now(timezone.utc),
                    source_ip=client_ip
                )
                
                # Store webhook data
                if webhook_id in self._pending_webhooks:
                    await self._pending_webhooks[webhook_id].put(webhook_data)
                    logger.info(f"Received webhook for {webhook_id}")
                else:
                    logger.warning(f"No pending webhook for {webhook_id}")
                
                return JSONResponse(
                    content={"status": "received", "webhook_id": webhook_id},
                    status_code=200
                )
                
            except Exception as e:
                logger.error(f"Error receiving webhook: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self._webhook_app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "service": "webhook-receiver"}
    
    async def start_webhook_server(self, host: str = "0.0.0.0", port: int = 8001):
        """Start the webhook receiver server"""
        if self._server_task is None or self._server_task.done():
            config = uvicorn.Config(
                self._webhook_app,
                host=host,
                port=port,
                log_level="info"
            )
            server = uvicorn.Server(config)
            self._server_task = asyncio.create_task(server.serve())
            logger.info(f"Started webhook server on {host}:{port}")
    
    async def stop_webhook_server(self):
        """Stop the webhook receiver server"""
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped webhook server")
    
    async def wait_for_webhook(
        self,
        webhook_url: str,
        expected_headers: Optional[Dict[str, str]] = None,
        expected_body_schema: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Wait for a webhook to be received"""
        # Extract webhook ID from URL
        webhook_id = self._extract_webhook_id(webhook_url)
        
        # Create queue for this webhook if it doesn't exist
        if webhook_id not in self._pending_webhooks:
            self._pending_webhooks[webhook_id] = asyncio.Queue()
        
        try:
            # Wait for webhook data
            webhook_data = await asyncio.wait_for(
                self._pending_webhooks[webhook_id].get(),
                timeout=timeout_seconds
            )
            
            # Validate webhook data
            self._validate_webhook_data(webhook_data, expected_headers, expected_body_schema)
            
            return {
                "headers": webhook_data.headers,
                "body": webhook_data.body,
                "query_params": webhook_data.query_params,
                "received_at": webhook_data.received_at.isoformat(),
                "source_ip": webhook_data.source_ip
            }
            
        except asyncio.TimeoutError:
            raise Exception(f"Webhook timeout after {timeout_seconds} seconds")
        finally:
            # Clean up
            if webhook_id in self._pending_webhooks:
                del self._pending_webhooks[webhook_id]
    
    def _extract_webhook_id(self, webhook_url: str) -> str:
        """Extract webhook ID from URL"""
        # Simple implementation - in production, you might want more sophisticated parsing
        if "/webhook/" in webhook_url:
            return webhook_url.split("/webhook/")[-1].split("?")[0]
        else:
            # Generate a unique ID based on URL
            import hashlib
            return hashlib.md5(webhook_url.encode()).hexdigest()[:8]
    
    def _validate_webhook_data(
        self,
        webhook_data: WebhookData,
        expected_headers: Optional[Dict[str, str]] = None,
        expected_body_schema: Optional[Dict[str, Any]] = None
    ):
        """Validate received webhook data"""
        # Validate headers
        if expected_headers:
            for header_name, expected_value in expected_headers.items():
                if header_name not in webhook_data.headers:
                    raise Exception(f"Missing expected header: {header_name}")
                if webhook_data.headers[header_name] != expected_value:
                    raise Exception(
                        f"Header {header_name} mismatch: expected {expected_value}, "
                        f"got {webhook_data.headers[header_name]}"
                    )
        
        # Validate body schema
        if expected_body_schema:
            try:
                body_data = json.loads(webhook_data.body)
                self._validate_json_schema(body_data, expected_body_schema)
            except json.JSONDecodeError:
                raise Exception("Webhook body is not valid JSON")
    
    def _validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]):
        """Validate JSON data against a simple schema"""
        for field, expected_type in schema.items():
            if field not in data:
                raise Exception(f"Missing required field: {field}")
            
            if isinstance(expected_type, type):
                if not isinstance(data[field], expected_type):
                    raise Exception(
                        f"Field {field} type mismatch: expected {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
            elif isinstance(expected_type, dict):
                if isinstance(data[field], dict):
                    self._validate_json_schema(data[field], expected_type)
                else:
                    raise Exception(f"Field {field} should be an object")
            elif isinstance(expected_type, list):
                if not isinstance(data[field], list):
                    raise Exception(f"Field {field} should be an array")
                if expected_type and isinstance(expected_type[0], dict):
                    for item in data[field]:
                        if isinstance(item, dict):
                            self._validate_json_schema(item, expected_type[0])
    
    async def generate_webhook_url(self, webhook_id: str, base_url: str = "http://localhost:8001") -> str:
        """Generate a webhook URL for testing"""
        return f"{base_url}/webhook/{webhook_id}"
    
    async def cleanup(self):
        """Cleanup webhook service"""
        await self.stop_webhook_server()
        self._pending_webhooks.clear()
