"""
Synthetic Test Framework - Main Application

This is the main FastAPI application for the synthetic test framework.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .api.v1.tests import router as tests_router
from .services.webhook_service import WebhookService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Global webhook service instance
webhook_service = WebhookService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Synthetic Test Framework")
    
    # Start webhook server
    try:
        await webhook_service.start_webhook_server()
        logger.info("Webhook server started successfully")
    except Exception as e:
        logger.error(f"Failed to start webhook server: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Synthetic Test Framework")
    
    # Stop webhook server
    try:
        await webhook_service.stop_webhook_server()
        logger.info("Webhook server stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping webhook server: {e}")


# Create FastAPI application
app = FastAPI(
    title="Synthetic Test Framework",
    description="A framework for creating and executing synthetic tests with DAG support",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tests_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Synthetic Test Framework API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "synthetic-test-framework",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.LOG_LEVEL == "DEBUG" else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
