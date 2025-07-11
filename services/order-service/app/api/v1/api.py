"""
Order Service API v1 Router
Main API router that includes all endpoint modules.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, cart, orders, users, payments

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(cart.router, prefix="/cart", tags=["cart"])
api_router.include_router(orders.router, prefix="/orders", tags=["orders"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])

# Root API endpoint
@api_router.get("/")
async def api_root():
    """API root endpoint."""
    return {
        "message": "Order Service API v1",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "cart": "/api/v1/cart",
            "orders": "/api/v1/orders",
            "payments": "/api/v1/payments",
        },
    }