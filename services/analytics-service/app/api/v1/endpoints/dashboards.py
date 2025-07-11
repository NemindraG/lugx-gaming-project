"""
Dashboard data endpoints for Analytics Service.
Pre-configured analytics dashboards for business intelligence.
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


@router.get("/overview")
async def get_overview_dashboard(
    period: str = Query("7d", description="Time period: 1d, 7d, 30d, 90d"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get comprehensive overview dashboard with key business metrics."""
    try:
        # Calculate date range based on period
        end_time = datetime.now()
        if period == "1d":
            start_time = end_time - timedelta(days=1)
        elif period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        elif period == "90d":
            start_time = end_time - timedelta(days=90)
        else:
            start_time = end_time - timedelta(days=7)
        
        # Get comprehensive metrics
        real_time_metrics = await analytics_service.get_real_time_metrics()
        traffic_analytics = await analytics_service.get_traffic_analytics(start_time, end_time, "day")
        conversion_funnel = await analytics_service.get_conversion_funnel(start_time, end_time)
        revenue_analytics = await analytics_service.get_revenue_analytics(start_time, end_time)
        
        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "dashboard": {
                "real_time": real_time_metrics,
                "traffic": traffic_analytics,
                "conversion": conversion_funnel,
                "revenue": revenue_analytics
            }
        }
        
    except Exception as e:
        logger.error("Failed to get overview dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overview dashboard: {str(e)}"
        )


@router.get("/sales")
async def get_sales_dashboard(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 365d"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get comprehensive sales analytics dashboard."""
    try:
        # Calculate date range based on period
        end_time = datetime.now()
        if period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        elif period == "90d":
            start_time = end_time - timedelta(days=90)
        elif period == "365d":
            start_time = end_time - timedelta(days=365)
        else:
            start_time = end_time - timedelta(days=30)
        
        # Get sales-related metrics
        conversion_funnel = await analytics_service.get_conversion_funnel(start_time, end_time)
        revenue_analytics = await analytics_service.get_revenue_analytics(start_time, end_time)
        
        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "dashboard": {
                "conversion_funnel": conversion_funnel,
                "revenue": revenue_analytics
            }
        }
        
    except Exception as e:
        logger.error("Failed to get sales dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sales dashboard: {str(e)}"
        )


@router.get("/user-engagement")
async def get_user_engagement_dashboard(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get comprehensive user engagement analytics dashboard."""
    try:
        # Calculate date range based on period
        end_time = datetime.now()
        if period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        elif period == "90d":
            start_time = end_time - timedelta(days=90)
        else:
            start_time = end_time - timedelta(days=30)
        
        # Get user engagement metrics
        user_behavior = await analytics_service.get_user_behavior_analytics(start_time, end_time)
        search_analytics = await analytics_service.get_search_analytics(start_time, end_time)
        cohort_analysis = await analytics_service.get_cohort_analysis(start_time, end_time)
        
        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "dashboard": {
                "user_behavior": user_behavior,
                "search_analytics": search_analytics,
                "cohort_analysis": cohort_analysis
            }
        }
        
    except Exception as e:
        logger.error("Failed to get user engagement dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user engagement dashboard: {str(e)}"
        )


@router.get("/executive")
async def get_executive_dashboard(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d, 365d"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
) -> Dict[str, Any]:
    """Get executive-level KPI dashboard with high-level business metrics."""
    try:
        # Calculate date range based on period
        end_time = datetime.now()
        if period == "7d":
            start_time = end_time - timedelta(days=7)
        elif period == "30d":
            start_time = end_time - timedelta(days=30)
        elif period == "90d":
            start_time = end_time - timedelta(days=90)
        elif period == "365d":
            start_time = end_time - timedelta(days=365)
        else:
            start_time = end_time - timedelta(days=30)
        
        # Get executive-level metrics
        real_time_metrics = await analytics_service.get_real_time_metrics()
        revenue_analytics = await analytics_service.get_revenue_analytics(start_time, end_time)
        conversion_funnel = await analytics_service.get_conversion_funnel(start_time, end_time)
        traffic_analytics = await analytics_service.get_traffic_analytics(start_time, end_time, "week")
        
        # Calculate growth rates (simplified - comparing with previous period)
        previous_period_start = start_time - (end_time - start_time)
        previous_revenue = await analytics_service.get_revenue_analytics(previous_period_start, start_time)
        
        revenue_growth = 0.0
        if previous_revenue['summary']['total_revenue'] > 0:
            current_revenue = revenue_analytics['summary']['total_revenue']
            prev_revenue = previous_revenue['summary']['total_revenue']
            revenue_growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
        
        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "dashboard": {
                "kpis": {
                    "total_revenue": revenue_analytics['summary']['total_revenue'],
                    "total_orders": revenue_analytics['summary']['total_orders'],
                    "average_order_value": revenue_analytics['summary']['average_order_value'],
                    "revenue_growth_percent": round(revenue_growth, 2),
                    "active_users": real_time_metrics.get('active_users_last_hour', 0),
                    "conversion_rate": conversion_funnel['funnel'][-1]['conversion_rate'] if conversion_funnel['funnel'] else 0
                },
                "revenue_trend": revenue_analytics['daily_revenue'],
                "traffic_trend": traffic_analytics['data'],
                "top_products": revenue_analytics['top_products']
            }
        }
        
    except Exception as e:
        logger.error("Failed to get executive dashboard", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get executive dashboard: {str(e)}"
        )


@router.get("/custom")
async def get_custom_dashboard(
    query: str = Query(..., description="Custom ClickHouse query"),
    clickhouse_client: ClickHouseClient = Depends(get_clickhouse_client)
) -> Dict[str, Any]:
    """Execute custom analytics query (restricted to SELECT statements)."""
    try:
        # Basic security check - only allow SELECT queries
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only SELECT queries are allowed"
            )
        
        # Additional security checks
        forbidden_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "CREATE", "ALTER"]
        if any(keyword in query_upper for keyword in forbidden_keywords):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query contains forbidden keywords"
            )
        
        # Execute custom query
        results = await clickhouse_client.execute_query(query, {})
        
        return {
            "query": query,
            "results": results,
            "result_count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to execute custom query", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute custom query: {str(e)}"
        )