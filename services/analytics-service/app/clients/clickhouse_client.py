"""
ClickHouse Async Client for Analytics Service
High-performance client optimized for web analytics and real-time data processing.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import aiohttp
import asyncio_mqtt
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class WebEvent(BaseModel):
    """Web analytics event model."""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str
    user_id: Optional[str] = None
    
    # Page tracking
    page_url: str
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    
    # User interactions
    element_type: Optional[str] = None
    element_text: Optional[str] = None
    element_id: Optional[str] = None
    click_x: Optional[int] = None
    click_y: Optional[int] = None
    
    # Scroll tracking
    scroll_depth: Optional[int] = None
    max_scroll: Optional[int] = None
    page_height: Optional[int] = None
    
    # E-commerce specific
    product_id: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    
    # Device/browser context
    user_agent: str
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    
    # Custom properties
    properties: Dict[str, Any] = Field(default_factory=dict)


class ClickHouseClient:
    """
    High-performance async ClickHouse client for web analytics.
    Optimized for high-volume event ingestion and real-time queries.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        database: str = "lugx_analytics",
        user: str = "analytics_service",
        password: str = "analytics_secure_password_2024",
        batch_size: int = 1000,
        flush_interval: int = 30
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self.base_url = f"http://{host}:{port}"
        self.auth = aiohttp.BasicAuth(user, password)
        
        # Event batching
        self._event_buffer: List[WebEvent] = []
        self._buffer_lock = asyncio.Lock()
        self._flush_task: Optional[asyncio.Task] = None
        
        # Connection management
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector = aiohttp.TCPConnector(
            limit=100,  # Max connections
            limit_per_host=50,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Initialize connection and start background tasks."""
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            auth=self.auth,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Test connection
        await self.ping()
        
        # Start background flush task
        self._flush_task = asyncio.create_task(self._background_flush())
        
        logger.info(f"Connected to ClickHouse at {self.host}:{self.port}")
    
    async def close(self):
        """Clean up resources."""
        # Cancel background task
        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Flush remaining events
        await self.flush_events()
        
        # Close session
        if self._session and not self._session.closed:
            await self._session.close()
        
        await self._connector.close()
        logger.info("ClickHouse client closed")
    
    async def ping(self) -> bool:
        """Test connection to ClickHouse."""
        try:
            async with self._session.get(f"{self.base_url}/ping") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"ClickHouse ping failed: {e}")
            return False
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results."""
        try:
            data = {
                'query': query,
                'default_format': 'JSONEachRow'
            }
            
            if params:
                data.update(params)
            
            async with self._session.post(
                f"{self.base_url}/",
                data=data
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    if content.strip():
                        return [json.loads(line) for line in content.strip().split('\n')]
                    return []
                else:
                    error_text = await response.text()
                    raise Exception(f"Query failed: {error_text}")
        
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def track_event(self, event: WebEvent):
        """Track a single web event (adds to batch)."""
        async with self._buffer_lock:
            self._event_buffer.append(event)
            
            # Flush immediately if buffer is full
            if len(self._event_buffer) >= self.batch_size:
                await self._flush_events_unsafe()
    
    async def batch_insert_events(self, events: List[WebEvent]) -> bool:
        """Batch insert web events with validation and error handling."""
        if not events:
            return True
        
        try:
            # Prepare data for insertion
            rows = []
            for event in events:
                row = {
                    'event_id': event.event_id,
                    'event_type': event.event_type,
                    'timestamp': event.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                    'session_id': event.session_id,
                    'user_id': event.user_id or '',
                    'page_url': event.page_url,
                    'page_title': event.page_title or '',
                    'referrer': event.referrer or '',
                    'element_type': event.element_type or '',
                    'element_text': event.element_text or '',
                    'element_id': event.element_id or '',
                    'click_x': event.click_x or 0,
                    'click_y': event.click_y or 0,
                    'scroll_depth': event.scroll_depth or 0,
                    'max_scroll': event.max_scroll or 0,
                    'page_height': event.page_height or 0,
                    'product_id': event.product_id or '',
                    'category': event.category or '',
                    'price': event.price or 0.0,
                    'user_agent': event.user_agent,
                    'screen_width': event.screen_width or 0,
                    'screen_height': event.screen_height or 0,
                    'viewport_width': event.viewport_width or 0,
                    'viewport_height': event.viewport_height or 0,
                    'properties': json.dumps(event.properties)
                }
                rows.append(row)
            
            # Create INSERT query
            query = f"""
                INSERT INTO {self.database}.web_events FORMAT JSONEachRow
            """
            
            # Prepare data
            data = '\n'.join(json.dumps(row) for row in rows)
            
            async with self._session.post(
                f"{self.base_url}/",
                data=query + '\n' + data,
                headers={'Content-Type': 'text/plain'}
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully inserted {len(events)} events")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Batch insert failed: {error_text}")
                    return False
        
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return False
    
    async def get_real_time_metrics(self, time_window: str = "1h") -> Dict:
        """Get real-time analytics for dashboards."""
        try:
            # Parse time window
            if time_window.endswith('h'):
                hours = int(time_window[:-1])
                start_time = datetime.utcnow() - timedelta(hours=hours)
            elif time_window.endswith('m'):
                minutes = int(time_window[:-1])
                start_time = datetime.utcnow() - timedelta(minutes=minutes)
            else:
                start_time = datetime.utcnow() - timedelta(hours=1)
            
            query = f"""
                SELECT
                    count() as total_events,
                    uniq(session_id) as unique_sessions,
                    uniq(user_id) as unique_users,
                    countIf(event_type = 'page_view') as page_views,
                    countIf(event_type = 'click') as clicks,
                    avgIf(scroll_depth, event_type = 'scroll') as avg_scroll_depth,
                    topK(5)(page_url) as top_pages
                FROM {self.database}.web_events
                WHERE timestamp >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
            """
            
            results = await self.execute_query(query)
            return results[0] if results else {}
        
        except Exception as e:
            logger.error(f"Real-time metrics query failed: {e}")
            return {}
    
    async def track_conversion_funnel(self, funnel_steps: List[str]) -> Dict:
        """Analyze conversion rates through funnel steps."""
        try:
            # Build funnel query
            funnel_conditions = []
            for i, step in enumerate(funnel_steps):
                funnel_conditions.append(f"event_type = '{step}'")
            
            query = f"""
                SELECT
                    {', '.join(f"countIf({cond}) as step_{i+1}" for i, cond in enumerate(funnel_conditions))},
                    {', '.join(f"step_{i+1}/step_1*100 as conversion_rate_{i+1}" for i in range(1, len(funnel_steps)))}
                FROM {self.database}.web_events
                WHERE timestamp >= now() - INTERVAL 24 HOUR
                GROUP BY session_id
            """
            
            results = await self.execute_query(query)
            return results[0] if results else {}
        
        except Exception as e:
            logger.error(f"Funnel analysis failed: {e}")
            return {}
    
    async def get_user_journey(self, session_id: str) -> List[Dict]:
        """Reconstruct complete user journey for session."""
        try:
            query = f"""
                SELECT
                    event_type,
                    timestamp,
                    page_url,
                    element_type,
                    element_text,
                    properties
                FROM {self.database}.web_events
                WHERE session_id = '{session_id}'
                ORDER BY timestamp ASC
            """
            
            return await self.execute_query(query)
        
        except Exception as e:
            logger.error(f"User journey query failed: {e}")
            return []
    
    async def get_popular_content(self, limit: int = 10) -> List[Dict]:
        """Get trending games and pages."""
        try:
            query = f"""
                SELECT
                    page_url,
                    count() as views,
                    uniq(session_id) as unique_visitors,
                    avgIf(scroll_depth, scroll_depth > 0) as avg_engagement
                FROM {self.database}.web_events
                WHERE event_type = 'page_view'
                  AND timestamp >= now() - INTERVAL 24 HOUR
                GROUP BY page_url
                ORDER BY views DESC
                LIMIT {limit}
            """
            
            return await self.execute_query(query)
        
        except Exception as e:
            logger.error(f"Popular content query failed: {e}")
            return []
    
    async def get_user_engagement_metrics(self) -> Dict:
        """Get user engagement and session metrics."""
        try:
            query = f"""
                SELECT
                    avg(session_duration) as avg_session_duration,
                    avg(page_views_per_session) as avg_page_views,
                    avg(max_scroll_depth) as avg_scroll_depth,
                    count(distinct user_id) as daily_active_users,
                    count(distinct session_id) as total_sessions
                FROM (
                    SELECT
                        session_id,
                        user_id,
                        max(timestamp) - min(timestamp) as session_duration,
                        countIf(event_type = 'page_view') as page_views_per_session,
                        max(scroll_depth) as max_scroll_depth
                    FROM {self.database}.web_events
                    WHERE timestamp >= now() - INTERVAL 24 HOUR
                    GROUP BY session_id, user_id
                )
            """
            
            results = await self.execute_query(query)
            return results[0] if results else {}
        
        except Exception as e:
            logger.error(f"Engagement metrics query failed: {e}")
            return {}
    
    async def flush_events(self):
        """Manually flush all buffered events."""
        async with self._buffer_lock:
            await self._flush_events_unsafe()
    
    async def _flush_events_unsafe(self):
        """Internal method to flush events (no lock)."""
        if not self._event_buffer:
            return
        
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()
        
        await self.batch_insert_events(events_to_flush)
    
    async def _background_flush(self):
        """Background task to periodically flush events."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush_events()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background flush failed: {e}")
    
    async def create_materialized_view(self, view_name: str, query: str):
        """Create a materialized view for optimized queries."""
        try:
            create_query = f"""
                CREATE MATERIALIZED VIEW IF NOT EXISTS {self.database}.{view_name}
                ENGINE = SummingMergeTree()
                ORDER BY tuple()
                AS {query}
            """
            
            await self.execute_query(create_query)
            logger.info(f"Materialized view {view_name} created successfully")
        
        except Exception as e:
            logger.error(f"Failed to create materialized view {view_name}: {e}")
            raise
    
    async def setup_analytics_views(self):
        """Set up standard analytics materialized views."""
        # Hourly page views
        await self.create_materialized_view(
            "hourly_page_views",
            """
            SELECT
                toStartOfHour(timestamp) as hour,
                page_url,
                count() as views,
                uniq(session_id) as unique_visitors
            FROM web_events
            WHERE event_type = 'page_view'
            GROUP BY hour, page_url
            """
        )
        
        # Real-time active users
        await self.create_materialized_view(
            "active_users_1m",
            """
            SELECT
                toStartOfMinute(timestamp) as minute,
                uniq(user_id) as active_users,
                uniq(session_id) as active_sessions
            FROM web_events
            GROUP BY minute
            """
        )
        
        # Conversion funnel data
        await self.create_materialized_view(
            "conversion_events",
            """
            SELECT
                toDate(timestamp) as date,
                session_id,
                user_id,
                event_type,
                page_url,
                product_id
            FROM web_events
            WHERE event_type IN ('page_view', 'product_view', 'add_to_cart', 'purchase')
            """
        )


# Factory function for easy client creation
async def create_clickhouse_client(
    host: str = "localhost",
    port: int = 8123,
    database: str = "lugx_analytics",
    user: str = "analytics_service",
    password: str = "analytics_secure_password_2024",
    **kwargs
) -> ClickHouseClient:
    """Create and initialize a ClickHouse client."""
    client = ClickHouseClient(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password,
        **kwargs
    )
    await client.connect()
    return client