"""
Redis connection and configuration for Order Service.
Handles Redis client setup and connection management.
"""

import json
import logging
from typing import Any, Dict, Optional, List
from uuid import UUID

import redis.asyncio as redis
from redis.asyncio import Redis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class RedisClient:
    """Redis client wrapper with async support."""
    
    def __init__(self):
        self._redis: Optional[Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis server."""
        try:
            self._redis = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self._redis.ping()
            logger.info("Connected to Redis successfully", redis_url=settings.REDIS_URL)
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from Redis server."""
        if self._redis:
            await self._redis.close()
            logger.info("Disconnected from Redis")
    
    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if not self._redis:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._redis
    
    async def set(self, key: str, value: Any, expires: Optional[int] = None) -> bool:
        """Set a key-value pair with optional expiration."""
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            result = await self.client.set(key, serialized_value, ex=expires)
            return bool(result)
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        try:
            value = await self.client.get(key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key."""
        try:
            result = await self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error("Redis DELETE failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("Redis EXISTS failed", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        try:
            result = await self.client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            return False
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set multiple hash fields."""
        try:
            # Serialize complex values
            serialized_mapping = {}
            for k, v in mapping.items():
                if isinstance(v, (dict, list)):
                    serialized_mapping[k] = json.dumps(v)
                else:
                    serialized_mapping[k] = str(v)
            
            result = await self.client.hset(name, mapping=serialized_mapping)
            return result
        except Exception as e:
            logger.error("Redis HSET failed", name=name, error=str(e))
            return 0
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash field value."""
        try:
            value = await self.client.hget(name, key)
            if value is None:
                return None
            
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error("Redis HGET failed", name=name, key=key, error=str(e))
            return None
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields."""
        try:
            result = await self.client.hgetall(name)
            
            # Deserialize values
            deserialized = {}
            for k, v in result.items():
                try:
                    deserialized[k] = json.loads(v)
                except json.JSONDecodeError:
                    deserialized[k] = v
            
            return deserialized
        except Exception as e:
            logger.error("Redis HGETALL failed", name=name, error=str(e))
            return {}
    
    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        try:
            result = await self.client.hdel(name, *keys)
            return result
        except Exception as e:
            logger.error("Redis HDEL failed", name=name, keys=keys, error=str(e))
            return 0
    
    async def sadd(self, name: str, *values: str) -> int:
        """Add members to a set."""
        try:
            result = await self.client.sadd(name, *values)
            return result
        except Exception as e:
            logger.error("Redis SADD failed", name=name, error=str(e))
            return 0
    
    async def srem(self, name: str, *values: str) -> int:
        """Remove members from a set."""
        try:
            result = await self.client.srem(name, *values)
            return result
        except Exception as e:
            logger.error("Redis SREM failed", name=name, error=str(e))
            return 0
    
    async def smembers(self, name: str) -> set:
        """Get all members of a set."""
        try:
            result = await self.client.smembers(name)
            return result or set()
        except Exception as e:
            logger.error("Redis SMEMBERS failed", name=name, error=str(e))
            return set()
    
    async def incr(self, name: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            result = await self.client.incr(name, amount)
            return result
        except Exception as e:
            logger.error("Redis INCR failed", name=name, error=str(e))
            return 0
    
    async def decr(self, name: str, amount: int = 1) -> int:
        """Decrement a counter."""
        try:
            result = await self.client.decr(name, amount)
            return result
        except Exception as e:
            logger.error("Redis DECR failed", name=name, error=str(e))
            return 0


# Global Redis client instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Get Redis client dependency for FastAPI."""
    if not redis_client._redis:
        await redis_client.connect()
    return redis_client


async def init_redis() -> None:
    """Initialize Redis connection on app startup."""
    await redis_client.connect()


async def close_redis() -> None:
    """Close Redis connection on app shutdown."""
    await redis_client.disconnect()