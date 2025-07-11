"""
Event schemas for Analytics Service.
Pydantic models for different event types and validation.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Event type enumeration."""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    SCROLL = "scroll"
    SEARCH = "search"
    CART_ADD = "cart_add"
    CART_REMOVE = "cart_remove"
    CART_VIEW = "cart_view"
    CHECKOUT_START = "checkout_start"
    CHECKOUT_COMPLETE = "checkout_complete"
    PURCHASE = "purchase"
    USER_REGISTER = "user_register"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    GAME_VIEW = "game_view"
    GAME_LIKE = "game_like"
    REVIEW_SUBMIT = "review_submit"
    WISHLIST_ADD = "wishlist_add"
    FILTER_APPLY = "filter_apply"
    SORT_APPLY = "sort_apply"
    ERROR = "error"
    PERFORMANCE = "performance"


class DeviceType(str, Enum):
    """Device type enumeration."""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


class BaseEvent(BaseModel):
    """Base event schema with common fields."""
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str = Field(..., min_length=1, max_length=255)
    user_id: Optional[UUID] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=1000)
    page_url: Optional[str] = Field(None, max_length=2000)
    referrer: Optional[str] = Field(None, max_length=2000)
    device_type: DeviceType = DeviceType.UNKNOWN
    browser: Optional[str] = Field(None, max_length=100)
    os: Optional[str] = Field(None, max_length=100)
    screen_width: Optional[int] = Field(None, ge=0, le=10000)
    screen_height: Optional[int] = Field(None, ge=0, le=10000)
    properties: Dict[str, Any] = Field(default_factory=dict)


class PageViewEvent(BaseEvent):
    """Page view event schema."""
    event_type: EventType = EventType.PAGE_VIEW
    page_title: str = Field(..., max_length=500)
    page_path: str = Field(..., max_length=1000)
    load_time: Optional[float] = Field(None, ge=0)
    previous_page: Optional[str] = Field(None, max_length=1000)


class ClickEvent(BaseEvent):
    """Click event schema."""
    event_type: EventType = EventType.CLICK
    element_id: Optional[str] = Field(None, max_length=255)
    element_class: Optional[str] = Field(None, max_length=255)
    element_text: Optional[str] = Field(None, max_length=500)
    element_tag: Optional[str] = Field(None, max_length=50)
    click_x: Optional[int] = Field(None, ge=0)
    click_y: Optional[int] = Field(None, ge=0)
    target_url: Optional[str] = Field(None, max_length=2000)


class ScrollEvent(BaseEvent):
    """Scroll event schema."""
    event_type: EventType = EventType.SCROLL
    scroll_depth: int = Field(..., ge=0, le=100)  # Percentage
    max_scroll_depth: int = Field(..., ge=0, le=100)
    time_on_page: float = Field(..., ge=0)
    page_height: Optional[int] = Field(None, ge=0)


class SearchEvent(BaseEvent):
    """Search event schema."""
    event_type: EventType = EventType.SEARCH
    search_query: str = Field(..., min_length=1, max_length=500)
    search_results_count: int = Field(..., ge=0)
    search_category: Optional[str] = Field(None, max_length=100)
    filters_applied: Optional[List[str]] = Field(default_factory=list)
    sort_order: Optional[str] = Field(None, max_length=50)


class CartEvent(BaseEvent):
    """Shopping cart event schema."""
    game_id: UUID
    game_title: str = Field(..., max_length=255)
    game_price: float = Field(..., ge=0)
    quantity: int = Field(..., ge=1)
    cart_total_items: int = Field(..., ge=0)
    cart_total_value: float = Field(..., ge=0)


class CartAddEvent(CartEvent):
    """Add to cart event schema."""
    event_type: EventType = EventType.CART_ADD


class CartRemoveEvent(CartEvent):
    """Remove from cart event schema."""
    event_type: EventType = EventType.CART_REMOVE


class CartViewEvent(BaseEvent):
    """Cart view event schema."""
    event_type: EventType = EventType.CART_VIEW
    cart_total_items: int = Field(..., ge=0)
    cart_total_value: float = Field(..., ge=0)
    cart_items: List[Dict[str, Any]] = Field(default_factory=list)


class CheckoutEvent(BaseEvent):
    """Checkout event schema."""
    order_id: Optional[UUID] = None
    total_amount: float = Field(..., ge=0)
    item_count: int = Field(..., ge=0)
    payment_method: Optional[str] = Field(None, max_length=50)
    discount_amount: float = Field(default=0.0, ge=0)
    shipping_amount: float = Field(default=0.0, ge=0)
    tax_amount: float = Field(default=0.0, ge=0)


class CheckoutStartEvent(CheckoutEvent):
    """Checkout start event schema."""
    event_type: EventType = EventType.CHECKOUT_START


class CheckoutCompleteEvent(CheckoutEvent):
    """Checkout complete event schema."""
    event_type: EventType = EventType.CHECKOUT_COMPLETE
    order_id: UUID


