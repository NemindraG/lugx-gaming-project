"""
Shopping cart schemas for Order Service.
Pydantic models for cart operations and validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class CartItemBase(BaseModel):
    """Base cart item schema."""
    game_id: UUID
    quantity: int = Field(..., ge=1, le=100)
    price: Decimal = Field(..., ge=0)


class CartItemCreate(CartItemBase):
    """Schema for adding items to cart."""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart items."""
    quantity: int = Field(..., ge=1, le=100)


class CartItemResponse(CartItemBase):
    """Schema for cart item responses."""
    id: str
    game_title: str
    game_image: Optional[str] = None
    game_platform: str
    discounted_price: Optional[Decimal] = Field(None, ge=0)
    is_available: bool = True
    subtotal: Decimal = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime


class CartSummary(BaseModel):
    """Schema for cart summary information."""
    total_items: int
    total_amount: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    final_amount: Decimal = Field(..., ge=0)


class CartResponse(BaseModel):
    """Schema for complete cart response."""
    user_id: UUID
    items: List[CartItemResponse]
    summary: CartSummary
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


class BulkCartUpdate(BaseModel):
    """Schema for bulk cart operations."""
    items: List[CartItemCreate] = Field(..., min_items=1, max_items=50)
    
    @validator('items')
    def validate_unique_games(cls, v):
        """Ensure no duplicate games in bulk update."""
        game_ids = [item.game_id for item in v]
        if len(game_ids) != len(set(game_ids)):
            raise ValueError('Duplicate games not allowed in single request')
        return v


class CartCheckout(BaseModel):
    """Schema for cart checkout preparation."""
    shipping_address_id: UUID
    billing_address_id: Optional[UUID] = None
    payment_method: str = Field(..., pattern=r'^(card|paypal|wallet)$')
    promo_code: Optional[str] = Field(None, max_length=50)
    save_as_wishlist: bool = False


class PromoCode(BaseModel):
    """Schema for promo code application."""
    code: str = Field(..., max_length=50, min_length=3)


class CartTransfer(BaseModel):
    """Schema for transferring anonymous cart to user."""
    anonymous_cart_id: str = Field(..., min_length=1)


class CartStats(BaseModel):
    """Schema for cart statistics."""
    total_active_carts: int
    total_items_in_carts: int
    average_cart_value: Decimal = Field(..., ge=0)
    abandoned_carts_count: int
    conversion_rate: Decimal = Field(..., ge=0, le=1)
