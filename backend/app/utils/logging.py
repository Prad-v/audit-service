"""
Logging configuration for the audit log framework.

This module sets up structured logging using structlog with
proper formatting and output configuration.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import Processor

from app.config import LoggingSettings


def setup_logging(settings: LoggingSettings) -> None:
    """
    Setup structured logging configuration.
    
    Args:
        settings: Logging configuration settings
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.level.upper()),
    )
    
    # Configure processors based on format
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if settings.format.lower() == "json":
        processors.extend([
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ])
    else:
        processors.extend([
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.level.upper())
        ),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def add_correlation_id(correlation_id: str) -> None:
    """
    Add correlation ID to logging context.
    
    Args:
        correlation_id: Correlation ID to add
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def add_request_context(
    method: str,
    path: str,
    user_id: str = None,
    tenant_id: str = None,
) -> None:
    """
    Add request context to logging.
    
    Args:
        method: HTTP method
        path: Request path
        user_id: User ID if available
        tenant_id: Tenant ID if available
    """
    context = {
        "http_method": method,
        "http_path": path,
    }
    
    if user_id:
        context["user_id"] = user_id
    if tenant_id:
        context["tenant_id"] = tenant_id
    
    structlog.contextvars.bind_contextvars(**context)


def clear_context() -> None:
    """Clear logging context variables."""
    structlog.contextvars.clear_contextvars()