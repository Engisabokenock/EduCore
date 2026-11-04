"""
Redis access with graceful degradation.

Redis is an accelerator (cache, rate-limit counters), never a hard dependency: a
missing or malformed REDIS_URL, or a Redis outage, must not take the API down. All
helpers log and fall back instead of raising.
"""
import json
import logging
from typing import Any, Optional

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger("educore.performance.cache")


def _build_pool() -> Optional[ConnectionPool]:
    url = settings.REDIS_URL
    if not url:
        logger.warning("REDIS_URL not set; caching and distributed rate limiting are disabled.")
        return None
    try:
        return ConnectionPool.from_url(
            url,
            max_connections=50,
            socket_timeout=2.0,
            socket_connect_timeout=2.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    except ValueError as exc:
        # Typical cause: an Upstash REST token pasted instead of the rediss:// URL.
        logger.error(
            "REDIS_URL is not a valid redis:// or rediss:// URL (%s); Redis features disabled.", exc
        )
        return None


redis_pool: Optional[ConnectionPool] = _build_pool()


def get_redis_client() -> Optional[Redis]:
    """Return a pooled async Redis client, or None when Redis is not configured."""
    if redis_pool is None:
        return None
    return Redis(connection_pool=redis_pool)


async def close_redis() -> None:
    if redis_pool is not None:
        await redis_pool.disconnect()


class CacheManager:
    """JSON cache-aside helpers. Every method is a safe no-op without Redis."""

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        client = get_redis_client()
        if client is None:
            return None
        try:
            async with client:
                data = await client.get(key)
                return json.loads(data) if data else None
        except Exception as exc:
            logger.warning("Redis read failed for %s: %s", key, exc)
            return None

    @staticmethod
    async def set(key: str, value: Any, expire_seconds: int = 300) -> bool:
        client = get_redis_client()
        if client is None:
            return False
        try:
            async with client:
                await client.set(key, json.dumps(value, default=str), ex=expire_seconds)
                return True
        except Exception as exc:
            logger.warning("Redis write failed for %s: %s", key, exc)
            return False

    @staticmethod
    async def invalidate(key: str) -> None:
        client = get_redis_client()
        if client is None:
            return
        try:
            async with client:
                await client.delete(key)
        except Exception as exc:
            logger.warning("Redis delete failed for %s: %s", key, exc)

    @staticmethod
    async def invalidate_prefix(prefix: str) -> None:
        """Evict every key starting with ``prefix`` (used after content changes)."""
        client = get_redis_client()
        if client is None:
            return
        try:
            async with client:
                async for key in client.scan_iter(match=f"{prefix}*", count=500):
                    await client.delete(key)
        except Exception as exc:
            logger.warning("Redis prefix eviction failed for %s: %s", prefix, exc)
