"""
Health check endpoints for the audit log framework.

This module provides comprehensive health checks for all system components
including database, cache, message queue, and external dependencies.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.config import get_settings
from app.db.database import get_database
from app.services.cache_service import get_cache_service
from app.services.nats_service import get_nats_service

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()


class HealthStatus(BaseModel):
    """Health status model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: Optional[float] = None


class ComponentHealth(BaseModel):
    """Individual component health model."""
    status: str
    response_time_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DetailedHealthResponse(BaseModel):
    """Detailed health check response model."""
    status: str
    timestamp: datetime
    version: str
    environment: str
    uptime_seconds: Optional[float] = None
    components: Dict[str, ComponentHealth]


# Application start time for uptime calculation
_start_time = time.time()


async def check_database_health() -> ComponentHealth:
    """Check database connectivity and performance."""
    start_time = time.time()
    
    try:
        db = await get_database()
        
        # Simple connectivity test
        result = await db.execute("SELECT 1")
        
        # Get some basic stats
        stats_query = """
        SELECT 
            COUNT(*) as total_connections,
            COUNT(CASE WHEN state = 'active' THEN 1 END) as active_connections
        FROM pg_stat_activity
        WHERE datname = current_database()
        """
        stats_result = await db.execute(stats_query)
        stats = dict(stats_result.fetchone()) if stats_result else {}
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            status="healthy",
            response_time_ms=response_time,
            details={
                "database_name": "audit_logs",
                "connection_stats": stats,
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("Database health check failed", error=str(e))
        
        return ComponentHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


async def check_cache_health() -> ComponentHealth:
    """Check Redis cache connectivity and performance."""
    start_time = time.time()
    
    try:
        cache = await get_cache_service()
        
        # Test basic operations
        test_key = "health_check_test"
        test_value = "test_value"
        
        # Set and get test
        await cache.set(test_key, test_value, ttl=10)
        retrieved_value = await cache.get(test_key)
        
        if retrieved_value != test_value:
            raise Exception("Cache set/get test failed")
        
        # Clean up
        await cache.delete(test_key)
        
        # Get Redis info
        info = await cache.info()
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            status="healthy",
            response_time_ms=response_time,
            details={
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("Cache health check failed", error=str(e))
        
        return ComponentHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


async def check_nats_health() -> ComponentHealth:
    """Check NATS connectivity and performance."""
    start_time = time.time()
    
    try:
        nats = await get_nats_service()
        
        # Check connection status
        if not nats.is_connected():
            raise Exception("NATS not connected")
        
        # Test publish/subscribe
        test_subject = "health.check.test"
        test_message = b"health_check_message"
        
        # Simple publish test
        await nats.publish(test_subject, test_message)
        
        # Get server info
        server_info = nats.get_server_info()
        
        response_time = (time.time() - start_time) * 1000
        
        return ComponentHealth(
            status="healthy",
            response_time_ms=response_time,
            details={
                "server_id": server_info.get("server_id"),
                "server_name": server_info.get("server_name"),
                "version": server_info.get("version"),
                "max_payload": server_info.get("max_payload"),
            }
        )
        
    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.error("NATS health check failed", error=str(e))
        
        return ComponentHealth(
            status="unhealthy",
            response_time_ms=response_time,
            error=str(e)
        )


@router.get("/", response_model=HealthStatus)
async def basic_health_check():
    """
    Basic health check endpoint.
    
    Returns basic application status without checking dependencies.
    This is suitable for load balancer health checks.
    """
    uptime = time.time() - _start_time
    
    return HealthStatus(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment=settings.environment,
        uptime_seconds=uptime,
    )


@router.get("/ready", response_model=HealthStatus)
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if the application is ready to serve requests.
    This includes basic dependency checks.
    """
    uptime = time.time() - _start_time
    
    try:
        # Quick check of critical dependencies
        db_task = check_database_health()
        cache_task = check_cache_health()
        nats_task = check_nats_health()
        
        # Run checks with timeout
        db_health, cache_health, nats_health = await asyncio.wait_for(
            asyncio.gather(db_task, cache_task, nats_task),
            timeout=5.0
        )
        
        # Check if any critical component is unhealthy
        if any(health.status == "unhealthy" for health in [db_health, cache_health, nats_health]):
            raise HTTPException(
                status_code=503,
                detail="One or more critical components are unhealthy"
            )
        
        return HealthStatus(
            status="ready",
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            environment=settings.environment,
            uptime_seconds=uptime,
        )
        
    except asyncio.TimeoutError:
        logger.error("Readiness check timed out")
        raise HTTPException(
            status_code=503,
            detail="Health check timed out"
        )
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="Application not ready"
        )


@router.get("/live", response_model=HealthStatus)
async def liveness_check():
    """
    Liveness check endpoint.
    
    Checks if the application is alive and responding.
    This is a simple check that doesn't verify dependencies.
    """
    uptime = time.time() - _start_time
    
    return HealthStatus(
        status="alive",
        timestamp=datetime.now(timezone.utc),
        version="0.1.0",
        environment=settings.environment,
        uptime_seconds=uptime,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check endpoint.
    
    Provides comprehensive health information for all system components.
    This endpoint is useful for monitoring and debugging.
    """
    uptime = time.time() - _start_time
    
    # Run all health checks concurrently
    db_task = check_database_health()
    cache_task = check_cache_health()
    nats_task = check_nats_health()
    
    try:
        # Run checks with timeout
        db_health, cache_health, nats_health = await asyncio.wait_for(
            asyncio.gather(db_task, cache_task, nats_task, return_exceptions=True),
            timeout=10.0
        )
        
        # Handle exceptions in individual checks
        components = {}
        
        if isinstance(db_health, Exception):
            components["database"] = ComponentHealth(
                status="unhealthy",
                error=str(db_health)
            )
        else:
            components["database"] = db_health
        
        if isinstance(cache_health, Exception):
            components["cache"] = ComponentHealth(
                status="unhealthy",
                error=str(cache_health)
            )
        else:
            components["cache"] = cache_health
        
        if isinstance(nats_health, Exception):
            components["message_queue"] = ComponentHealth(
                status="unhealthy",
                error=str(nats_health)
            )
        else:
            components["message_queue"] = nats_health
        
        # Determine overall status
        unhealthy_components = [
            name for name, health in components.items()
            if health.status == "unhealthy"
        ]
        
        overall_status = "unhealthy" if unhealthy_components else "healthy"
        
        return DetailedHealthResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            environment=settings.environment,
            uptime_seconds=uptime,
            components=components,
        )
        
    except asyncio.TimeoutError:
        logger.error("Detailed health check timed out")
        
        return DetailedHealthResponse(
            status="timeout",
            timestamp=datetime.now(timezone.utc),
            version="0.1.0",
            environment=settings.environment,
            uptime_seconds=uptime,
            components={
                "database": ComponentHealth(status="timeout", error="Health check timed out"),
                "cache": ComponentHealth(status="timeout", error="Health check timed out"),
                "message_queue": ComponentHealth(status="timeout", error="Health check timed out"),
            },
        )


@router.get("/metrics")
async def health_metrics():
    """
    Health metrics endpoint.
    
    Returns health-related metrics in a format suitable for monitoring systems.
    """
    uptime = time.time() - _start_time
    
    # Run quick health checks
    try:
        db_task = check_database_health()
        cache_task = check_cache_health()
        nats_task = check_nats_health()
        
        db_health, cache_health, nats_health = await asyncio.wait_for(
            asyncio.gather(db_task, cache_task, nats_task, return_exceptions=True),
            timeout=5.0
        )
        
        metrics = {
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database_status": 1 if not isinstance(db_health, Exception) and db_health.status == "healthy" else 0,
            "database_response_time_ms": db_health.response_time_ms if not isinstance(db_health, Exception) else None,
            "cache_status": 1 if not isinstance(cache_health, Exception) and cache_health.status == "healthy" else 0,
            "cache_response_time_ms": cache_health.response_time_ms if not isinstance(cache_health, Exception) else None,
            "message_queue_status": 1 if not isinstance(nats_health, Exception) and nats_health.status == "healthy" else 0,
            "message_queue_response_time_ms": nats_health.response_time_ms if not isinstance(nats_health, Exception) else None,
        }
        
        return metrics
        
    except Exception as e:
        logger.error("Health metrics check failed", error=str(e))
        return {
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }