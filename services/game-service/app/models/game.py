"""
SQLAlchemy models for Game Service.
Implements the complete database schema with async support.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    ARRAY, Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, text, Index
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID, JSONB, TSVECTOR
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models with async support."""
    pass


class Publisher(Base):
    """Game publishers and development studios."""
    
    __tablename__ = "publishers"
    __table_args__ = {"schema": "game_service"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Relationships
    games: Mapped[List["Game"]] = relationship("Game", back_populates="publisher")

    def __repr__(self) -> str:
        return f"<Publisher(id={self.id}, name='{self.name}')>"


class Category(Base):
    """Game categories/genres with hierarchical support."""
    
    __tablename__ = "categories"
    __table_args__ = {"schema": "game_service"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon_url: Mapped[Optional[str]] = mapped_column(String(500))
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PgUUID(as_uuid=True), 
        ForeignKey("game_service.categories.id", ondelete="SET NULL")
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Self-referential relationship
    parent: Mapped[Optional["Category"]] = relationship("Category", remote_side=[id])
    children: Mapped[List["Category"]] = relationship("Category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Game(Base):
    """Main game catalog with pricing and metadata."""
    
    __tablename__ = "games"
    __table_args__ = (
        CheckConstraint("price >= 0", name="check_price_non_negative"),
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 100", name="check_discount_range"),
        CheckConstraint("metacritic_score IS NULL OR (metacritic_score >= 0 AND metacritic_score <= 100)", name="check_metacritic_range"),
        CheckConstraint(
            "(discount_percentage = 0) OR (discount_percentage > 0 AND price > 0)",
            name="price_discount_check"
        ),
        {"schema": "game_service"}
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    short_description: Mapped[Optional[str]] = mapped_column(String(500))
    publisher_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), 
        ForeignKey("game_service.publishers.id", ondelete="RESTRICT"),
        nullable=False
    )
    release_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_percentage: Mapped[int] = mapped_column(Integer, default=0)
    
    # Media
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    trailer_url: Mapped[Optional[str]] = mapped_column(String(500))
    screenshots: Mapped[Optional[List[str]]] = mapped_column(ARRAY(Text), default=list)
    
    # Metadata
    platform: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list)
    system_requirements: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    age_rating: Mapped[Optional[str]] = mapped_column(String(10))  # E, T, M, etc.
    metacritic_score: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Search optimization
    search_vector: Mapped[Optional[str]] = mapped_column(TSVECTOR)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, inactive, discontinued
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    trending_score: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Relationships
    publisher: Mapped["Publisher"] = relationship("Publisher", back_populates="games")
    categories: Mapped[List["Category"]] = relationship(
        "Category", 
        secondary="game_service.game_categories",
        back_populates=None
    )
    inventory: Mapped[List["Inventory"]] = relationship("Inventory", back_populates="game")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="game")

    @property
    def discounted_price(self) -> Decimal:
        """Calculate the discounted price."""
        if self.discount_percentage > 0:
            discount_amount = self.price * (Decimal(self.discount_percentage) / Decimal(100))
            return self.price - discount_amount
        return self.price

    @property
    def is_on_sale(self) -> bool:
        """Check if the game is currently on sale."""
        return self.discount_percentage > 0

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, title='{self.title}', price={self.price})>"


class GameCategory(Base):
    """Many-to-many relationship between games and categories."""
    
    __tablename__ = "game_categories"
    __table_args__ = (
        UniqueConstraint("game_id", name="idx_game_primary_category", postgresql_where=text("is_primary = true")),
        {"schema": "game_service"}
    )

    game_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), 
        ForeignKey("game_service.games.id", ondelete="CASCADE"),
        primary_key=True
    )
    category_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), 
        ForeignKey("game_service.categories.id", ondelete="CASCADE"),
        primary_key=True
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<GameCategory(game_id={self.game_id}, category_id={self.category_id}, primary={self.is_primary})>"


class Inventory(Base):
    """Stock management for games (digital and physical)."""
    
    __tablename__ = "inventory"
    __table_args__ = (
        CheckConstraint("quantity_available >= 0", name="check_quantity_available"),
        CheckConstraint("quantity_reserved >= 0", name="check_quantity_reserved"),
        CheckConstraint("inventory_type IN ('digital', 'physical')", name="check_inventory_type"),
        CheckConstraint("quantity_available >= quantity_reserved", name="available_reserved_check"),
        UniqueConstraint("game_id", "inventory_type"),
        {"schema": "game_service"}
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), 
        ForeignKey("game_service.games.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Stock levels
    quantity_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantity_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Digital vs Physical
    inventory_type: Mapped[str] = mapped_column(String(20), nullable=False, default="digital")
    
    # Restock information
    restock_threshold: Mapped[int] = mapped_column(Integer, default=10)
    restock_quantity: Mapped[int] = mapped_column(Integer, default=100)
    last_restocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Constraints
    low_stock_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    max_per_order: Mapped[int] = mapped_column(Integer, default=5)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="inventory")

    @property
    def is_in_stock(self) -> bool:
        """Check if item is in stock."""
        return self.quantity_available > self.quantity_reserved

    @property
    def available_quantity(self) -> int:
        """Get actually available quantity (not reserved)."""
        return max(0, self.quantity_available - self.quantity_reserved)

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, game_id={self.game_id}, type='{self.inventory_type}', available={self.available_quantity})>"


class Review(Base):
    """Customer reviews and ratings for games."""
    
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'hidden')", name="check_review_status"),
        UniqueConstraint("game_id", "user_id"),
        {"schema": "game_service"}
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    game_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), 
        ForeignKey("game_service.games.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)  # References Order Service users
    
    # Review content
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    content: Mapped[Optional[str]] = mapped_column(Text)
    
    # Review metadata
    is_verified_purchase: Mapped[bool] = mapped_column(Boolean, default=False)
    helpful_count: Mapped[int] = mapped_column(Integer, default=0)
    reported_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="pending")
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    moderated_by: Mapped[Optional[UUID]] = mapped_column(PgUUID(as_uuid=True))
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp()
    )

    # Relationships
    game: Mapped["Game"] = relationship("Game", back_populates="reviews")

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, game_id={self.game_id}, rating={self.rating}, status='{self.status}')>"


# Create indexes programmatically
__all__ = [
    "Base", 
    "Publisher", 
    "Category", 
    "Game", 
    "GameCategory", 
    "Inventory", 
    "Review"
]