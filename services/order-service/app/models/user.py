"""
User model for Order Service.
Handles user authentication, profile management, and preferences.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, DateTime, String, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """User model for authentication and profile management."""
    
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email", unique=True),
        Index("idx_users_username", "username", unique=True),
        Index("idx_users_created_at", "created_at"),
        Index("idx_users_last_login", "last_login_at"),
        {"schema": "order_service"},
    )
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    
    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Preferences and settings
    preferences: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)
    notification_settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, default=dict)
    
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
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Security fields
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255))
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    email_verification_expires: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Relationships
    addresses: Mapped[List["UserAddress"]] = relationship(
        "UserAddress", back_populates="user", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem", back_populates="user", cascade="all, delete-orphan"
    )
    reviews: Mapped[List["UserReview"]] = relationship(
        "UserReview", back_populates="user", cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def is_locked(self) -> bool:
        """Check if user account is locked."""
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding sensitive fields)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "preferences": self.preferences,
            "notification_settings": self.notification_settings,
        }


class UserAddress(Base):
    """User address model for shipping and billing."""
    
    __tablename__ = "user_addresses"
    __table_args__ = (
        Index("idx_user_addresses_user_id", "user_id"),
        Index("idx_user_addresses_is_default", "is_default_shipping", "is_default_billing"),
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
    
    # Address fields
    address_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'shipping', 'billing', 'both'
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(100))
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state_province: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Flags
    is_default_shipping: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default_billing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
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
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    
    def __repr__(self) -> str:
        return f"<UserAddress(id={self.id}, user_id={self.user_id}, type={self.address_type})>"
    
    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        address_parts = [
            self.address_line_1,
            self.address_line_2,
            f"{self.city}, {self.state_province} {self.postal_code}",
            self.country,
        ]
        return ", ".join(filter(None, address_parts))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert address to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "address_type": self.address_type,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "company": self.company,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city": self.city,
            "state_province": self.state_province,
            "postal_code": self.postal_code,
            "country": self.country,
            "phone": self.phone,
            "is_default_shipping": self.is_default_shipping,
            "is_default_billing": self.is_default_billing,
            "full_address": self.full_address,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class UserReview(Base):
    """User review model for games (sync with Game Service)."""
    
    __tablename__ = "user_reviews"
    __table_args__ = (
        Index("idx_user_reviews_user_id", "user_id"),
        Index("idx_user_reviews_game_id", "game_id"),
        Index("idx_user_reviews_rating", "rating"),
        Index("idx_user_reviews_created_at", "created_at"),
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
    
    # Review fields
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    title: Mapped[Optional[str]] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    
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
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    
    def __repr__(self) -> str:
        return f"<UserReview(id={self.id}, user_id={self.user_id}, game_id={self.game_id}, rating={self.rating})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert review to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "game_id": str(self.game_id),
            "rating": self.rating,
            "title": self.title,
            "content": self.content,
            "is_verified_purchase": self.is_verified_purchase,
            "helpful_count": self.helpful_count,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }