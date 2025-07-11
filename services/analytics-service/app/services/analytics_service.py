"""
Analytics service for real-time calculations and business intelligence.
Handles complex analytics queries and metric computations using ClickHouse.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal

from fastapi import HTTPException, status
import structlog

from app.clients.clickhouse_client import ClickHouseClient

logger = structlog.get_logger()


class AnalyticsService:
    """Service for real-time analytics and business intelligence."""
    
    def __init__(self, clickhouse_client: ClickHouseClient):
        self.clickhouse = clickhouse_client
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time platform metrics."""
        try:
            # Current timestamp
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)
            
            # Concurrent queries for better performance
            current_users_query = """
            SELECT COUNT(DISTINCT session_id) as active_sessions
            FROM events 
            WHERE timestamp >= %(hour_ago)s
            """
            
            page_views_query = """
            SELECT COUNT(*) as page_views
            FROM events 
            WHERE event_type = 'page_view' 
            AND timestamp >= %(hour_ago)s
            """
            
            revenue_query = """
            SELECT 
                COUNT(*) as orders_count,
                SUM(total_amount) as total_revenue
            FROM events 
            WHERE event_type = 'purchase' 
            AND timestamp >= %(day_ago)s
            """
            
            conversion_query = """
            SELECT 
                COUNT(DISTINCT session_id) as checkout_sessions,
                COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) as purchase_sessions
            FROM events 
            WHERE event_type IN ('checkout_start', 'purchase')
            AND timestamp >= %(day_ago)s
            """
            
            # Execute queries
            params = {'hour_ago': hour_ago, 'day_ago': day_ago}
            
            current_users = await self.clickhouse.execute_query(current_users_query, params)
            page_views = await self.clickhouse.execute_query(page_views_query, params)
            revenue = await self.clickhouse.execute_query(revenue_query, params)
            conversion = await self.clickhouse.execute_query(conversion_query, params)
            
            # Calculate conversion rate
            checkout_sessions = conversion[0]['checkout_sessions'] if conversion else 0
            purchase_sessions = conversion[0]['purchase_sessions'] if conversion else 0
            conversion_rate = (purchase_sessions / checkout_sessions * 100) if checkout_sessions > 0 else 0
            
            return {
                'timestamp': now.isoformat(),
                'active_users_last_hour': current_users[0]['active_sessions'] if current_users else 0,
                'page_views_last_hour': page_views[0]['page_views'] if page_views else 0,
                'orders_last_24h': revenue[0]['orders_count'] if revenue else 0,
                'revenue_last_24h': float(revenue[0]['total_revenue'] or 0) if revenue else 0,
                'conversion_rate_24h': round(conversion_rate, 2)
            }
            
        except Exception as e:
            logger.error("Failed to get real-time metrics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get real-time metrics: {str(e)}"
            )
    
    async def get_traffic_analytics(
        self, 
        start_time: datetime, 
        end_time: datetime,
        granularity: str = "hour"
    ) -> Dict[str, Any]:
        """Get traffic analytics with time-series data."""
        try:
            # Validate granularity
            if granularity not in ["hour", "day", "week"]:
                raise ValueError("Granularity must be 'hour', 'day', or 'week'")
            
            # Time grouping format
            time_formats = {
                "hour": "toStartOfHour(timestamp)",
                "day": "toStartOfDay(timestamp)",
                "week": "toStartOfWeek(timestamp)"
            }
            
            time_group = time_formats[granularity]
            
            query = f"""
            SELECT 
                {time_group} as time_bucket,
                COUNT(*) as total_events,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as page_views,
                COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                COUNT(CASE WHEN event_type = 'cart_add' THEN 1 END) as cart_adds,
                COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchases
            FROM events 
            WHERE timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY time_bucket
            ORDER BY time_bucket
            """
            
            results = await self.clickhouse.execute_query(query, {
                'start_time': start_time,
                'end_time': end_time
            })
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'granularity': granularity
                },
                'data': results
            }
            
        except Exception as e:
            logger.error("Failed to get traffic analytics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get traffic analytics: {str(e)}"
            )
    
    async def get_conversion_funnel(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get conversion funnel analytics."""
        try:
            query = """
            SELECT 
                funnel_stage,
                COUNT(DISTINCT session_id) as sessions,
                COUNT(DISTINCT user_id) as users
            FROM (
                SELECT 
                    session_id,
                    user_id,
                    CASE 
                        WHEN event_type = 'page_view' THEN 'page_view'
                        WHEN event_type = 'game_view' THEN 'product_view'
                        WHEN event_type = 'cart_add' THEN 'cart_add'
                        WHEN event_type = 'checkout_start' THEN 'checkout_start'
                        WHEN event_type = 'purchase' THEN 'purchase'
                    END as funnel_stage
                FROM events 
                WHERE timestamp >= %(start_time)s 
                AND timestamp <= %(end_time)s
                AND event_type IN ('page_view', 'game_view', 'cart_add', 'checkout_start', 'purchase')
            ) 
            WHERE funnel_stage IS NOT NULL
            GROUP BY funnel_stage
            ORDER BY 
                CASE funnel_stage
                    WHEN 'page_view' THEN 1
                    WHEN 'product_view' THEN 2
                    WHEN 'cart_add' THEN 3
                    WHEN 'checkout_start' THEN 4
                    WHEN 'purchase' THEN 5
                END
            """
            
            results = await self.clickhouse.execute_query(query, {
                'start_time': start_time,
                'end_time': end_time
            })
            
            # Calculate conversion rates
            funnel_data = []
            previous_sessions = None
            
            for stage in results:
                sessions = stage['sessions']
                conversion_rate = None
                
                if previous_sessions is not None:
                    conversion_rate = (sessions / previous_sessions * 100) if previous_sessions > 0 else 0
                
                funnel_data.append({
                    'stage': stage['funnel_stage'],
                    'sessions': sessions,
                    'users': stage['users'],
                    'conversion_rate': round(conversion_rate, 2) if conversion_rate is not None else None,
                    'drop_off_rate': round(100 - conversion_rate, 2) if conversion_rate is not None else None
                })
                
                previous_sessions = sessions
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'funnel': funnel_data
            }
            
        except Exception as e:
            logger.error("Failed to get conversion funnel", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get conversion funnel: {str(e)}"
            )
    
    async def get_revenue_analytics(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get revenue and business analytics."""
        try:
            revenue_query = """
            SELECT 
                toStartOfDay(timestamp) as date,
                COUNT(*) as orders,
                SUM(total_amount) as revenue,
                AVG(total_amount) as avg_order_value,
                COUNT(DISTINCT user_id) as unique_customers
            FROM events 
            WHERE event_type = 'purchase'
            AND timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY date
            ORDER BY date
            """
            
            product_revenue_query = """
            SELECT 
                JSON_EXTRACT_STRING(properties, 'game_title') as product_name,
                COUNT(*) as purchase_count,
                SUM(JSON_EXTRACT_FLOAT(properties, 'total_amount')) as revenue
            FROM events 
            WHERE event_type = 'purchase'
            AND timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY product_name
            ORDER BY revenue DESC
            LIMIT 10
            """
            
            params = {'start_time': start_time, 'end_time': end_time}
            
            daily_revenue = await self.clickhouse.execute_query(revenue_query, params)
            top_products = await self.clickhouse.execute_query(product_revenue_query, params)
            
            # Calculate totals
            total_revenue = sum(row['revenue'] for row in daily_revenue)
            total_orders = sum(row['orders'] for row in daily_revenue)
            avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_revenue': float(total_revenue),
                    'total_orders': total_orders,
                    'average_order_value': round(avg_order_value, 2)
                },
                'daily_revenue': daily_revenue,
                'top_products': top_products
            }
            
        except Exception as e:
            logger.error("Failed to get revenue analytics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get revenue analytics: {str(e)}"
            )
    
    async def get_user_behavior_analytics(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get user behavior analytics."""
        try:
            session_query = """
            SELECT 
                session_id,
                COUNT(*) as events_count,
                MAX(timestamp) - MIN(timestamp) as session_duration,
                COUNT(DISTINCT page_url) as pages_visited,
                SUM(CASE WHEN event_type = 'cart_add' THEN 1 ELSE 0 END) as cart_adds,
                SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchases
            FROM events 
            WHERE timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY session_id
            """
            
            device_query = """
            SELECT 
                device_type,
                COUNT(DISTINCT session_id) as sessions,
                COUNT(CASE WHEN event_type = 'purchase' THEN 1 END) as purchases
            FROM events 
            WHERE timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY device_type
            """
            
            popular_pages_query = """
            SELECT 
                page_url,
                COUNT(*) as page_views,
                COUNT(DISTINCT session_id) as unique_visitors,
                AVG(JSON_EXTRACT_FLOAT(properties, 'time_on_page')) as avg_time_on_page
            FROM events 
            WHERE event_type = 'page_view'
            AND timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY page_url
            ORDER BY page_views DESC
            LIMIT 10
            """
            
            params = {'start_time': start_time, 'end_time': end_time}
            
            session_data = await self.clickhouse.execute_query(session_query, params)
            device_data = await self.clickhouse.execute_query(device_query, params)
            popular_pages = await self.clickhouse.execute_query(popular_pages_query, params)
            
            # Calculate session metrics
            if session_data:
                avg_session_duration = sum(row['session_duration'] for row in session_data) / len(session_data)
                avg_pages_per_session = sum(row['pages_visited'] for row in session_data) / len(session_data)
                bounce_rate = len([row for row in session_data if row['pages_visited'] == 1]) / len(session_data) * 100
            else:
                avg_session_duration = 0
                avg_pages_per_session = 0
                bounce_rate = 0
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'session_metrics': {
                    'average_session_duration': round(avg_session_duration, 2),
                    'average_pages_per_session': round(avg_pages_per_session, 2),
                    'bounce_rate': round(bounce_rate, 2)
                },
                'device_breakdown': device_data,
                'popular_pages': popular_pages
            }
            
        except Exception as e:
            logger.error("Failed to get user behavior analytics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user behavior analytics: {str(e)}"
            )
    
    async def get_search_analytics(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get search behavior analytics."""
        try:
            search_terms_query = """
            SELECT 
                JSON_EXTRACT_STRING(properties, 'search_query') as search_term,
                COUNT(*) as search_count,
                AVG(JSON_EXTRACT_INT(properties, 'search_results_count')) as avg_results,
                COUNT(DISTINCT session_id) as unique_searchers
            FROM events 
            WHERE event_type = 'search'
            AND timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            GROUP BY search_term
            ORDER BY search_count DESC
            LIMIT 20
            """
            
            zero_results_query = """
            SELECT COUNT(*) as zero_result_searches
            FROM events 
            WHERE event_type = 'search'
            AND JSON_EXTRACT_INT(properties, 'search_results_count') = 0
            AND timestamp >= %(start_time)s 
            AND timestamp <= %(end_time)s
            """
            
            params = {'start_time': start_time, 'end_time': end_time}
            
            popular_searches = await self.clickhouse.execute_query(search_terms_query, params)
            zero_results = await self.clickhouse.execute_query(zero_results_query, params)
            
            total_searches = sum(row['search_count'] for row in popular_searches)
            zero_result_count = zero_results[0]['zero_result_searches'] if zero_results else 0
            zero_result_rate = (zero_result_count / total_searches * 100) if total_searches > 0 else 0
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'summary': {
                    'total_searches': total_searches,
                    'zero_result_searches': zero_result_count,
                    'zero_result_rate': round(zero_result_rate, 2)
                },
                'popular_search_terms': popular_searches
            }
            
        except Exception as e:
            logger.error("Failed to get search analytics", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get search analytics: {str(e)}"
            )
    
    async def get_cohort_analysis(
        self, 
        start_time: datetime, 
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get user cohort analysis."""
        try:
            # This is a simplified cohort analysis
            # In production, you'd want more sophisticated cohort tracking
            query = """
            WITH user_cohorts AS (
                SELECT 
                    user_id,
                    toStartOfWeek(MIN(timestamp)) as cohort_week,
                    toStartOfWeek(timestamp) as activity_week
                FROM events 
                WHERE user_id IS NOT NULL
                AND timestamp >= %(start_time)s 
                AND timestamp <= %(end_time)s
                GROUP BY user_id, activity_week
            )
            SELECT 
                cohort_week,
                activity_week,
                COUNT(DISTINCT user_id) as active_users
            FROM user_cohorts
            GROUP BY cohort_week, activity_week
            ORDER BY cohort_week, activity_week
            """
            
            results = await self.clickhouse.execute_query(query, {
                'start_time': start_time,
                'end_time': end_time
            })
            
            return {
                'period': {
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat()
                },
                'cohort_data': results
            }
            
        except Exception as e:
            logger.error("Failed to get cohort analysis", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get cohort analysis: {str(e)}"
            )