class PurchaseEvent(BaseEvent):
    """Purchase event schema."""
    event_type: EventType = EventType.PURCHASE
    order_id: UUID
    transaction_id: str = Field(..., max_length=255)
    total_amount: float = Field(..., ge=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: str = Field(..., max_length=50)
    items: List[Dict[str, Any]] = Field(..., min_items=1)


class UserEvent(BaseEvent):
    """User authentication event schema."""
    user_email: Optional[str] = Field(None, max_length=255)
    registration_source: Optional[str] = Field(None, max_length=100)


class UserRegisterEvent(UserEvent):
    """User registration event schema."""
    event_type: EventType = EventType.USER_REGISTER
    user_id: UUID


class UserLoginEvent(UserEvent):
    """User login event schema."""
    event_type: EventType = EventType.USER_LOGIN
    user_id: UUID
    login_method: Optional[str] = Field(None, max_length=50)


class UserLogoutEvent(UserEvent):
    """User logout event schema."""
    event_type: EventType = EventType.USER_LOGOUT
    user_id: UUID
    session_duration: Optional[float] = Field(None, ge=0)


class GameEvent(BaseEvent):
    """Game interaction event schema."""
    game_id: UUID
    game_title: str = Field(..., max_length=255)
    game_category: Optional[str] = Field(None, max_length=100)
    game_price: Optional[float] = Field(None, ge=0)


class GameViewEvent(GameEvent):
    """Game view event schema."""
    event_type: EventType = EventType.GAME_VIEW
    view_duration: Optional[float] = Field(None, ge=0)
    came_from: Optional[str] = Field(None, max_length=255)


class GameLikeEvent(GameEvent):
    """Game like event schema."""
    event_type: EventType = EventType.GAME_LIKE
    is_like: bool = True  # True for like, False for unlike


class ReviewSubmitEvent(GameEvent):
    """Review submission event schema."""
    event_type: EventType = EventType.REVIEW_SUBMIT
    rating: int = Field(..., ge=1, le=5)
    review_length: int = Field(..., ge=0)


class WishlistAddEvent(GameEvent):
    """Wishlist add event schema."""
    event_type: EventType = EventType.WISHLIST_ADD


class FilterEvent(BaseEvent):
    """Filter application event schema."""
    event_type: EventType = EventType.FILTER_APPLY
    filter_type: str = Field(..., max_length=100)
    filter_value: str = Field(..., max_length=255)
    results_count: int = Field(..., ge=0)


class SortEvent(BaseEvent):
    """Sort application event schema."""
    event_type: EventType = EventType.SORT_APPLY
    sort_field: str = Field(..., max_length=100)
    sort_direction: str = Field(..., pattern=r"^(asc|desc)$")
    results_count: int = Field(..., ge=0)


class ErrorEvent(BaseEvent):
    """Error event schema."""
    event_type: EventType = EventType.ERROR
    error_message: str = Field(..., max_length=1000)
    error_code: Optional[str] = Field(None, max_length=100)
    error_stack: Optional[str] = Field(None, max_length=5000)
    component: Optional[str] = Field(None, max_length=255)


class PerformanceEvent(BaseEvent):
    """Performance event schema."""
    event_type: EventType = EventType.PERFORMANCE
    metric_name: str = Field(..., max_length=100)
    metric_value: float = Field(..., ge=0)
    metric_unit: str = Field(..., max_length=20)
    page_load_time: Optional[float] = Field(None, ge=0)
    dom_content_loaded: Optional[float] = Field(None, ge=0)
    first_contentful_paint: Optional[float] = Field(None, ge=0)


class EventBatch(BaseModel):
    """Batch of events for bulk ingestion."""
    events: List[Union[
        PageViewEvent, ClickEvent, ScrollEvent, SearchEvent,
        CartAddEvent, CartRemoveEvent, CartViewEvent,
        CheckoutStartEvent, CheckoutCompleteEvent, PurchaseEvent,
        UserRegisterEvent, UserLoginEvent, UserLogoutEvent,
        GameViewEvent, GameLikeEvent, ReviewSubmitEvent, WishlistAddEvent,
        FilterEvent, SortEvent, ErrorEvent, PerformanceEvent
    ]] = Field(..., min_items=1, max_items=1000)
    batch_id: Optional[str] = Field(None, max_length=255)
    source: Optional[str] = Field(None, max_length=100)


class EventResponse(BaseModel):
    """Response schema for event ingestion."""
    success: bool
    message: str
    event_id: Optional[str] = None
    events_processed: Optional[int] = None
    errors: Optional[List[str]] = Field(default_factory=list)


class EventQuery(BaseModel):
    """Schema for event querying."""
    event_types: Optional[List[EventType]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    user_id: Optional[UUID] = None
    session_id: Optional[str] = None
    page_url: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)