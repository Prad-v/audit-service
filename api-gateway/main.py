"""
Unified API Gateway

This service provides a single entry point for all API documentation and endpoints,
combining the main audit service API and the alerting service API.
"""

import asyncio
import logging
from typing import Dict, Any, List
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service configurations
SERVICES = {
    "audit": {
        "name": "Audit Service",
        "base_url": "http://audit-api:8000",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health/"
    },
    "alerting": {
        "name": "Alerting Service", 
        "base_url": "http://audit-alerting:8001",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health"
    },
    "events": {
        "name": "Events Service",
        "base_url": "http://audit-events:8003",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "health_url": "/health"
    },

}

# Global HTTP client
http_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global http_client
    
    # Startup
    logger.info("Starting Unified API Gateway...")
    http_client = httpx.AsyncClient(timeout=30.0)
    logger.info("Unified API Gateway started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Unified API Gateway...")
    if http_client:
        await http_client.aclose()
    logger.info("Unified API Gateway shut down successfully")

# Create FastAPI app
app = FastAPI(
    title="Unified Audit Service API",
    description="Combined API documentation for Audit Service, Alerting Service, and Events Service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_service_openapi(service_name: str) -> Dict[str, Any]:
    """Fetch OpenAPI specification from a service"""
    try:
        service_config = SERVICES[service_name]
        response = await http_client.get(f"{service_config['base_url']}{service_config['openapi_url']}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching OpenAPI from {service_name}: {e}")
        return None

async def merge_openapi_specs() -> Dict[str, Any]:
    """Merge OpenAPI specifications from all services"""
    merged_spec = {
        "openapi": "3.0.2",
        "info": {
            "title": "Unified Audit Service API",
            "description": "Combined API documentation for Audit Service, Alerting Service, and Events Service",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "/api/v1", "description": "Main API"},
            {"url": "/api/v1/alerts", "description": "Alerting API"}
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "tags": []
    }
    
    # Fetch and merge OpenAPI specs from all services
    for service_name, service_config in SERVICES.items():
        spec = await get_service_openapi(service_name)
        if spec:
            # Add service tag
            service_tag = {
                "name": service_name,
                "description": f"{service_config['name']} endpoints"
            }
            merged_spec["tags"].append(service_tag)
            
            # Merge paths with service prefix
            for path, path_item in spec.get("paths", {}).items():
                if service_name == "audit":
                    # Audit service paths remain as-is
                    merged_path = path
                else:
                    # Alerting service paths get /alerts prefix
                    merged_path = f"/alerts{path}"
                
                # Add service tag to all operations
                for method in ["get", "post", "put", "delete", "patch"]:
                    if method in path_item:
                        if "tags" not in path_item[method]:
                            path_item[method]["tags"] = []
                        path_item[method]["tags"].append(service_name)
                
                merged_spec["paths"][merged_path] = path_item
            
            # Merge schemas
            for schema_name, schema in spec.get("components", {}).get("schemas", {}).items():
                merged_spec["components"]["schemas"][schema_name] = schema
    
    return merged_spec

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "service": "unified-api-gateway",
        "services": {}
    }
    
    # Check health of all services
    for service_name, service_config in SERVICES.items():
        try:
            response = await http_client.get(f"{service_config['base_url']}{service_config['health_url']}")
            if response.status_code == 200:
                health_status["services"][service_name] = "healthy"
            else:
                health_status["services"][service_name] = "unhealthy"
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            health_status["services"][service_name] = "unreachable"
    
    return health_status

@app.get("/openapi.json")
async def get_openapi_spec():
    """Get merged OpenAPI specification"""
    return await merge_openapi_specs()

@app.get("/docs", response_class=HTMLResponse)
async def get_docs():
    """Serve unified API documentation"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Unified Audit Service API - Swagger UI</title>
        <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css" />
        <style>
            html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
            *, *:before, *:after { box-sizing: inherit; }
            body { margin:0; background: #fafafa; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {
                const ui = SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    tagsSorter: "alpha",
                    operationsSorter: "alpha"
                });
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Proxy endpoints to individual services
@app.api_route("/api/v1/alerts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_alerting_api(request: Request, path: str):
    """Proxy requests to alerting service"""
    try:
        # Build target URL
        target_url = f"{SERVICES['alerting']['base_url']}/api/v1/alerts/{path}"
        
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=body
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to alerting service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_audit_api(request: Request, path: str):
    """Proxy requests to audit service"""
    try:
        # Build target URL
        target_url = f"{SERVICES['audit']['base_url']}/api/v1/{path}"
        
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=body
        )
        
        # Handle responses with no content (like 204 DELETE responses)
        if response.status_code == 204 or not response.content:
            return JSONResponse(
                content=None,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to audit service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.api_route("/events/api/v1/events/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_events_api(request: Request, path: str):
    """Proxy requests to events service events endpoints"""
    try:
        # Build target URL
        target_url = f"{SERVICES['events']['base_url']}/api/v1/events/{path}"
        
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=body
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to events service: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.api_route("/events/api/v1/providers/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_events_providers_api(request: Request, path: str):
    """Proxy requests to events service providers endpoints"""
    try:
        # Build target URL
        target_url = f"{SERVICES['events']['base_url']}/api/v1/providers/{path}"
        
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=body
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to events service providers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.api_route("/events/api/v1/subscriptions/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_events_subscriptions_api(request: Request, path: str):
    """Proxy requests to events service subscriptions endpoints"""
    try:
        # Build target URL
        target_url = f"{SERVICES['events']['base_url']}/api/v1/subscriptions/{path}"
        
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=body
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to events service subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.api_route("/events/api/v1/alerts/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_events_alerts_api(request: Request, path: str):
    """Proxy requests to events service alerts endpoints"""
    try:
        # Build target URL
        target_url = f"{SERVICES['events']['base_url']}/api/v1/alerts/{path}"
        
        # Get request body
        body = await request.body()
        
        # Forward request
        response = await http_client.request(
            method=request.method,
            url=target_url,
            headers=dict(request.headers),
            params=dict(request.query_params),
            content=body
        )
        
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error proxying to events service alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
