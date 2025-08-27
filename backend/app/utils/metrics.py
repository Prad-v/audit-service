"""
Metrics and monitoring utilities for the audit log framework.

This module provides Prometheus metrics collection and custom
performance monitoring for the audit log system.
"""

import time
from functools import wraps
from typing import Dict, Any, Optional

import structlog
from prometheus_client import Counter, Histogram, Gauge, Info

logger = structlog.get_logger(__name__)


class AuditMetrics:
    """Prometheus metrics for audit log operations."""
    
    def __init__(self):
        # Audit log creation metrics
        self.audit_logs_created = Counter(
            'audit_logs_created_total',
            'Total number of audit logs created',
            ['tenant_id', 'event_type']
        )
        
        self.audit_logs_by_type = Counter(
            'audit_logs_by_type_total',
            'Total number of audit logs by event type',
            ['event_type']
        )
        
        self.audit_logs_errors = Counter(
            'audit_logs_errors_total',
            'Total number of audit log creation errors',
            ['error_type']
        )
        
        # Batch operation metrics
        self.batch_operations = Counter(
            'audit_batch_operations_total',
            'Total number of batch operations',
            ['tenant_id']
        )
        
        self.batch_size = Histogram(
            'audit_batch_size',
            'Size of audit log batches',
            buckets=[1, 10, 50, 100, 500, 1000, 5000]
        )
        
        # Query metrics
        self.queries_executed = Counter(
            'audit_queries_executed_total',
            'Total number of audit queries executed',
            ['tenant_id', 'query_type']
        )
        
        self.query_duration = Histogram(
            'audit_query_duration_seconds',
            'Duration of audit queries in seconds',
            ['query_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        self.query_results = Histogram(
            'audit_query_results_count',
            'Number of results returned by queries',
            buckets=[1, 10, 50, 100, 500, 1000, 5000, 10000]
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'audit_cache_hits_total',
            'Total number of cache hits',
            ['cache_type']
        )
        
        self.cache_misses = Counter(
            'audit_cache_misses_total',
            'Total number of cache misses',
            ['cache_type']
        )
        
        # Export metrics
        self.exports_generated = Counter(
            'audit_exports_generated_total',
            'Total number of exports generated',
            ['tenant_id', 'format']
        )
        
        self.export_duration = Histogram(
            'audit_export_duration_seconds',
            'Duration of export operations in seconds',
            ['format'],
            buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
        )
        
        # Database metrics
        self.db_connections_active = Gauge(
            'audit_db_connections_active',
            'Number of active database connections'
        )
        
        self.db_operations = Counter(
            'audit_db_operations_total',
            'Total number of database operations',
            ['operation_type', 'table']
        )
        
        self.db_operation_duration = Histogram(
            'audit_db_operation_duration_seconds',
            'Duration of database operations in seconds',
            ['operation_type'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
        
        # NATS metrics
        self.nats_messages_published = Counter(
            'audit_nats_messages_published_total',
            'Total number of NATS messages published',
            ['subject']
        )
        
        self.nats_publish_errors = Counter(
            'audit_nats_publish_errors_total',
            'Total number of NATS publish errors',
            ['error_type']
        )
        
        # API metrics
        self.api_requests = Counter(
            'audit_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code']
        )
        
        self.api_request_duration = Histogram(
            'audit_api_request_duration_seconds',
            'Duration of API requests in seconds',
            ['method', 'endpoint'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
        )
        
        # System metrics
        self.system_info = Info(
            'audit_system_info',
            'System information'
        )
        
        self.active_tenants = Gauge(
            'audit_active_tenants',
            'Number of active tenants'
        )
        
        self.active_users = Gauge(
            'audit_active_users',
            'Number of active users'
        )


# Global metrics instance
audit_metrics = AuditMetrics()


def track_execution_time(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """
    Decorator to track execution time of functions.
    
    Args:
        metric_name: Name of the histogram metric to update
        labels: Optional labels for the metric
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric = getattr(audit_metrics, metric_name, None)
                if metric and hasattr(metric, 'observe'):
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric = getattr(audit_metrics, metric_name, None)
                if metric and hasattr(metric, 'observe'):
                    if labels:
                        metric.labels(**labels).observe(duration)
                    else:
                        metric.observe(duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def increment_counter(metric_name: str, labels: Optional[Dict[str, str]] = None, value: float = 1):
    """
    Increment a counter metric.
    
    Args:
        metric_name: Name of the counter metric
        labels: Optional labels for the metric
        value: Value to increment by (default: 1)
    """
    try:
        metric = getattr(audit_metrics, metric_name, None)
        if metric and hasattr(metric, 'inc'):
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
    except Exception as e:
        logger.warning("Failed to increment metric", metric=metric_name, error=str(e))


def set_gauge(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """
    Set a gauge metric value.
    
    Args:
        metric_name: Name of the gauge metric
        value: Value to set
        labels: Optional labels for the metric
    """
    try:
        metric = getattr(audit_metrics, metric_name, None)
        if metric and hasattr(metric, 'set'):
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
    except Exception as e:
        logger.warning("Failed to set gauge metric", metric=metric_name, error=str(e))


def observe_histogram(metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
    """
    Observe a value in a histogram metric.
    
    Args:
        metric_name: Name of the histogram metric
        value: Value to observe
        labels: Optional labels for the metric
    """
    try:
        metric = getattr(audit_metrics, metric_name, None)
        if metric and hasattr(metric, 'observe'):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
    except Exception as e:
        logger.warning("Failed to observe histogram metric", metric=metric_name, error=str(e))


class MetricsCollector:
    """Collector for custom application metrics."""
    
    def __init__(self):
        self.start_time = time.time()
    
    async def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # Update system info
            audit_metrics.system_info.info({
                'version': '1.0.0',
                'environment': 'development',  # Should come from config
                'uptime_seconds': str(int(time.time() - self.start_time)),
            })
            
            # Collect database metrics
            await self._collect_database_metrics()
            
            # Collect tenant/user metrics
            await self._collect_tenant_metrics()
            
        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))
    
    async def _collect_database_metrics(self):
        """Collect database-related metrics."""
        try:
            from app.db.database import get_database_manager
            db_manager = get_database_manager()
            
            # Get connection pool info
            if hasattr(db_manager, 'engine') and db_manager.engine:
                pool = db_manager.engine.pool
                if hasattr(pool, 'size'):
                    audit_metrics.db_connections_active.set(pool.checkedout())
            
        except Exception as e:
            logger.warning("Failed to collect database metrics", error=str(e))
    
    async def _collect_tenant_metrics(self):
        """Collect tenant and user metrics."""
        try:
            from app.db.database import get_database_manager
            from app.db.schemas import Tenant, User
            from sqlalchemy import select, func
            
            db_manager = get_database_manager()
            async with db_manager.get_session() as session:
                # Count active tenants
                tenant_count_stmt = select(func.count()).select_from(
                    select(Tenant).where(Tenant.is_active == True).subquery()
                )
                tenant_result = await session.execute(tenant_count_stmt)
                tenant_count = tenant_result.scalar()
                audit_metrics.active_tenants.set(tenant_count)
                
                # Count active users
                user_count_stmt = select(func.count()).select_from(
                    select(User).where(User.is_active == True).subquery()
                )
                user_result = await session.execute(user_count_stmt)
                user_count = user_result.scalar()
                audit_metrics.active_users.set(user_count)
                
        except Exception as e:
            logger.warning("Failed to collect tenant metrics", error=str(e))


# Global metrics collector
metrics_collector = MetricsCollector()


def setup_metrics():
    """Initialize metrics collection."""
    logger.info("Setting up metrics collection")
    
    # Set initial system info
    audit_metrics.system_info.info({
        'version': '1.0.0',
        'service': 'audit-log-framework',
        'started_at': str(int(time.time())),
    })
    
    logger.info("Metrics collection initialized")


async def collect_periodic_metrics():
    """Collect metrics that need periodic updates."""
    await metrics_collector.collect_system_metrics()