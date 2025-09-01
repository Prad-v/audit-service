"""
Events Service Main Application

This service handles events from various sources including:
- Grafana alerts
- Cloud provider alerts (GCP, AWS, Azure, OCI)
- Cloud outage status events
- Custom event sources
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import init_db, close_db
from app.api.v1.events import router as events_router
from app.api.v1.providers import router as providers_router
from app.api.v1.subscriptions import router as subscriptions_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.outages import router as outages_router
from app.api.v1.processors import router as processors_router
from app.services.background_tasks import background_task_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Events Service...")
    await init_db()
    
    # Start background tasks
    try:
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await background_task_manager.start_outage_monitoring(session)
        logger.info("Background tasks started successfully")
    except Exception as e:
        logger.error(f"Error starting background tasks: {e}")
    
    logger.info("Events Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Events Service...")
    
    # Stop background tasks
    try:
        await background_task_manager.stop_outage_monitoring()
        logger.info("Background tasks stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping background tasks: {e}")
    
    await close_db()
    logger.info("Events Service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Events Service",
    description="Cloud service provider events and monitoring service",
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


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "events"}


# Include routers
app.include_router(events_router, prefix="/api/v1/events", tags=["events"])
app.include_router(providers_router, prefix="/api/v1/providers", tags=["providers"])
app.include_router(subscriptions_router, prefix="/api/v1/subscriptions", tags=["subscriptions"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(outages_router, prefix="/api/v1", tags=["outage-monitoring"])
app.include_router(processors_router, prefix="/api/v1", tags=["event-processors"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
