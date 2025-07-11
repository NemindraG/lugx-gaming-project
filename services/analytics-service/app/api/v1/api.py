"""
Analytics Service API v1 Router
Main API router that includes all endpoint modules.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import events, analytics, dashboards

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(events.router, prefix="/events", tags=["events"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])

# Root API endpoint
@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Analytics Service API v1",
        "version": "1.0.0",
        "endpoints": {
            "events": "/api/v1/events",
            "analytics": "/api/v1/analytics",
            "dashboards": "/api/v1/dashboards",
        },
    }