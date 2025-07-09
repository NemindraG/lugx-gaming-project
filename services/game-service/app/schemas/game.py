"""
Pydantic schemas for Game Service API.
Defines request/response models with validation.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    class Config:
        from_attributes = True
        validate_assignment = True
        arbitrary_types_allowed = True


# Publisher schemas
class PublisherBase(BaseSchema):
    """Base publisher schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1900, le=2100)


class PublisherCreate(PublisherBase):
    """Schema for creating a publisher."""

    pass


class PublisherUpdate(BaseSchema):
    """Schema for updating a publisher."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(
        None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    logo_url: Optional[str] = Field(None, max_length=500)
    country: Optional[str] = Field(None, max_length=100)
    founded_year: Optional[int] = Field(None, ge=1900, le=2100)
    is_active: Optional[bool] = None


class PublisherResponse(PublisherBase):
    """Schema for publisher response."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


# Category schemas
class CategoryBase(BaseSchema):
    """Base category schema."""

    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    display_order: int = Field(0, ge=0)


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseSchema):
    """Schema for updating a category."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(
        None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$"
    )
    description: Optional[str] = None
    icon_url: Optional[str] = Field(None, max_length=500)
    parent_id: Optional[UUID] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    children: List["CategoryResponse"] = []


# Game schemas
class GameBase(BaseSchema):
    """Base game schema."""

    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    publisher_id: UUID
    release_date: Optional[date] = None
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    discount_percentage: int = Field(0, ge=0, le=100)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    trailer_url: Optional[str] = Field(None, max_length=500)
    screenshots: List[str] = Field(default_factory=list)
    platform: List[str] = Field(default_factory=list)
    system_requirements: Dict[str, Any] = Field(default_factory=dict)
    age_rating: Optional[str] = Field(None, max_length=10)
    metacritic_score: Optional[int] = Field(None, ge=0, le=100)
    featured: bool = False
    trending_score: int = Field(0, ge=0)

    @validator("platform")
    def validate_platforms(cls, v: List[str]) -> List[str]:
        """Validate platform list."""
        valid_platforms = {
            "PC",
            "PS4",
            "PS5",
            "XBOX_ONE",
            "XBOX_SERIES",
            "NINTENDO_SWITCH",
            "MOBILE",
        }
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        return v

    @validator("age_rating")
    def validate_age_rating(cls, v: Optional[str]) -> Optional[str]:
        """Validate age rating."""
        if v is not None:
            valid_ratings = {"E", "E10+", "T", "M", "AO", "RP"}
            if v not in valid_ratings:
                raise ValueError(f"Invalid age rating: {v}")
        return v

    @root_validator(pre=True)
    def validate_discount(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate discount logic."""
        price = values.get("price")
        discount = values.get("discount_percentage", 0)

        if discount > 0 and (price is None or price <= 0):
            raise ValueError("Price must be greater than 0 when discount is applied")

        return values


class GameCreate(GameBase):
    """Schema for creating a game."""

    category_ids: List[UUID] = Field(default_factory=list)
    primary_category_id: Optional[UUID] = None

    @root_validator(pre=True)
    def validate_categories(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate category assignment."""
        category_ids = values.get("category_ids", [])
        primary_category_id = values.get("primary_category_id")

        if primary_category_id and primary_category_id not in category_ids:
            raise ValueError("Primary category must be in the category list")

        return values


class GameUpdate(BaseSchema):
    """Schema for updating a game."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(
        None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$"
    )
    description: Optional[str] = None
    short_description: Optional[str] = Field(None, max_length=500)
    publisher_id: Optional[UUID] = None
    release_date: Optional[date] = None
    price: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    discount_percentage: Optional[int] = Field(None, ge=0, le=100)
    cover_image_url: Optional[str] = Field(None, max_length=500)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    trailer_url: Optional[str] = Field(None, max_length=500)
    screenshots: Optional[List[str]] = None
    platform: Optional[List[str]] = None
    system_requirements: Optional[Dict[str, Any]] = None
    age_rating: Optional[str] = Field(None, max_length=10)
    metacritic_score: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[str] = None
    featured: Optional[bool] = None
    trending_score: Optional[int] = Field(None, ge=0)
    category_ids: Optional[List[UUID]] = None
    primary_category_id: Optional[UUID] = None

    @validator("status")
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate game status."""
        if v is not None:
            valid_statuses = {"active", "inactive", "discontinued"}
            if v not in valid_statuses:
                raise ValueError(f"Invalid status: {v}")
        return v


class GameResponse(GameBase):
    """Schema for game response."""

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    discounted_price: Decimal
    is_on_sale: bool
    publisher: PublisherResponse
    categories: List[CategoryResponse] = []

    class Config(BaseSchema.Config):
        # Allow computed fields
        fields = {
            "discounted_price": {"exclude": False},
            "is_on_sale": {"exclude": False},
        }


class GameListResponse(BaseSchema):
    """Schema for game list response with pagination."""

    games: List[GameResponse]
    total: int
    page: int
    per_page: int
    pages: int


# Inventory schemas
class InventoryBase(BaseSchema):
    """Base inventory schema."""

    game_id: UUID
    quantity_available: int = Field(0, ge=0)
    quantity_reserved: int = Field(0, ge=0)
    inventory_type: str = Field("digital")
    restock_threshold: int = Field(10, ge=0)
    restock_quantity: int = Field(100, ge=1)
    max_per_order: int = Field(5, ge=1)

    @validator("inventory_type")
    def validate_inventory_type(cls, v: str) -> str:
        """Validate inventory type."""
        valid_types = {"digital", "physical"}
        if v not in valid_types:
            raise ValueError(f"Invalid inventory type: {v}")
        return v

    @root_validator(pre=True)
    def validate_quantities(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quantity logic."""
        available = values.get("quantity_available", 0)
        reserved = values.get("quantity_reserved", 0)

        if available < reserved:
            raise ValueError("Available quantity cannot be less than reserved quantity")

        return values


