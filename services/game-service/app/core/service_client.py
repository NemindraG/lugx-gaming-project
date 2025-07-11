"""
Service client for inter-service communication.
Provides a standardized way for services to communicate with each other.
"""

import httpx
import structlog
from typing import Dict, Any, Optional
from fastapi import HTTPException, status

from app.core.config import settings

logger = structlog.get_logger()


class ServiceClient:
    """Base client for inter-service communication."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to service."""
        try:
            response = await self._client.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Service request failed", endpoint=endpoint, status=e.response.status_code)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service request failed: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Service request error", endpoint=endpoint, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {str(e)}"
            )
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request to service."""
        try:
            response = await self._client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Service request failed", endpoint=endpoint, status=e.response.status_code)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service request failed: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Service request error", endpoint=endpoint, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {str(e)}"
            )
    
    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request to service."""
        try:
            response = await self._client.put(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Service request failed", endpoint=endpoint, status=e.response.status_code)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service request failed: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Service request error", endpoint=endpoint, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {str(e)}"
            )
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make DELETE request to service."""
        try:
            response = await self._client.delete(endpoint)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Service request failed", endpoint=endpoint, status=e.response.status_code)
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Service request failed: {e.response.text}"
            )
        except Exception as e:
            logger.error(f"Service request error", endpoint=endpoint, error=str(e))
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {str(e)}"
            )


class OrderServiceClient(ServiceClient):
    """Client for communicating with Order Service."""
    
    def __init__(self):
        super().__init__(settings.ORDER_SERVICE_URL)
    
    async def get_user_orders(self, user_id: str) -> Dict[str, Any]:
        """Get user's order history."""
        return await self.get(f"/api/v1/orders?user_id={user_id}")
    
    async def check_user_purchase(self, user_id: str, game_id: str) -> bool:
        """Check if user has purchased a specific game."""
        orders = await self.get_user_orders(user_id)
        for order in orders.get("orders", []):
            for item in order.get("items", []):
                if item.get("game_id") == game_id:
                    return True
        return False


class AnalyticsServiceClient(ServiceClient):
    """Client for communicating with Analytics Service."""
    
    def __init__(self):
        super().__init__(settings.ANALYTICS_SERVICE_URL)
    
    async def track_event(self, event_data: Dict[str, Any]) -> None:
        """Send event to analytics service."""
        await self.post("/api/v1/events/track", event_data)
    
    async def track_page_view(self, page_data: Dict[str, Any]) -> None:
        """Track page view event."""
        await self.post("/api/v1/events/page-view", page_data)
    
    async def get_trending_games(self) -> Dict[str, Any]:
        """Get trending games from analytics."""
        return await self.get("/api/v1/analytics/trending-games")