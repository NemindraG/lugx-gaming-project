"""
Logging configuration for Analytics Service.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def configure_logging():
    """Configure structured logging for the application."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Set log levels for external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("clickhouse_driver").setLevel(logging.WARNING)


def get_logger(name: str = None) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestLoggerMiddleware:
    """Middleware to add request context to logs."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """Add request context to all logs within the request."""
        if scope["type"] == "http":
            # Extract request information
            request_id = scope.get("request_id", "unknown")
            method = scope.get("method", "unknown")
            path = scope.get("path", "unknown")
            
            # Bind context to structlog
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
                method=method,
                path=path,
                service="analytics-service",
            )
        
        await self.app(scope, receive, send)