"""
Analytics data endpoints for Analytics Service.
Provides real-time analytics and business intelligence APIs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.clients.clickhouse_client import ClickHouseClient
from app.services.analytics_service import AnalyticsService

router = APIRouter()
logger = structlog.get_logger()


def get_clickhouse_client(request: Request) -> ClickHouseClient:
    """Get ClickHouse client from app state."""
    return request.app.state.clickhouse_client


def get_analytics_service(
    clickhouse_client: ClickHouseClient = Depends(get_clickhouse_client)
) -> AnalyticsService:
    """Get analytics service instance."""
    return AnalyticsService(clickhouse_client)


@router.get("/real-time")
async def get_real_time_metrics(
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get real-time platform metrics."""
    return await analytics_service.get_real_time_metrics()


@router.get("/traffic")
async def get_traffic_analytics(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    granularity: str = Query("hour", description="Time granularity: hour, day, week"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get traffic analytics with time-series data."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    return await analytics_service.get_traffic_analytics(start_time, end_time, granularity)


@router.get("/conversion-funnel")
async def get_conversion_funnel(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get conversion funnel analytics."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=30)
    
    return await analytics_service.get_conversion_funnel(start_time, end_time)


@router.get("/revenue")
async def get_revenue_analytics(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get revenue and business analytics."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=30)
    
    return await analytics_service.get_revenue_analytics(start_time, end_time)


@router.get("/user-behavior")
async def get_user_behavior_analytics(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get user behavior analytics."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=30)
    
    return await analytics_service.get_user_behavior_analytics(start_time, end_time)


@router.get("/search")
async def get_search_analytics(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get search behavior analytics."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    return await analytics_service.get_search_analytics(start_time, end_time)


@router.get("/cohorts")
async def get_cohort_analysis(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get user cohort analysis."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=90)  # 3 months for cohort analysis
    
    return await analytics_service.get_cohort_analysis(start_time, end_time)


@router.get("/performance")
async def get_performance_metrics(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get website performance metrics."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    try:
        query = """
        SELECT 
            AVG(JSON_EXTRACT_FLOAT(properties, 'page_load_time')) as avg_page_load_time,
            AVG(JSON_EXTRACT_FLOAT(properties, 'dom_content_loaded')) as avg_dom_content_loaded,
            AVG(JSON_EXTRACT_FLOAT(properties, 'first_contentful_paint')) as avg_first_contentful_paint,
            COUNT(*) as total_measurements
        FROM events 
        WHERE event_type = 'performance'
        AND timestamp >= %(start_time)s 
        AND timestamp <= %(end_time)s
        """
        
        clickhouse_client = analytics_service.clickhouse
        results = await clickhouse_client.execute_query(query, {
            'start_time': start_time,
            'end_time': end_time
        })
        
        return {
            'period': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'performance_metrics': results[0] if results else {}
        }
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}"
        )


@router.get("/errors")
async def get_error_analytics(
    start_time: Optional[datetime] = Query(None, description="Start time for analysis"),
    end_time: Optional[datetime] = Query(None, description="End time for analysis"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get error tracking analytics."""
    # Set default date range if not provided
    if not end_time:
        end_time = datetime.now()
    if not start_time:
        start_time = end_time - timedelta(days=7)
    
    try:
        query = """
        SELECT 
            JSON_EXTRACT_STRING(properties, 'error_message') as error_message,
            JSON_EXTRACT_STRING(properties, 'component') as component,
            COUNT(*) as error_count,
            COUNT(DISTINCT session_id) as affected_sessions
        FROM events 
        WHERE event_type = 'error'
        AND timestamp >= %(start_time)s 
        AND timestamp <= %(end_time)s
        GROUP BY error_message, component
        ORDER BY error_count DESC
        LIMIT 20
        """
        
        clickhouse_client = analytics_service.clickhouse
        results = await clickhouse_client.execute_query(query, {
            'start_time': start_time,
            'end_time': end_time
        })
        
        return {
            'period': {
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'error_analytics': results
        }
        
    except Exception as e:
        logger.error("Failed to get error analytics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error analytics: {str(e)}"
        )