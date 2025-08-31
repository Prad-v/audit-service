"""
Main FastAPI application entry point.

This module sets up the FastAPI application with all middleware, routes,
and lifecycle event handlers.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.middleware import (
    AuthenticationMiddleware,
    TenantIsolationMiddleware,
)
from app.api.v1 import audit, auth, health, metrics, mcp, llm, cloud
from app.config import get_settings
from app.core.exceptions import AuditLogException
from app.db.database import DatabaseManager
from app.services.cache_service import CacheService
from app.services.nats_service import NATSService
from app.utils.logging import setup_logging, LoggingMiddleware
from app.utils.metrics import setup_metrics

# Setup structured logging
logger = structlog.get_logger(__name__)

# Global settings
settings = get_settings()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global service instances
db_manager: DatabaseManager = None
cache_service: CacheService = None
nats_service: NATSService = None


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting audit log framework", version=fastapi_app.version)
    
    try:
        # Initialize services
        global db_manager, cache_service, nats_service
        
        # Database
        logger.info("Initializing database connection")
        db_manager = DatabaseManager(settings.database)
        await db_manager.initialize()
        fastapi_app.state.db = db_manager
        
        # Set global database manager for other components
        from app.db.database import set_database_manager
        set_database_manager(db_manager)
        
        # Cache
        logger.info("Initializing cache service")
        cache_service = CacheService(settings.redis)
        await cache_service.initialize()
        fastapi_app.state.cache = cache_service
        
        # Set global cache service for other components
        from app.services.cache_service import _cache_service
        import app.services.cache_service
        app.services.cache_service._cache_service = cache_service
        
        # NATS
        logger.info("Initializing NATS service")
        nats_service = NATSService(settings.nats)
        await nats_service.initialize()
        fastapi_app.state.nats = nats_service
        
        # Set global NATS service for other components
        import app.services.nats_service
        app.services.nats_service._nats_service = nats_service
        
        # Setup metrics
        if settings.monitoring.metrics_enabled:
            setup_metrics()
        
        logger.info("Application startup completed successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to start application", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down audit log framework")
        
        # Close services
        if nats_service:
            await nats_service.close()
        if cache_service:
            await cache_service.close()
        if db_manager:
            await db_manager.close()
        
        logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # Setup logging first
    setup_logging(settings.logging)
    
    # Create FastAPI app
    app = FastAPI(
        title="Audit Log Framework",
        description="High-performance audit logging system with multi-tenant support",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan,
    )
    
    # Add middleware (order matters!)
    
    # Trusted hosts
    if not settings.debug:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1", "*.yourdomain.com"]
        )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=settings.api.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Rate limiting
    if settings.rate_limit.enabled:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        app.add_middleware(SlowAPIMiddleware)
    
    # Logging middleware (should be early in the chain)
    app.add_middleware(LoggingMiddleware)
    
    # Authentication and authorization middleware
    app.add_middleware(TenantIsolationMiddleware)
    app.add_middleware(AuthenticationMiddleware)
    
    # Exception handlers
    @app.exception_handler(AuditLogException)
    async def audit_log_exception_handler(request: Request, exc: AuditLogException):
        """Handle custom audit log exceptions."""
        logger.error(
            "Audit log exception",
            error=str(exc),
            error_code=exc.error_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": str(exc),
                "details": exc.details,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An internal server error occurred",
            },
        )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit Logs"])
    app.include_router(mcp.router, prefix="/api/v1", tags=["MCP - Natural Language Queries"])
    app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM Providers"])
    app.include_router(cloud.router, prefix="/api/v1", tags=["Cloud Management"])
    
    # Metrics endpoints
    if settings.monitoring.prometheus_enabled:
        app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
    
    # Root endpoint
    @app.get("/", include_in_schema=False)
    async def root():
        """Root endpoint with basic information."""
        return {
            "name": "Audit Log Framework",
            "version": "0.1.0",
            "status": "running",
            "environment": settings.environment,
            "docs_url": "/docs" if settings.debug else None,
        }
    
    return app


# Create the application instance
app = create_app()


def main():
    """
    Main entry point for running the application.
    
    This function is used when running the application directly
    or through the CLI command.
    """
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Run the application
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload and settings.debug,
        workers=1 if settings.debug else settings.api.workers,
        log_level=settings.logging.level.lower(),
        access_log=True,
        log_config=log_config,
    )


if __name__ == "__main__":
    main()