class InventoryCreate(InventoryBase):
    """Schema for creating inventory."""

    pass


class InventoryUpdate(BaseSchema):
    """Schema for updating inventory."""

    quantity_available: Optional[int] = Field(None, ge=0)
    quantity_reserved: Optional[int] = Field(None, ge=0)
    restock_threshold: Optional[int] = Field(None, ge=0)
    restock_quantity: Optional[int] = Field(None, ge=1)
    max_per_order: Optional[int] = Field(None, ge=1)
    low_stock_alert: Optional[bool] = None


class InventoryResponse(InventoryBase):
    """Schema for inventory response."""

    id: UUID
    low_stock_alert: bool
    last_restocked_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    is_in_stock: bool
    available_quantity: int

    class Config(BaseSchema.Config):
        # Allow computed fields
        fields = {
            "is_in_stock": {"exclude": False},
            "available_quantity": {"exclude": False},
        }


# Review schemas
class ReviewBase(BaseSchema):
    """Base review schema."""

    game_id: UUID
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""

    user_id: UUID


class ReviewUpdate(BaseSchema):
    """Schema for updating a review."""

    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None


class ReviewResponse(ReviewBase):
    """Schema for review response."""

    id: UUID
    user_id: UUID
    is_verified_purchase: bool
    helpful_count: int
    reported_count: int
    status: str
    moderated_at: Optional[datetime]
    moderated_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseSchema):
    """Schema for review list response with pagination."""

    reviews: List[ReviewResponse]
    total: int
    page: int
    per_page: int
    pages: int
    average_rating: float
    rating_distribution: Dict[int, int]  # {1: count, 2: count, ...}


# Search and filter schemas
class GameSearchRequest(BaseSchema):
    """Schema for game search request."""

    query: Optional[str] = None
    category_ids: Optional[List[UUID]] = None
    publisher_ids: Optional[List[UUID]] = None
    platforms: Optional[List[str]] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    age_ratings: Optional[List[str]] = None
    featured_only: bool = False
    on_sale_only: bool = False
    in_stock_only: bool = True
    sort_by: str = Field(
        "created_at",
        pattern=r"^(title|price|release_date|created_at|rating|trending_score)$",
    )
    sort_order: str = Field("desc", pattern=r"^(asc|desc)$")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

    @root_validator(pre=True)
    def validate_price_range(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Validate price range."""
        min_price = values.get("min_price")
        max_price = values.get("max_price")

        if min_price and max_price and min_price > max_price:
            raise ValueError("min_price cannot be greater than max_price")

        return values


# Health check schema
class HealthCheckResponse(BaseSchema):
    """Schema for health check response."""

    status: str
    service: str = "game-service"
    version: str
    database: Dict[str, Any]
    dependencies: Dict[str, Any]


# Update forward references
CategoryResponse.model_rebuild()

__all__ = [
    "PublisherCreate",
    "PublisherUpdate",
    "PublisherResponse",
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "GameCreate",
    "GameUpdate",
    "GameResponse",
    "GameListResponse",
    "InventoryCreate",
    "InventoryUpdate",
    "InventoryResponse",
    "ReviewCreate",
    "ReviewUpdate",
    "ReviewResponse",
    "ReviewListResponse",
    "GameSearchRequest",
    "HealthCheckResponse",
]
