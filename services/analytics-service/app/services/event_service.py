"""
Event service for Analytics Service.
Handles event processing, validation, and business logic.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union
from uuid import uuid4

from fastapi import HTTPException, status
import structlog

from app.clients.clickhouse_client import ClickHouseClient
from app.schemas.events import (
    BaseEvent, EventBatch, EventResponse, EventQuery,
    PageViewEvent, ClickEvent, ScrollEvent, SearchEvent,
    CartAddEvent, CartRemoveEvent, CartViewEvent,
    CheckoutStartEvent, CheckoutCompleteEvent, PurchaseEvent,
    UserRegisterEvent, UserLoginEvent, UserLogoutEvent,
    GameViewEvent, GameLikeEvent, ReviewSubmitEvent, WishlistAddEvent,
    FilterEvent, SortEvent, ErrorEvent, PerformanceEvent
)

logger = structlog.get_logger()


class EventService:
    """Service for event processing and analytics."""
    
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.clickhouse = clickhouse_client
        self.batch_size = 1000
        self.flush_interval = 5  # seconds
        self._event_buffer: List[Dict[str, Any]] = []
        self._buffer_lock = asyncio.Lock()
    
    async def track_event(self, event: BaseEvent) -> EventResponse:
        """Track a single event."""
        try:
            # Validate and enrich event
            enriched_event = await self._enrich_event(event)
            
            # Generate event ID
            event_id = str(uuid4())
            enriched_event['event_id'] = event_id
            
            # Add to buffer for batch processing
            async with self._buffer_lock:
                self._event_buffer.append(enriched_event)
                
                # Flush if buffer is full
                if len(self._event_buffer) >= self.batch_size:
                    await self._flush_events()
            
            logger.info("Event tracked", 
                       event_type=event.event_type,
                       event_id=event_id,
                       user_id=str(event.user_id) if event.user_id else None)
            
            return EventResponse(
                success=True,
                message="Event tracked successfully",
                event_id=event_id
            )
            
        except Exception as e:
            logger.error("Failed to track event", 
                        event_type=event.event_type,
                        error=str(e))
            
            return EventResponse(
                success=False,
                message=f"Failed to track event: {str(e)}",
                errors=[str(e)]
            )
    
    async def track_page_view(self, event: PageViewEvent) -> EventResponse:
        """Track a page view event with additional processing."""
        # Calculate session metrics
        if event.user_id:
            await self._update_session_metrics(event.session_id, event.user_id)
        
        # Track page popularity
        await self._track_page_popularity(event.page_path)
        
        return await self.track_event(event)
    
    async def track_search(self, event: SearchEvent) -> EventResponse:
        """Track a search event with search analytics."""
        # Track popular search terms
        await self._track_search_terms(event.search_query, event.search_results_count)
        
        # Update search performance metrics
        await self._update_search_metrics(event)
        
        return await self.track_event(event)
    
    async def track_cart_event(self, event: Union[CartAddEvent, CartRemoveEvent]) -> EventResponse:
        """Track cart events with conversion funnel analytics."""
        # Update conversion funnel metrics
        await self._update_conversion_funnel(event)
        
        # Track product performance
        await self._track_product_metrics(event.game_id, event.event_type)
        
        return await self.track_event(event)
    
    async def track_purchase(self, event: PurchaseEvent) -> EventResponse:
        """Track purchase events with revenue analytics."""
        # Update revenue metrics
        await self._update_revenue_metrics(event)
        
        # Track conversion completion
        await self._track_conversion_completion(event)
        
        return await self.track_event(event)
    
    async def ingest_batch(self, event_batch: EventBatch) -> EventResponse:
        """Ingest a batch of events."""
        try:
            processed_events = []
            errors = []
            
            for event in event_batch.events:
                try:
                    # Validate and enrich each event
                    enriched_event = await self._enrich_event(event)
                    enriched_event['event_id'] = str(uuid4())
                    enriched_event['batch_id'] = event_batch.batch_id
                    processed_events.append(enriched_event)
                    
                except Exception as e:
                    error_msg = f"Failed to process event: {str(e)}"
                    errors.append(error_msg)
                    logger.error("Event processing failed", error=error_msg)
            
            # Bulk insert processed events
            if processed_events:
                await self.clickhouse.ingest_events(processed_events)
            
            logger.info("Event batch processed", 
                       batch_id=event_batch.batch_id,
                       total_events=len(event_batch.events),
                       processed=len(processed_events),
                       errors=len(errors))
            
            return EventResponse(
                success=len(errors) == 0,
                message=f"Processed {len(processed_events)} events",
                events_processed=len(processed_events),
                errors=errors
            )
            
        except Exception as e:
            logger.error("Batch ingestion failed", 
                        batch_id=event_batch.batch_id,
                        error=str(e))
            
            return EventResponse(
                success=False,
                message=f"Batch ingestion failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def query_events(self, query: EventQuery) -> List[Dict[str, Any]]:
        """Query events based on filters."""
        try:
            # Build ClickHouse query
            sql_query, params = self._build_query(query)
            
            # Execute query
            results = await self.clickhouse.execute_query(sql_query, params)
            
            logger.info("Events queried", 
                       filters=query.dict(exclude_unset=True),
                       result_count=len(results))
            
            return results
            
        except Exception as e:
            logger.error("Event query failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Query failed: {str(e)}"
            )
    
    async def get_event_summary(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get event summary for a time period."""
        try:
            query = """
            SELECT 
                event_type,
                COUNT(*) as event_count,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT session_id) as unique_sessions
            FROM events 
            WHERE timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY event_type
            ORDER BY event_count DESC
            """
            
            results = await self.clickhouse.execute_query(query, {
                'start_time': start_time,
                'end_time': end_time
            })
            
            # Calculate totals
            total_events = sum(row['event_count'] for row in results)
            total_users = len(set(row['unique_users'] for row in results))
            total_sessions = len(set(row['unique_sessions'] for row in results))
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_events': total_events,
                    'unique_users': total_users,
                    'unique_sessions': total_sessions
                },
                'events_by_type': results
            }
            
        except Exception as e:
            logger.error("Event summary failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summary generation failed: {str(e)}"
            )
    
    async def _enrich_event(self, event: BaseEvent) -> Dict[str, Any]:
        """Enrich event with additional metadata."""
        event_dict = event.dict()
        
        # Add server-side timestamp
        event_dict['server_timestamp'] = datetime.now(timezone.utc)
        
        # Detect device type from user agent if not provided
        if event.device_type == "unknown" and event.user_agent:
            event_dict['device_type'] = self._detect_device_type(event.user_agent)
        
        # Extract browser and OS info
        if event.user_agent:
            browser_info = self._parse_user_agent(event.user_agent)
            event_dict.update(browser_info)
        
        # Add geolocation if IP address is available
        if event.ip_address:
            geo_info = await self._get_geolocation(event.ip_address)
            event_dict.update(geo_info)
        
        return event_dict
    
    async def _flush_events(self):
        """Flush buffered events to ClickHouse."""
        if not self._event_buffer:
            return
        
        try:
            events_to_flush = self._event_buffer.copy()
            self._event_buffer.clear()
            
            await self.clickhouse.ingest_events(events_to_flush)
            
            logger.info("Events flushed", count=len(events_to_flush))
            
        except Exception as e:
            logger.error("Failed to flush events", error=str(e))
            # Re-add events to buffer for retry
            self._event_buffer.extend(events_to_flush)
    
    async def _update_session_metrics(self, session_id: str, user_id: Optional[str]):
        """Update session-level metrics."""
        # This would update session duration, page views, etc.
        pass
    
    async def _track_page_popularity(self, page_path: str):
        """Track page popularity metrics."""
        # This would update page view counts, popular pages, etc.
        pass
    
    async def _track_search_terms(self, query: str, results_count: int):
        """Track search term analytics."""
        # This would update popular search terms, search performance, etc.
        pass
    
    async def _update_search_metrics(self, event: SearchEvent):
        """Update search performance metrics."""
        # This would track search success rates, zero-result searches, etc.
        pass
    
    async def _update_conversion_funnel(self, event: Union[CartAddEvent, CartRemoveEvent]):
        """Update conversion funnel metrics."""
        # This would track cart abandonment, conversion rates, etc.
        pass
    
    async def _track_product_metrics(self, game_id: str, event_type: str):
        """Track product-level metrics."""
        # This would update product popularity, cart additions, etc.
        pass
    
    async def _update_revenue_metrics(self, event: PurchaseEvent):
        """Update revenue and business metrics."""
        # This would track revenue, average order value, etc.
        pass
    
    async def _track_conversion_completion(self, event: PurchaseEvent):
        """Track conversion completion metrics."""
        # This would update conversion rates, customer lifetime value, etc.
        pass
    
    def _detect_device_type(self, user_agent: str) -> str:
        """Detect device type from user agent."""
        user_agent_lower = user_agent.lower()
        
        if any(mobile in user_agent_lower for mobile in ['mobile', 'android', 'iphone']):
            return 'mobile'
        elif 'tablet' in user_agent_lower or 'ipad' in user_agent_lower:
            return 'tablet'
        else:
            return 'desktop'
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, Optional[str]]:
        """Parse browser and OS from user agent."""
        # Simplified parsing - in production you'd use a proper library
        ua_lower = user_agent.lower()
        
        browser = None
        os = None
        
        # Browser detection
        if 'chrome' in ua_lower:
            browser = 'Chrome'
        elif 'firefox' in ua_lower:
            browser = 'Firefox'
        elif 'safari' in ua_lower:
            browser = 'Safari'
        elif 'edge' in ua_lower:
            browser = 'Edge'
        
        # OS detection
        if 'windows' in ua_lower:
            os = 'Windows'
        elif 'mac' in ua_lower:
            os = 'macOS'
        elif 'linux' in ua_lower:
            os = 'Linux'
        elif 'android' in ua_lower:
            os = 'Android'
        elif 'ios' in ua_lower:
            os = 'iOS'
        
        return {'browser': browser, 'os': os}
    
    async def _get_geolocation(self, ip_address: str) -> Dict[str, Optional[str]]:
        """Get geolocation from IP address."""
        # Simplified implementation - in production you'd use a geolocation service
        return {
            'country': None,
            'region': None,
            'city': None,
            'timezone': None
        }
    
    def _build_query(self, query: EventQuery) -> tuple[str, Dict[str, Any]]:
        """Build ClickHouse SQL query from EventQuery."""
        conditions = []
        params = {}
        
        if query.event_types:
            conditions.append("event_type IN %(event_types)s")
            params['event_types'] = [et.value for et in query.event_types]
        
        if query.start_time:
            conditions.append("timestamp >= %(start_time)s")
            params['start_time'] = query.start_time
        
        if query.end_time:
            conditions.append("timestamp <= %(end_time)s")
            params['end_time'] = query.end_time
        
        if query.user_id:
            conditions.append("user_id = %(user_id)s")
            params['user_id'] = str(query.user_id)
        
        if query.session_id:
            conditions.append("session_id = %(session_id)s")
            params['session_id'] = query.session_id
        
        if query.page_url:
            conditions.append("page_url = %(page_url)s")
            params['page_url'] = query.page_url
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        sql = f"""
        SELECT * FROM events 
        {where_clause}
        ORDER BY timestamp DESC 
        LIMIT %(limit)s OFFSET %(offset)s
        """
        
        params['limit'] = query.limit
        params['offset'] = query.offset
        
        return sql, params