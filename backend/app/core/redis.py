"""
NexusOps AI — Redis Client
Async Redis connection with connection pooling
"""
from typing import Optional

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency — returns a Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


class CacheService:
    """
    High-level Redis cache abstraction with TTL support.
    Used for caching expensive AI analysis results and cluster data.
    """

    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client

    async def get(self, key: str) -> Optional[str]:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        await self._redis.setex(key, ttl, value)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self._redis.exists(key))

    async def publish(self, channel: str, message: str) -> None:
        """Publish a message to a Redis pub/sub channel."""
        await self._redis.publish(channel, message)

    async def increment(self, key: str, ttl: int = 60) -> int:
        """Atomic increment with TTL — useful for rate limiting."""
        pipe = self._redis.pipeline()
        await pipe.incr(key)
        await pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]
