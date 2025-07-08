"""
Main API router for Game Service v1.
Aggregates all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import games, publishers, categories, inventory, reviews


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    games.router, 
    prefix="/games", 
    tags=["games"]
)

api_router.include_router(
    publishers.router, 
    prefix="/publishers", 
    tags=["publishers"]
)

api_router.include_router(
    categories.router, 
    prefix="/categories", 
    tags=["categories"]
)

api_router.include_router(
    inventory.router, 
    prefix="/inventory", 
    tags=["inventory"]
)

api_router.include_router(
    reviews.router, 
    prefix="/reviews", 
    tags=["reviews"]
)