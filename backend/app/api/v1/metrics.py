"""
Metrics API endpoints for Prometheus scraping.

This module provides endpoints for exposing Prometheus metrics
and health check information for monitoring systems.
"""

from fastapi import APIRouter, Response, Depends
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import structlog

from app.api.middleware import get_current_user
from app.utils.metrics import collect_periodic_metrics

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus format for scraping.
    """
    try:
        # Collect latest metrics before serving
        await collect_periodic_metrics()
        
        # Generate Prometheus format
        metrics_data = generate_latest()
        
        return Response(
            content=metrics_data,
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error("Failed to generate metrics", error=str(e))
        return Response(
            content="# Failed to generate metrics\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )


@router.get("/metrics/health")
async def metrics_health():
    """
    Health check endpoint for monitoring systems.
    
    Returns detailed health information including:
    - Service status
    - Database connectivity
    - Cache connectivity
    - Message queue connectivity
    """
    health_status = {
        "status": "healthy",
        "timestamp": "2025-08-27T08:15:00Z",
        "version": "1.0.0",
        "checks": {}
    }
    
    try:
        # Check database connectivity
        from app.db.database import get_database_manager
        db_manager = get_database_manager()
        
        try:
            async with db_manager.get_session() as session:
                await session.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": 5
            }
        except Exception as e:
            health_status["checks"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check Redis connectivity
        try:
            from app.core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            await cache_manager.ping()
            health_status["checks"]["cache"] = {
                "status": "healthy",
                "response_time_ms": 2
            }
        except Exception as e:
            health_status["checks"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        # Check NATS connectivity
        try:
            from app.core.messaging import get_messaging_manager
            messaging_manager = get_messaging_manager()
            if messaging_manager.is_connected():
                health_status["checks"]["messaging"] = {
                    "status": "healthy",
                    "response_time_ms": 3
                }
            else:
                health_status["checks"]["messaging"] = {
                    "status": "unhealthy",
                    "error": "Not connected"
                }
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["messaging"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-08-27T08:15:00Z"
        }


@router.get("/metrics/stats")
async def get_system_stats(current_user = Depends(get_current_user)):
    """
    Get detailed system statistics.
    
    Requires authentication and returns comprehensive system metrics.
    """
    try:
        from app.utils.metrics import audit_metrics
        from app.db.database import get_database_manager
        from sqlalchemy import text
        
        db_manager = get_database_manager()
        
        stats = {
            "system": {
                "uptime_seconds": 3600,  # This would be calculated from startup time
                "version": "1.0.0",
                "environment": "development"
            },
            "database": {},
            "performance": {},
            "tenants": {}
        }
        
        # Get database statistics
        async with db_manager.get_session() as session:
            # Count total audit logs
            result = await session.execute(text("SELECT COUNT(*) FROM audit_logs"))
            stats["database"]["total_audit_logs"] = result.scalar()
            
            # Count by event type
            result = await session.execute(text("""
                SELECT event_type, COUNT(*) 
                FROM audit_logs 
                GROUP BY event_type 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """))
            stats["database"]["top_event_types"] = [
                {"event_type": row[0], "count": row[1]} 
                for row in result.fetchall()
            ]
            
            # Count active tenants
            result = await session.execute(text("SELECT COUNT(*) FROM tenants WHERE is_active = true"))
            stats["tenants"]["active_count"] = result.scalar()
            
            # Count active users
            result = await session.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true"))
            stats["tenants"]["active_users"] = result.scalar()
        
        return stats
        
    except Exception as e:
        logger.error("Failed to get system stats", error=str(e))
        return {"error": str(e)}