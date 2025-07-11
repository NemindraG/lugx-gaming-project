"""
Event ingestion endpoints for Analytics Service.
Handles structured event tracking with validation and processing.
"""

from datetime import datetime
from typing import List, Dict, Any, Union
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
import structlog

from app.clients.clickhouse_client import ClickHouseClient
from app.services.event_service import EventService
from app.schemas.events import (
    EventBatch, EventResponse, EventQuery,
    PageViewEvent, ClickEvent, ScrollEvent, SearchEvent,
    CartAddEvent, CartRemoveEvent, CartViewEvent,
    CheckoutStartEvent, CheckoutCompleteEvent, PurchaseEvent,
    UserRegisterEvent, UserLoginEvent, UserLogoutEvent,
    GameViewEvent, GameLikeEvent, ReviewSubmitEvent, WishlistAddEvent,
    FilterEvent, SortEvent, ErrorEvent, PerformanceEvent
)

router = APIRouter()
logger = structlog.get_logger()


def get_clickhouse_client(request: Request) -> ClickHouseClient:
    """Get ClickHouse client from app state."""
    return request.app.state.clickhouse_client


def get_event_service(
    clickhouse_client: ClickHouseClient = Depends(get_clickhouse_client)
) -> EventService:
    """Get event service instance."""
    return EventService(clickhouse_client)


@router.post("/batch", response_model=EventResponse)
async def ingest_event_batch(
    event_batch: EventBatch,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Ingest a batch of events for high-throughput analytics processing."""
    return await event_service.ingest_batch(event_batch)


@router.post("/pageview", response_model=EventResponse)
async def track_page_view(
    event: PageViewEvent,
    event_service: EventService = Depends(get_event_service),
    user_agent: str = Header(None, alias="User-Agent"),
    x_forwarded_for: str = Header(None, alias="X-Forwarded-For")
) -> EventResponse:
    """Track a page view event."""
    # Enrich with request headers if not provided
    if not event.user_agent and user_agent:
        event.user_agent = user_agent
    if not event.ip_address and x_forwarded_for:
        event.ip_address = x_forwarded_for.split(',')[0].strip()
    
    return await event_service.track_page_view(event)


@router.post("/click", response_model=EventResponse)
async def track_click(
    event: ClickEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track a click interaction event."""
    return await event_service.track_event(event)


@router.post("/scroll", response_model=EventResponse)
async def track_scroll(
    event: ScrollEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track a scroll depth event."""
    return await event_service.track_event(event)


@router.post("/search", response_model=EventResponse)
async def track_search(
    event: SearchEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track a search event with analytics processing."""
    return await event_service.track_search(event)


@router.post("/cart/add", response_model=EventResponse)
async def track_cart_add(
    event: CartAddEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track add to cart event."""
    return await event_service.track_cart_event(event)


@router.post("/cart/remove", response_model=EventResponse)
async def track_cart_remove(
    event: CartRemoveEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track remove from cart event."""
    return await event_service.track_cart_event(event)


@router.post("/cart/view", response_model=EventResponse)
async def track_cart_view(
    event: CartViewEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track cart view event."""
    return await event_service.track_event(event)


@router.post("/checkout/start", response_model=EventResponse)
async def track_checkout_start(
    event: CheckoutStartEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track checkout start event."""
    return await event_service.track_event(event)


@router.post("/checkout/complete", response_model=EventResponse)
async def track_checkout_complete(
    event: CheckoutCompleteEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track checkout completion event."""
    return await event_service.track_event(event)


@router.post("/purchase", response_model=EventResponse)
async def track_purchase(
    event: PurchaseEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track purchase event with revenue analytics."""
    return await event_service.track_purchase(event)


@router.post("/user/register", response_model=EventResponse)
async def track_user_register(
    event: UserRegisterEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track user registration event."""
    return await event_service.track_event(event)


@router.post("/user/login", response_model=EventResponse)
async def track_user_login(
    event: UserLoginEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track user login event."""
    return await event_service.track_event(event)


@router.post("/user/logout", response_model=EventResponse)
async def track_user_logout(
    event: UserLogoutEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track user logout event."""
    return await event_service.track_event(event)


@router.post("/game/view", response_model=EventResponse)
async def track_game_view(
    event: GameViewEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track game view event."""
    return await event_service.track_event(event)


@router.post("/game/like", response_model=EventResponse)
async def track_game_like(
    event: GameLikeEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track game like/unlike event."""
    return await event_service.track_event(event)


@router.post("/review/submit", response_model=EventResponse)
async def track_review_submit(
    event: ReviewSubmitEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track review submission event."""
    return await event_service.track_event(event)


@router.post("/wishlist/add", response_model=EventResponse)
async def track_wishlist_add(
    event: WishlistAddEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track wishlist add event."""
    return await event_service.track_event(event)


@router.post("/filter", response_model=EventResponse)
async def track_filter_apply(
    event: FilterEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track filter application event."""
    return await event_service.track_event(event)


@router.post("/sort", response_model=EventResponse)
async def track_sort_apply(
    event: SortEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track sort application event."""
    return await event_service.track_event(event)


@router.post("/error", response_model=EventResponse)
async def track_error(
    event: ErrorEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track error event."""
    return await event_service.track_event(event)


@router.post("/performance", response_model=EventResponse)
async def track_performance(
    event: PerformanceEvent,
    event_service: EventService = Depends(get_event_service)
) -> EventResponse:
    """Track performance metrics event."""
    return await event_service.track_event(event)


@router.post("/query")
async def query_events(
    query: EventQuery,
    event_service: EventService = Depends(get_event_service)
) -> List[Dict[str, Any]]:
    """Query events based on filters."""
    return await event_service.query_events(query)


@router.get("/summary")
async def get_event_summary(
    start_time: datetime,
    end_time: datetime,
    event_service: EventService = Depends(get_event_service)
) -> Dict[str, Any]:
    """Get event summary for a time period."""
    return await event_service.get_event_summary(start_time, end_time)