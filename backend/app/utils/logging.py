"""
Enhanced logging utilities with correlation IDs and structured logging.

This module provides comprehensive logging functionality including:
- Correlation ID tracking across requests
- Structured logging with consistent formatting
- Performance logging and metrics integration
- Request/response logging middleware
"""

import asyncio
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationIdProcessor:
    """Processor to add correlation ID to log records."""
    
    def __call__(self, logger, method_name, event_dict):
        """Add correlation ID to the event dictionary."""
        corr_id = correlation_id.get()
        if corr_id:
            event_dict['correlation_id'] = corr_id
        return event_dict


class RequestProcessor:
    """Processor to add request context to log records."""
    
    def __call__(self, logger, method_name, event_dict):
        """Add request context to the event dictionary."""
        # Add timestamp if not present
        if 'timestamp' not in event_dict:
            event_dict['timestamp'] = time.time()
        
        # Add service information
        event_dict['service'] = 'audit-log-framework'
        event_dict['version'] = '1.0.0'
        
        return event_dict


class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    async def log_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics for an operation."""
        log_data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'success': success,
        }
        
        if metadata:
            log_data.update(metadata)
        
        if success:
            self.logger.info("Operation completed", **log_data)
        else:
            self.logger.warning("Operation failed", **log_data)


class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self):
        self.logger = structlog.get_logger("audit")
    
    async def log_audit_event(
        self,
        event_type: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an audit event with structured data."""
        log_data = {
            'event_type': event_type,
            'tenant_id': tenant_id,
            'audit_category': 'system_audit',
        }
        
        if user_id:
            log_data['user_id'] = user_id
        if resource_id:
            log_data['resource_id'] = resource_id
        if action:
            log_data['action'] = action
        if metadata:
            log_data['metadata'] = metadata
        
        self.logger.info("Audit event", **log_data)
    
    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a security-related event."""
        log_data = {
            'event_type': event_type,
            'severity': severity,
            'description': description,
            'audit_category': 'security',
        }
        
        if source_ip:
            log_data['source_ip'] = source_ip
        if user_id:
            log_data['user_id'] = user_id
        if metadata:
            log_data['metadata'] = metadata
        
        if severity in ['high', 'critical']:
            self.logger.error("Security event", **log_data)
        elif severity == 'medium':
            self.logger.warning("Security event", **log_data)
        else:
            self.logger.info("Security event", **log_data)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs."""
    
    def __init__(self, app, logger_name: str = "http"):
        super().__init__(app)
        self.logger = structlog.get_logger(logger_name)
        self.performance_logger = PerformanceLogger()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and response with logging."""
        # Generate correlation ID
        corr_id = str(uuid.uuid4())
        correlation_id.set(corr_id)
        
        # Add correlation ID to request headers for downstream services
        request.headers.__dict__['_list'].append(
            (b'x-correlation-id', corr_id.encode())
        )
        
        start_time = time.time()
        
        # Log incoming request
        await self._log_request(request, corr_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            await self._log_response(request, response, duration, corr_id)
            
            # Log performance metrics
            await self.performance_logger.log_operation(
                operation=f"{request.method} {request.url.path}",
                duration=duration,
                success=response.status_code < 400,
                metadata={
                    'status_code': response.status_code,
                    'method': request.method,
                    'path': request.url.path,
                }
            )
            
            # Add correlation ID to response headers
            response.headers['X-Correlation-ID'] = corr_id
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Log error
            self.logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=corr_id,
            )
            
            # Log performance metrics for failed request
            await self.performance_logger.log_operation(
                operation=f"{request.method} {request.url.path}",
                duration=duration,
                success=False,
                metadata={
                    'method': request.method,
                    'path': request.url.path,
                    'error': str(e),
                }
            )
            
            raise
        finally:
            # Clear correlation ID
            correlation_id.set(None)
    
    async def _log_request(self, request: Request, corr_id: str):
        """Log incoming request details."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get user agent
        user_agent = request.headers.get("user-agent", "unknown")
        
        self.logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            client_ip=client_ip,
            user_agent=user_agent,
            correlation_id=corr_id,
        )
    
    async def _log_response(
        self,
        request: Request,
        response: Response,
        duration: float,
        corr_id: str
    ):
        """Log response details."""
        self.logger.info(
            "Request completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            correlation_id=corr_id,
        )


def setup_logging(config: Dict[str, Any]):
    """
    Setup structured logging configuration.
    
    Args:
        config: Logging configuration dictionary
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            CorrelationIdProcessor(),
            RequestProcessor(),
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(getattr(config, 'level', 'INFO').upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(getattr(config, 'level', 'INFO').upper()),
    )
    
    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id.get()


def set_correlation_id(corr_id: str):
    """Set the correlation ID for the current context."""
    correlation_id.set(corr_id)


# Global logger instances
performance_logger = PerformanceLogger()
audit_logger = AuditLogger()


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


async def log_async_operation(
    operation_name: str,
    func,
    *args,
    **kwargs
):
    """
    Wrapper to log async operations with timing and error handling.
    
    Args:
        operation_name: Name of the operation for logging
        func: Async function to execute
        *args: Arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function execution
    """
    logger = get_logger("operations")
    start_time = time.time()
    
    try:
        logger.info(f"Starting {operation_name}")
        result = await func(*args, **kwargs)
        
        duration = time.time() - start_time
        logger.info(
            f"Completed {operation_name}",
            duration_ms=round(duration * 1000, 2),
            success=True
        )
        
        return result
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"Failed {operation_name}",
            duration_ms=round(duration * 1000, 2),
            error=str(e),
            error_type=type(e).__name__,
            success=False
        )
        raise