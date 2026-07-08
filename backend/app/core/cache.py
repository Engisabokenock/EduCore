import json
import logging
from typing import Optional, Any
from redis.asyncio import ConnectionPool, Redis
from app.core.config import settings

logger = logging.getLogger("educore.performance.cache")

# Initialize highly optimized connection pool for Redis clusters.
# pool_size and timeout thresholds configured for low-overhead re-use.
redis_pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=50,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    retry_on_timeout=True,
)


def get_redis_client() -> Redis:
    """Returns a thread-safe async Redis client instance from the pool."""
    return Redis(connection_pool=redis_pool)


class CacheManager:
    """High-utility interface abstraction managing structural serialization caching layers."""

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Fetches and de-serializes cached entries down from memory pools."""
        async with get_redis_client() as client:
            try:
                data = await client.get(key)
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"Redis memory read exception trace: {str(e)}")
                return None

    @staticmethod
    async def set(key: str, value: Any, expire_seconds: int = 300) -> bool:
        """Serializes and records high-frequency runtime data maps into Redis."""
        async with get_redis_client() as client:
            try:
                serialized_data = json.dumps(value, default=str)
                await client.set(key, serialized_data, ex=expire_seconds)
                return True
            except Exception as e:
                logger.error(f"Redis memory write exception trace: {str(e)}")
                return False

    @staticmethod
    async def invalidate(key: str) -> None:
        """Evicts stale data segments cleanly to guarantee multi-node record consistency."""
        async with get_redis_client() as client:
            try:
                await client.delete(key)
            except Exception as e:
                logger.error(f"Redis memory eviction exception trace: {str(e)}")
