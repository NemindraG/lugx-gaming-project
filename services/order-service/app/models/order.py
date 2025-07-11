"""
Order model for Order Service.
Handles order processing, payments, and order history.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Integer, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Order(Base):
    """Order model for purchase transactions."""
    
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_order_number", "order_number", unique=True),
        Index("idx_orders_status", "status"),
        Index("idx_orders_created_at", "created_at"),
        Index("idx_orders_total_amount", "total_amount"),
        {"schema": "order_service"},
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Order identification
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Human-readable order number"
    )
    
    # Order status
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="pending, confirmed, processing, shipped, delivered, cancelled, refunded"
    )
    
    # Financial information
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Subtotal before tax and fees"
    )
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Final total amount"
    )
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Customer information
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Shipping address
    shipping_address: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Complete shipping address information"
    )
    
    # Billing address
    billing_address: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Complete billing address information"
    )
    
    # Payment information
    payment_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="credit_card, paypal, bank_transfer, etc."
    )
    payment_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending, authorized, captured, failed, refunded"
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="External payment system reference"
    )
    
    # Order metadata
    notes: Mapped[Optional[str]] = mapped_column(Text)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=dict,
        comment="Additional order metadata"
    )
    
    # Fulfillment information
    fulfillment_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending, processing, shipped, delivered, cancelled"
    )
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    shipping_carrier: Mapped[Optional[str]] = mapped_column(String(50))
    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    actual_delivery: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    shipped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"
    
    @property
    def is_cancellable(self) -> bool:
        """Check if order can be cancelled."""
        return self.status in ["pending", "confirmed"] and self.payment_status != "captured"
    
    @property
    def is_refundable(self) -> bool:
        """Check if order can be refunded."""
        return self.payment_status == "captured" and self.status not in ["cancelled", "refunded"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "order_number": self.order_number,
            "status": self.status,
            "subtotal": float(self.subtotal),
            "tax_amount": float(self.tax_amount),
            "shipping_amount": float(self.shipping_amount),
            "discount_amount": float(self.discount_amount),
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "shipping_address": self.shipping_address,
            "billing_address": self.billing_address,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "payment_reference": self.payment_reference,
            "notes": self.notes,
            "admin_notes": self.admin_notes,
            "metadata": self.metadata,
            "fulfillment_status": self.fulfillment_status,
            "tracking_number": self.tracking_number,
            "shipping_carrier": self.shipping_carrier,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "actual_delivery": self.actual_delivery.isoformat() if self.actual_delivery else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "is_cancellable": self.is_cancellable,
            "is_refundable": self.is_refundable,
        }


class OrderItem(Base):
    """Order item model for individual products in an order."""
    
    __tablename__ = "order_items"
    __table_args__ = (
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_game_id", "game_id"),
        Index("idx_order_items_sku", "sku"),
        {"schema": "order_service"},
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign keys
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    game_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Product information (snapshot at time of order)
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    game_title: Mapped[str] = mapped_column(String(255), nullable=False)
    game_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    game_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Pricing information
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Unit price at time of order"
    )
    discount_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Discount percentage applied"
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    total_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Total price for this line item"
    )
    
    # Product details
    inventory_type: Mapped[str] = mapped_column(
        String(20),
        default="digital",
        nullable=False,
        comment="digital or physical"
    )
    license_key: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Digital license key for digital products"
    )
    
    # Fulfillment status
    fulfillment_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment="pending, processing, fulfilled, cancelled"
    )
    
    # Metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=dict,
        comment="Additional item metadata"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    fulfilled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    
    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, game_id={self.game_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order item to dictionary."""
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "game_id": str(self.game_id),
            "sku": self.sku,
            "game_title": self.game_title,
            "game_slug": self.game_slug,
            "game_image_url": self.game_image_url,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "discount_percentage": self.discount_percentage,
            "discount_amount": float(self.discount_amount),
            "total_price": float(self.total_price),
            "inventory_type": self.inventory_type,
            "license_key": self.license_key,
            "fulfillment_status": self.fulfillment_status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "fulfilled_at": self.fulfilled_at.isoformat() if self.fulfilled_at else None,
        }


class PaymentTransaction(Base):
    """Payment transaction model for tracking payment attempts."""
    
    __tablename__ = "payment_transactions"
    __table_args__ = (
        Index("idx_payment_transactions_order_id", "order_id"),
        Index("idx_payment_transactions_transaction_id", "transaction_id", unique=True),
        Index("idx_payment_transactions_status", "status"),
        Index("idx_payment_transactions_created_at", "created_at"),
        {"schema": "order_service"},
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign key
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Transaction identification
    transaction_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique transaction identifier"
    )
    
    # Payment details
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_processor: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    
    # Transaction status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="pending, authorized, captured, failed, cancelled, refunded"
    )
    
    # External references
    external_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        comment="Payment processor transaction ID"
    )
    authorization_code: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Response data
    processor_response: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        comment="Full response from payment processor"
    )
    
    # Error information
    error_code: Mapped[Optional[str]] = mapped_column(String(100))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    def __repr__(self) -> str:
        return f"<PaymentTransaction(id={self.id}, transaction_id={self.transaction_id}, status={self.status})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert payment transaction to dictionary."""
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "transaction_id": self.transaction_id,
            "payment_method": self.payment_method,
            "payment_processor": self.payment_processor,
            "amount": float(self.amount),
            "currency": self.currency,
            "status": self.status,
            "external_transaction_id": self.external_transaction_id,
            "authorization_code": self.authorization_code,
            "processor_response": self.processor_response,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }