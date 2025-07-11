"""
Game Service FastAPI Application.
Provides REST API for game catalog management.
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog


from app.api.v1.api import api_router
from app.database import check_database_connection


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Game Service...")

    # Check database connection
    db_connected = await check_database_connection()
    if not db_connected:
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")

    logger.info("Game Service started successfully")

    yield

    # Shutdown
    logger.info("Shutting down Game Service...")


# Create FastAPI application
app = FastAPI(
    title="Lugx Gaming - Game Service API",
    description="Microservice for managing game catalog, inventory, and reviews",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=os.getenv("ALLOWED_HOSTS", "*").split(",")
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next): # type: ignore
    """
    Log all HTTP requests and responses.
    """
    start_time = time.time()

    # Log request
    logger.info(
        "Request received",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # Process request
    response = await call_next(request) # type: ignore

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code, # type: ignore
        process_time=round(process_time, 4),
    )

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time) # type: ignore

    return response # type: ignore


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    """
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        exception=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None),
        },
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "game-service",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


# Health check endpoint
@app.get("/health")
async def health_check(): # type: ignore
    """
    Health check endpoint for monitoring.
    """
    from app.database import get_database_health

    # Check database health
    db_health = await get_database_health()

    # Determine overall health
    overall_status = "healthy" if db_health.get("status") == "healthy" else "unhealthy"

    return {
        "status": overall_status,
        "service": "game-service",
        "version": "1.0.0",
        "timestamp": time.time(),
        "checks": {
            "database": db_health,
        },
    } # type: ignore


# Include API router
app.include_router(api_router, prefix="/api/v1")


# Prometheus metrics endpoint (if enabled)
if os.getenv("ENABLE_METRICS", "false").lower() == "true":
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8001")),
        reload=os.getenv("ENVIRONMENT", "production") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True,
    )
