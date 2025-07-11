#!/usr/bin/env python3
"""
Order Service - FastAPI Application
Handles user authentication, shopping cart, orders, and user management.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import get_database_health
from app.core.logging import configure_logging
from app.core.redis import init_redis, close_redis

# Configure structured logging
configure_logging()
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('order_service_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('order_service_request_duration_seconds', 'Request duration', ['method', 'endpoint'])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("🚀 Starting Order Service", version=settings.VERSION)
    
    # Startup
    try:
        # Test database connection
        health = await get_database_health()
        if health["status"] != "healthy":
            logger.error("Database health check failed", health=health)
            raise RuntimeError("Database connection failed")
        
        # Initialize Redis connection
        await init_redis()
        
        logger.info("✅ Order Service started successfully", database_status=health["status"])
        yield
        
    except Exception as e:
        logger.error("❌ Failed to start Order Service", error=str(e))
        raise
    finally:
        # Shutdown
        await close_redis()
        logger.info("🛑 Shutting down Order Service")


# Create FastAPI application
app = FastAPI(
    title="Lugx Gaming Platform - Order Service",
    description="User authentication, shopping cart, orders, and user management",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Request/response middleware for logging and metrics."""
    start_time = asyncio.get_event_loop().time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=str(request.query_params),
        user_agent=request.headers.get("user-agent", ""),
        client_ip=request.client.host if request.client else "unknown",
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate metrics
    duration = asyncio.get_event_loop().time() - start_time
    endpoint = request.url.path
    
    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=endpoint,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=endpoint
    ).observe(duration)
    
    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=f"{duration:.3f}s",
    )
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        method=request.method,
        path=request.url.path,
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint for load balancer and monitoring."""
    try:
        # Check database health
        db_health = await get_database_health()
        
        health_status = {
            "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
            "service": "order-service",
            "version": settings.VERSION,
            "timestamp": db_health["timestamp"],
            "checks": {
                "database": db_health,
            },
        }
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return Response(
            content=str(health_status),
            status_code=status_code,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return Response(
            content=str({
                "status": "unhealthy",
                "service": "order-service",
                "version": settings.VERSION,
                "error": str(e),
            }),
            status_code=503,
            media_type="application/json"
        )


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "order-service",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/api/docs" if settings.DEBUG else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=settings.DEBUG,
        log_level="info",
    )