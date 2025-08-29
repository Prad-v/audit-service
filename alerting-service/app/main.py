"""
Alerting Service Main Application

This is the main FastAPI application for the alerting service.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import init_db, close_db
from app.api.v1.alerts import router as alerts_router

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
    logger.info("Starting Alerting Service...")
    await init_db()
    logger.info("Alerting Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Alerting Service...")
    await close_db()
    logger.info("Alerting Service shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="Alerting Service",
    description="Policy-based alerting service for audit events",
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
    return {"status": "healthy", "service": "alerting"}


# Include routers
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["alerts"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
