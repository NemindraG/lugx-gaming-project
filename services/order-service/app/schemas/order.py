"""
Order schemas for Order Service.
Pydantic models for order operations and validation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, Enum):
    """Payment method enumeration."""
    CARD = "card"
    PAYPAL = "paypal"
    WALLET = "wallet"


class OrderItemBase(BaseModel):
    """Base order item schema."""
    game_id: UUID
    quantity: int = Field(..., ge=1, le=100)
    unit_price: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class OrderItemResponse(OrderItemBase):
    """Schema for order item responses."""
    id: UUID
    game_title: str
    game_platform: str
    game_image: Optional[str] = None
    subtotal: Decimal = Field(..., ge=0)


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    shipping_address_id: UUID
    billing_address_id: Optional[UUID] = None
    payment_method: PaymentMethod
    promo_code: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = Field(None, max_length=1000)


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[OrderStatus] = None
    tracking_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=1000)


class OrderSummary(BaseModel):
    """Schema for order summary information."""
    subtotal: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    shipping_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., ge=0)


class OrderResponse(BaseModel):
    """Schema for order responses."""
    id: UUID
    order_number: str
    user_id: UUID
    status: OrderStatus
    payment_status: PaymentStatus
    items: List[OrderItemResponse]
    summary: OrderSummary
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: PaymentMethod
    promo_code: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_delivery: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentRequest(BaseModel):
    """Schema for payment processing."""
    order_id: UUID
    payment_method: PaymentMethod
    payment_token: str = Field(..., min_length=1)
    billing_address: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """Schema for payment responses."""
    payment_id: str
    status: PaymentStatus
    amount: Decimal = Field(..., ge=0)
    currency: str = "USD"
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime


class OrderListFilter(BaseModel):
    """Schema for order list filtering."""
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class OrderStats(BaseModel):
    """Schema for order statistics."""
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: Decimal = Field(..., ge=0)
    average_order_value: Decimal = Field(..., ge=0)
