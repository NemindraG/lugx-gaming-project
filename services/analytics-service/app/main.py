#!/usr/bin/env python3
"""
Analytics Service - FastAPI Application
Handles real-time analytics, event ingestion, and business intelligence.
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
from app.core.logging import configure_logging
from app.clients.clickhouse_client import ClickHouseClient

# Configure structured logging
configure_logging()
logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('analytics_service_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('analytics_service_request_duration_seconds', 'Request duration', ['method', 'endpoint'])

# Global ClickHouse client instance
clickhouse_client: ClickHouseClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global clickhouse_client
    
    logger.info("🚀 Starting Analytics Service", version=settings.VERSION)
    
    # Startup
    try:
        # Initialize ClickHouse client
        clickhouse_client = ClickHouseClient(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            database=settings.CLICKHOUSE_DATABASE,
            user=settings.CLICKHOUSE_USERNAME,
            password=settings.CLICKHOUSE_PASSWORD,
        )
        
        # Test ClickHouse connection
        await clickhouse_client.connect()
        logger.info("✅ ClickHouse connection established")
        
        # Initialize database schema
        await clickhouse_client.init_schema()
        logger.info("✅ ClickHouse schema initialized")
        
        # Make client available to endpoints
        app.state.clickhouse_client = clickhouse_client
        
        logger.info("✅ Analytics Service started successfully")
        yield
        
    except Exception as e:
        logger.error("❌ Failed to start Analytics Service", error=str(e))
        raise
    finally:
        # Shutdown
        if clickhouse_client:
            await clickhouse_client.close()
        logger.info("🛑 Analytics Service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Lugx Gaming Platform - Analytics Service",
    description="Real-time analytics, event ingestion, and business intelligence",
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
        # Check ClickHouse health
        clickhouse_health = await clickhouse_client.health_check()
        
        health_status = {
            "status": "healthy" if clickhouse_health["status"] == "healthy" else "unhealthy",
            "service": "analytics-service",
            "version": settings.VERSION,
            "timestamp": clickhouse_health["timestamp"],
            "checks": {
                "clickhouse": clickhouse_health,
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
                "service": "analytics-service",
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
        "service": "analytics-service",
        "version": settings.VERSION,
        "status": "running",
        "docs_url": "/api/docs" if settings.DEBUG else None,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.DEBUG,
        log_level="info",
    )