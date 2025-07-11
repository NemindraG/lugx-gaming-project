"""
Order management endpoints for Order Service.
Handles order creation, tracking, and management operations.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.database import get_async_session
from app.core.redis import get_redis, RedisClient
from app.core.security import get_current_user_id
from app.services.order_service import OrderService
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderResponse, PaymentRequest,
    OrderListFilter, OrderStats
)

logger = structlog.get_logger()

router = APIRouter()


async def get_order_service(
    session: AsyncSession = Depends(get_async_session),
    redis_client: RedisClient = Depends(get_redis)
) -> OrderService:
    """Get order service instance."""
    return OrderService(session, redis_client)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_create: OrderCreate,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Create new order from cart."""
    return await order_service.create_order_from_cart(current_user_id, order_create)


@router.get("/", response_model=List[OrderResponse])
async def get_user_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> List[OrderResponse]:
    """Get user's order history with pagination and filtering."""
    return await order_service.get_user_orders(
        user_id=current_user_id,
        limit=limit,
        offset=offset
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Get specific order details."""
    return await order_service.get_order(order_id, current_user_id)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_update: OrderUpdate,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Update order (limited fields for users)."""
    return await order_service.update_order(order_id, current_user_id, order_update)


@router.put("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> OrderResponse:
    """Cancel an order."""
    return await order_service.cancel_order(order_id, current_user_id)


@router.post("/{order_id}/payment")
async def process_payment(
    order_id: UUID,
    payment_request: PaymentRequest,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> dict:
    """Process payment for an order."""
    return await order_service.process_payment(order_id, current_user_id, payment_request)


@router.get("/{order_id}/status")
async def get_order_status(
    order_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> dict:
    """Get order status and tracking information."""
    order = await order_service.get_order(order_id, current_user_id)
    
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "status": order.status,
        "payment_status": order.payment_status,
        "tracking_number": order.tracking_number,
        "estimated_delivery": order.estimated_delivery,
        "created_at": order.created_at,
        "updated_at": order.updated_at
    }


@router.get("/{order_id}/invoice")
async def get_order_invoice(
    order_id: UUID,
    current_user_id: UUID = Depends(get_current_user_id),
    order_service: OrderService = Depends(get_order_service)
) -> dict:
    """Get order invoice information."""
    order = await order_service.get_order(order_id, current_user_id)
    
    # Only allow invoice access for confirmed/completed orders
    if order.status not in ['confirmed', 'processing', 'shipped', 'delivered']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice not available for orders in current status"
        )
    
    return {
        "order_id": str(order.id),
        "order_number": order.order_number,
        "invoice_date": order.created_at,
        "customer": {
            "user_id": str(order.user_id)
        },
        "billing_address": order.billing_address,
        "shipping_address": order.shipping_address,
        "items": order.items,
        "summary": order.summary,
        "payment_method": order.payment_method,
        "status": order.status
    }