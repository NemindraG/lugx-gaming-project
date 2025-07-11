"""
Shopping cart endpoints for Order Service.
Handles cart operations with Redis backend.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
import structlog

from app.core.redis import get_redis, RedisClient
from app.core.security import get_current_user_id, get_optional_user_id
from app.services.cart_service import CartService
from app.schemas.cart import (
    CartItemCreate, CartItemUpdate, CartItemResponse,
    CartResponse, BulkCartUpdate, PromoCode, CartTransfer
)

logger = structlog.get_logger()

router = APIRouter()


def get_session_id(request: Request) -> str:
    """Extract session ID from request headers or generate new one."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        # In production, you might use cookies or generate based on IP/User-Agent
        session_id = f"session_{hash(request.client.host)}_{hash(request.headers.get('user-agent', ''))}"
    return session_id


async def get_cart_service(
    request: Request,
    redis_client: RedisClient = Depends(get_redis),
    user_id: Optional[UUID] = Depends(get_optional_user_id)
) -> CartService:
    """Get cart service instance with user context."""
    session_id = get_session_id(request) if not user_id else None
    return CartService(redis_client, user_id, session_id)


@router.get("/", response_model=CartResponse)
async def get_cart(
    cart_service: CartService = Depends(get_cart_service)
) -> CartResponse:
    """Get user's shopping cart."""
    return await cart_service.get_cart()


@router.post("/items", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    item_create: CartItemCreate,
    cart_service: CartService = Depends(get_cart_service)
) -> CartItemResponse:
    """Add item to shopping cart."""
    return await cart_service.add_item(item_create)


@router.put("/items/{game_id}", response_model=CartItemResponse)
async def update_cart_item(
    game_id: UUID,
    item_update: CartItemUpdate,
    cart_service: CartService = Depends(get_cart_service)
) -> CartItemResponse:
    """Update cart item quantity."""
    updated_item = await cart_service.update_item(game_id, item_update)
    
    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    return updated_item


@router.delete("/items/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    game_id: UUID,
    cart_service: CartService = Depends(get_cart_service)
) -> None:
    """Remove item from shopping cart."""
    removed = await cart_service.remove_item(game_id)
    
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    cart_service: CartService = Depends(get_cart_service)
) -> None:
    """Clear entire shopping cart."""
    await cart_service.clear_cart()


@router.post("/bulk-update", response_model=CartResponse)
async def bulk_update_cart(
    bulk_update: BulkCartUpdate,
    cart_service: CartService = Depends(get_cart_service)
) -> CartResponse:
    """Bulk update cart items."""
    return await cart_service.bulk_update(bulk_update)


@router.post("/promo-code", response_model=CartResponse)
async def apply_promo_code(
    promo_data: PromoCode,
    cart_service: CartService = Depends(get_cart_service)
) -> CartResponse:
    """Apply promo code to cart."""
    return await cart_service.apply_promo_code(promo_data)


@router.delete("/promo-code", response_model=CartResponse)
async def remove_promo_code(
    cart_service: CartService = Depends(get_cart_service)
) -> CartResponse:
    """Remove promo code from cart."""
    return await cart_service.remove_promo_code()


@router.post("/transfer", status_code=status.HTTP_204_NO_CONTENT)
async def transfer_cart(
    current_user_id: UUID = Depends(get_current_user_id),
    redis_client: RedisClient = Depends(get_redis),
    request: Request = None
) -> None:
    """Transfer anonymous cart to user account on login."""
    session_id = get_session_id(request)
    
    # Create service for anonymous cart
    anonymous_cart_service = CartService(redis_client, None, session_id)
    
    # Transfer to user
    await anonymous_cart_service.transfer_cart(current_user_id)


@router.get("/count")
async def get_cart_item_count(
    cart_service: CartService = Depends(get_cart_service)
) -> dict:
    """Get cart item count for header display."""
    cart = await cart_service.get_cart()
    return {"count": cart.summary.total_items}