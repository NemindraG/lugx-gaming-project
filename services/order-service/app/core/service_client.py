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


class GameServiceClient(ServiceClient):
    """Client for communicating with Game Service."""
    
    def __init__(self):
        super().__init__(settings.GAME_SERVICE_URL)
    
    async def get_game_details(self, game_id: str) -> Dict[str, Any]:
        """Get game details from Game Service."""
        return await self.get(f"/api/v1/games/{game_id}")
    
    async def check_inventory(self, game_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Check game inventory availability."""
        return await self.get(f"/api/v1/games/{game_id}/inventory", {"quantity": quantity})
    
    async def reserve_inventory(self, game_id: str, quantity: int) -> Dict[str, Any]:
        """Reserve inventory for order."""
        return await self.post(f"/api/v1/games/{game_id}/inventory/reserve", {"quantity": quantity})
    
    async def release_inventory(self, game_id: str, quantity: int) -> Dict[str, Any]:
        """Release reserved inventory."""
        return await self.post(f"/api/v1/games/{game_id}/inventory/release", {"quantity": quantity})


class AnalyticsServiceClient(ServiceClient):
    """Client for communicating with Analytics Service."""
    
    def __init__(self):
        super().__init__(settings.ANALYTICS_SERVICE_URL)
    
    async def track_event(self, event_data: Dict[str, Any]) -> None:
        """Send event to analytics service."""
        await self.post("/api/v1/events/track", event_data)
    
    async def track_conversion(self, conversion_data: Dict[str, Any]) -> None:
        """Track conversion event."""
        await self.post("/api/v1/events/conversion", conversion_data)
    
    async def track_user_action(self, action_data: Dict[str, Any]) -> None:
        """Track user action event."""
        await self.post("/api/v1/events/user-action", action_data)