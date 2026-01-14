# app/core/redis_pool.py
"""
Redis connection pool manager with optimized serialization.
Provides efficient connection pooling and data serialization for high-performance operations.
"""

import json
import logging
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

logger = logging.getLogger(__name__)


class SerializationFormat:
    """Serialization format options."""

    JSON = "json"
    MSGPACK = "msgpack"  # More efficient binary format (requires msgpack library)


class RedisPoolManager:
    """
    Manages Redis connection pools with optimized settings.

    Features:
    - Connection pooling for better performance
    - Configurable pool size
    - Efficient serialization options
    - Connection health monitoring
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        max_connections: int = 50,
        min_idle_connections: int = 10,
        socket_timeout: float = 5.0,
        socket_connect_timeout: float = 5.0,
        socket_keepalive: bool = True,
        serialization_format: str = SerializationFormat.JSON,
    ):
        """
        Initialize Redis pool manager.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum number of connections in pool
            min_idle_connections: Minimum idle connections to maintain
            socket_timeout: Socket timeout in seconds
            socket_connect_timeout: Socket connect timeout in seconds
            socket_keepalive: Enable TCP keepalive
            serialization_format: Data serialization format (json or msgpack)
        """
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.min_idle_connections = min_idle_connections
        self.serialization_format = serialization_format

        # Create connection pool with optimized settings
        # Note: socket_keepalive_options disabled for cloud environments
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=True,  # Auto-decode responses to strings
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            socket_keepalive=socket_keepalive,
        )

        self._redis_client: Optional[redis.Redis] = None

        # Try to import msgpack if that format is selected
        self._msgpack = None
        if serialization_format == SerializationFormat.MSGPACK:
            try:
                import msgpack

                self._msgpack = msgpack
                logger.info("Using msgpack for efficient serialization")
            except ImportError:
                logger.warning("msgpack not available, falling back to JSON")
                self.serialization_format = SerializationFormat.JSON

    async def get_client(self) -> redis.Redis:
        """
        Get Redis client from pool.

        Returns:
            Redis client instance
        """
        if self._redis_client is None:
            self._redis_client = redis.Redis(connection_pool=self.pool)
            # Test connection
            try:
                await self._redis_client.ping()
                logger.info(
                    f"Redis pool initialized with {self.max_connections} max connections"
                )
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

        return self._redis_client

    async def close(self):
        """Close all connections in the pool."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None

        await self.pool.disconnect()
        logger.info("Redis connection pool closed")

    def serialize(self, data: Any) -> str:
        """
        Serialize data using configured format.

        Args:
            data: Data to serialize

        Returns:
            Serialized string
        """
        if self.serialization_format == SerializationFormat.MSGPACK and self._msgpack:
            # Use msgpack for more efficient binary serialization
            packed = self._msgpack.packb(data, use_bin_type=True)
            # Convert to base64 string for Redis storage
            import base64

            return base64.b64encode(packed).decode("utf-8")
        else:
            # Default to JSON
            return json.dumps(data, default=str)

    def deserialize(self, data: str) -> Any:
        """
        Deserialize data using configured format.

        Args:
            data: Serialized string

        Returns:
            Deserialized data
        """
        if self.serialization_format == SerializationFormat.MSGPACK and self._msgpack:
            # Decode from base64 and unpack
            import base64

            packed = base64.b64decode(data.encode("utf-8"))
            return self._msgpack.unpackb(packed, raw=False)
        else:
            # Default to JSON
            return json.loads(data)

    async def get_pool_stats(self) -> dict:
        """
        Get connection pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        # Note: redis-py doesn't expose detailed pool stats directly
        # This is a simplified version
        return {
            "max_connections": self.max_connections,
            "serialization_format": self.serialization_format,
            "connected": self._redis_client is not None,
        }

    async def health_check(self) -> bool:
        """
        Perform health check on Redis connection.

        Returns:
            True if healthy, False otherwise
        """
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


# Global pool manager instance
_global_pool_manager: Optional[RedisPoolManager] = None


def get_redis_pool_manager(
    redis_url: str = "redis://localhost:6379",
) -> RedisPoolManager:
    """Get or create the global Redis pool manager."""
    global _global_pool_manager
    if _global_pool_manager is None:
        _global_pool_manager = RedisPoolManager(redis_url=redis_url)
    return _global_pool_manager


async def close_redis_pool():
    """Close the global Redis pool."""
    global _global_pool_manager
    if _global_pool_manager:
        await _global_pool_manager.close()
        _global_pool_manager = None
