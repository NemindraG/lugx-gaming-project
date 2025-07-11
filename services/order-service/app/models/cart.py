"""
Shopping cart model for Order Service.
Handles cart items, pricing, and session management.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Integer, Numeric, JSONB, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class CartItem(Base):
    """Shopping cart item model."""
    
    __tablename__ = "cart_items"
    __table_args__ = (
        Index("idx_cart_items_user_id", "user_id"),
        Index("idx_cart_items_game_id", "game_id"),
        Index("idx_cart_items_session_id", "session_id"),
        Index("idx_cart_items_expires_at", "expires_at"),
        Index("idx_cart_items_user_game", "user_id", "game_id", unique=True),
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
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,  # Can be null for guest carts
        index=True,
    )
    game_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Session management (for guest carts)
    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    
    # Cart item fields
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price at the time of adding to cart"
    )
    discount_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Discount percentage at the time of adding to cart"
    )
    
    # Product information (cached for performance)
    game_title: Mapped[str] = mapped_column(String(255), nullable=False)
    game_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    game_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    inventory_type: Mapped[str] = mapped_column(
        String(20),
        default="digital",
        nullable=False,
        comment="digital or physical"
    )
    
    # Metadata
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=dict,
        comment="Additional cart item metadata"
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
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this cart item expires (for reservation)"
    )
    
    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="cart_items")
    
    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, user_id={self.user_id}, game_id={self.game_id}, quantity={self.quantity})>"
    
    @property
    def total_price(self) -> Decimal:
        """Calculate total price for this cart item."""
        if self.discount_percentage > 0:
            discount_amount = self.unit_price * (Decimal(self.discount_percentage) / 100)
            discounted_price = self.unit_price - discount_amount
            return discounted_price * self.quantity
        return self.unit_price * self.quantity
    
    @property
    def discount_amount(self) -> Decimal:
        """Calculate discount amount for this cart item."""
        if self.discount_percentage > 0:
            return self.unit_price * (Decimal(self.discount_percentage) / 100) * self.quantity
        return Decimal("0.00")
    
    @property
    def is_expired(self) -> bool:
        """Check if cart item is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cart item to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "game_id": str(self.game_id),
            "session_id": self.session_id,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "discount_percentage": self.discount_percentage,
            "total_price": float(self.total_price),
            "discount_amount": float(self.discount_amount),
            "game_title": self.game_title,
            "game_slug": self.game_slug,
            "game_image_url": self.game_image_url,
            "inventory_type": self.inventory_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_expired": self.is_expired,
        }


class CartSession(Base):
    """Cart session model for managing guest and user cart sessions."""
    
    __tablename__ = "cart_sessions"
    __table_args__ = (
        Index("idx_cart_sessions_session_id", "session_id", unique=True),
        Index("idx_cart_sessions_user_id", "user_id"),
        Index("idx_cart_sessions_expires_at", "expires_at"),
        {"schema": "order_service"},
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    
    # Session identification
    session_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    
    # User association (optional)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    
    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Cart summary (for performance)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    
    # Session settings
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    locale: Mapped[str] = mapped_column(String(10), default="en-US", nullable=False)
    
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
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this cart session expires",
    )
    
    def __repr__(self) -> str:
        return f"<CartSession(id={self.id}, session_id={self.session_id}, user_id={self.user_id})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if cart session is expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def is_guest(self) -> bool:
        """Check if this is a guest cart session."""
        return self.user_id is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cart session to dictionary."""
        return {
            "id": str(self.id),
            "session_id": self.session_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "total_items": self.total_items,
            "total_amount": float(self.total_amount),
            "currency": self.currency,
            "locale": self.locale,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired,
            "is_guest": self.is_guest,
        }


class SavedItem(Base):
    """Saved items (wishlist) model."""
    
    __tablename__ = "saved_items"
    __table_args__ = (
        Index("idx_saved_items_user_id", "user_id"),
        Index("idx_saved_items_game_id", "game_id"),
        Index("idx_saved_items_user_game", "user_id", "game_id", unique=True),
        Index("idx_saved_items_created_at", "created_at"),
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
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    game_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Saved item fields
    game_title: Mapped[str] = mapped_column(String(255), nullable=False)
    game_slug: Mapped[str] = mapped_column(String(255), nullable=False)
    game_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    price_at_save: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Price when item was saved"
    )
    
    # Notification settings
    notify_on_sale: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_on_availability: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    target_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="User's target price for notifications"
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
    
    def __repr__(self) -> str:
        return f"<SavedItem(id={self.id}, user_id={self.user_id}, game_id={self.game_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert saved item to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "game_id": str(self.game_id),
            "game_title": self.game_title,
            "game_slug": self.game_slug,
            "game_image_url": self.game_image_url,
            "price_at_save": float(self.price_at_save),
            "notify_on_sale": self.notify_on_sale,
            "notify_on_availability": self.notify_on_availability,
            "target_price": float(self.target_price) if self.target_price else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }