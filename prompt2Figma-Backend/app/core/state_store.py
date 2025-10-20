# app/core/state_store.py
"""
Redis-based state store for the Stateful Iterative Design Engine.
Handles storage and retrieval of design sessions, states, and context history.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from app.core.context_compression import compress_with_summarization
from app.core.error_recovery import GracefulDegradationManager, SessionRecoveryManager
from app.core.models import DesignSession, DesignState, EditContext, SessionMetadata
from app.core.performance_monitor import MetricType, PerformanceTimer, get_performance_monitor
from app.core.redis_pool import RedisPoolManager

logger = logging.getLogger(__name__)


class RedisStateStore:
    """
    Redis-based storage for design sessions and states.

    Key Patterns:
    - session:{session_id}:metadata     # Session info and current version
    - session:{session_id}:state:v{n}   # Versioned design states
    - session:{session_id}:context      # Context history (last 10 interactions)
    - user:{user_id}:sessions          # User's active sessions
    - analytics:edits:{date}           # Daily edit metrics
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        use_connection_pool: bool = True,
        max_connections: int = 50,
    ):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self.session_ttl = timedelta(hours=24)  # Sessions expire after 24 hours
        self.context_limit = 10  # Keep last 10 context entries

        # Connection pool for better performance
        self.use_connection_pool = use_connection_pool
        self.pool_manager = None
        if use_connection_pool:
            self.pool_manager = RedisPoolManager(
                redis_url=redis_url, max_connections=max_connections
            )

        # Performance monitoring
        self.performance_monitor = get_performance_monitor()

        # Error handling components
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5, recovery_timeout=60, success_threshold=2
        )
        self.recovery_manager = SessionRecoveryManager()
        self.degradation_manager = GracefulDegradationManager()

    async def connect(self):
        """Initialize Redis connection with circuit breaker protection."""
        if self._redis is None:
            try:

                async def _connect():
                    if self.use_connection_pool and self.pool_manager:
                        # Use connection pool for better performance
                        self._redis = await self.pool_manager.get_client()
                    else:
                        # Fallback to direct connection
                        self._redis = redis.from_url(
                            self.redis_url, decode_responses=True
                        )

                    await self._redis.ping()  # Test connection
                    return True

                await self.circuit_breaker.call(_connect)
                logger.info(
                    f"Connected to Redis state store (pool: {self.use_connection_pool})"
                )

                # Disable degraded mode if it was enabled
                if self.degradation_manager.is_degraded():
                    self.degradation_manager.disable_degraded_mode()

            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker prevented Redis connection: {e}")
                self.degradation_manager.enable_degraded_mode()
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.degradation_manager.enable_degraded_mode()
                raise

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            if not self.use_connection_pool:
                # Only close if not using pool (pool manages its own connections)
                await self._redis.close()
            self._redis = None

        if self.pool_manager:
            await self.pool_manager.close()

        logger.info("Disconnected from Redis state store")

    @property
    def redis(self) -> redis.Redis:
        """Get Redis connection, ensuring it's initialized."""
        if self._redis is None:
            raise RuntimeError(
                "Redis connection not initialized. Call connect() first."
            )
        return self._redis

    async def _execute_with_circuit_breaker(self, operation, *args, **kwargs):
        """
        Execute a Redis operation with circuit breaker protection.

        Args:
            operation: Async function to execute
            *args, **kwargs: Arguments for the operation

        Returns:
            Result of the operation or None if circuit is open

        Raises:
            CircuitBreakerError: If circuit breaker is open
        """
        try:
            return await self.circuit_breaker.call(operation, *args, **kwargs)
        except CircuitBreakerError as e:
            logger.error(f"Circuit breaker open: {e}")
            self.degradation_manager.enable_degraded_mode("Circuit breaker open")
            raise
        except Exception as e:
            logger.error(f"Redis operation failed: {e}")
            # Check if circuit breaker opened due to this failure
            if self.circuit_breaker.state.value == "open":
                self.degradation_manager.enable_degraded_mode(
                    "Redis operation failures"
                )
            raise

    # Session Management
    async def create_session(self, session: DesignSession) -> bool:
        """Create a new design session in Redis."""
        try:
            session_key = f"session:{session.session_id}:metadata"
            user_sessions_key = f"user:{session.user_id}:sessions"

            # Store session metadata
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "initial_prompt": session.initial_prompt,
                "current_version": session.current_version,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "status": session.status.value,
                "total_edits": 0,
            }

            await self.redis.hset(session_key, mapping=session_data)
            await self.redis.expire(session_key, self.session_ttl)

            # Add to user's session list
            await self.redis.sadd(user_sessions_key, session.session_id)
            await self.redis.expire(user_sessions_key, self.session_ttl)

            logger.info(
                f"Created session {session.session_id} for user {session.user_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create session {session.session_id}: {e}")
            return False

    async def get_session_metadata(self, session_id: str) -> Optional[SessionMetadata]:
        """Retrieve session metadata from Redis."""
        try:
            session_key = f"session:{session_id}:metadata"
            data = await self.redis.hgetall(session_key)

            if not data:
                return None

            return SessionMetadata(
                session_id=data["session_id"],
                user_id=data["user_id"],
                initial_prompt=data["initial_prompt"],
                current_version=int(data["current_version"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                last_activity=datetime.fromisoformat(data["last_activity"]),
                status=data["status"],
                total_edits=int(data.get("total_edits", 0)),
            )

        except Exception as e:
            logger.error(f"Failed to get session metadata {session_id}: {e}")
            return None

    async def update_session_activity(self, session_id: str) -> bool:
        """Update the last activity timestamp for a session."""
        try:
            session_key = f"session:{session_id}:metadata"
            await self.redis.hset(
                session_key, "last_activity", datetime.utcnow().isoformat()
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False

    # Design State Management
    async def store_design_state(
        self, session_id: str, version: int, state: DesignState
    ) -> bool:
        """Store a versioned design state with performance monitoring."""
        async with PerformanceTimer(
            self.performance_monitor,
            MetricType.STATE_STORAGE_TIME,
            session_id=session_id,
            metadata={"version": version},
        ):
            try:
                state_key = f"session:{session_id}:state:v{version}"

                # Use efficient serialization if pool manager available
                if self.pool_manager:
                    wireframe_str = self.pool_manager.serialize(state.wireframe_json)
                    metadata_str = self.pool_manager.serialize(state.metadata)
                else:
                    wireframe_str = json.dumps(state.wireframe_json)
                    metadata_str = json.dumps(state.metadata)

                state_data = {
                    "wireframe_json": wireframe_str,
                    "metadata": metadata_str,
                    "created_at": state.created_at.isoformat(),
                    "version": version,
                }

                await self.redis.hset(state_key, mapping=state_data)
                await self.redis.expire(state_key, self.session_ttl)

                # Update current version in session metadata
                session_key = f"session:{session_id}:metadata"
                await self.redis.hset(session_key, "current_version", version)

                logger.info(f"Stored design state v{version} for session {session_id}")
                return True

            except Exception as e:
                logger.error(
                    f"Failed to store design state {session_id} v{version}: {e}"
                )
                return False

    async def get_design_state(
        self, session_id: str, version: Optional[int] = None
    ) -> Optional[DesignState]:
        """
        Retrieve a design state with validation and recovery.
        If version is None, gets the latest version.
        """
        async with PerformanceTimer(
            self.performance_monitor,
            MetricType.STATE_RETRIEVAL_TIME,
            session_id=session_id,
            metadata={"version": version},
        ):
            try:
                # Check degraded mode first
                if self.degradation_manager.is_degraded():
                    logger.warning(
                        f"Operating in degraded mode for session {session_id}"
                    )
                    cached_data = await self.degradation_manager.get_cached_session(
                        session_id
                    )
                    if cached_data and version is None:
                        # Return cached state if available
                        return DesignState(**cached_data)
                    return None

                if version is None:
                    # Get current version from session metadata
                    metadata = await self.get_session_metadata(session_id)
                    if not metadata:
                        return None
                    version = metadata.current_version

                state_key = f"session:{session_id}:state:v{version}"

                async def _get_state():
                    return await self.redis.hgetall(state_key)

                data = await self._execute_with_circuit_breaker(_get_state)

                if not data:
                    return None

                # Validate state integrity
                is_valid, error_msg = (
                    await self.recovery_manager.validate_session_state(session_id, data)
                )

                if not is_valid:
                    logger.warning(
                        f"Invalid state detected for {session_id} v{version}: {error_msg}"
                    )

                    # Attempt recovery
                    previous_versions = await self.get_all_versions(session_id)
                    previous_states = []
                    for prev_version in previous_versions:
                        if prev_version < version:
                            prev_data = await self.redis.hgetall(
                                f"session:{session_id}:state:v{prev_version}"
                            )
                            if prev_data:
                                previous_states.append(prev_data)

                    recovered_state = await self.recovery_manager.recover_session_state(
                        session_id, data, previous_states
                    )

                    if recovered_state:
                        logger.info(
                            f"Successfully recovered state for {session_id} v{version}"
                        )
                        # Store recovered state back to Redis
                        await self.store_design_state(
                            session_id, version, recovered_state
                        )
                        return recovered_state
                    else:
                        logger.error(
                            f"Failed to recover state for {session_id} v{version}"
                        )
                        return None

                # State is valid, convert to model
                # Use efficient deserialization if pool manager available
                if self.pool_manager:
                    wireframe_json = self.pool_manager.deserialize(
                        data["wireframe_json"]
                    )
                    metadata_json = self.pool_manager.deserialize(data["metadata"])
                else:
                    wireframe_json = json.loads(data["wireframe_json"])
                    metadata_json = json.loads(data["metadata"])

                design_state = DesignState(
                    wireframe_json=wireframe_json,
                    metadata=metadata_json,
                    created_at=datetime.fromisoformat(data["created_at"]),
                    version=int(data["version"]),
                )

                # Validate the model itself
                is_model_valid, model_error = (
                    await self.recovery_manager.validate_design_state_model(
                        design_state
                    )
                )

                if not is_model_valid:
                    logger.error(f"Design state model validation failed: {model_error}")
                    return None

                return design_state

            except CircuitBreakerError:
                logger.error(
                    f"Circuit breaker prevented state retrieval for {session_id}"
                )
                return None
            except Exception as e:
                logger.error(f"Failed to get design state {session_id} v{version}: {e}")
                return None

    async def get_all_versions(self, session_id: str) -> List[int]:
        """Get all available version numbers for a session."""
        try:
            pattern = f"session:{session_id}:state:v*"
            keys = await self.redis.keys(pattern)

            versions = []
            for key in keys:
                # Extract version number from key like "session:id:state:v1"
                version_str = key.split(":v")[-1]
                try:
                    versions.append(int(version_str))
                except ValueError:
                    continue

            return sorted(versions)

        except Exception as e:
            logger.error(f"Failed to get versions for session {session_id}: {e}")
            return []

    # Context Management
    async def add_context_entry(self, session_id: str, context: EditContext) -> bool:
        """Add a context entry to the session's context history."""
        try:
            context_key = f"session:{session_id}:context"

            context_data = {
                "prompt": context.prompt,
                "edit_type": context.edit_type.value,
                "target_elements": json.dumps(context.target_elements),
                "timestamp": context.timestamp.isoformat(),
                "processing_time_ms": context.processing_time_ms,
            }

            # Add to list (LPUSH for newest first)
            await self.redis.lpush(context_key, json.dumps(context_data))

            # Trim to keep only last N entries
            await self.redis.ltrim(context_key, 0, self.context_limit - 1)
            await self.redis.expire(context_key, self.session_ttl)

            return True

        except Exception as e:
            logger.error(f"Failed to add context entry for session {session_id}: {e}")
            return False

    async def get_context_history(
        self, session_id: str, limit: int = 10
    ) -> List[EditContext]:
        """Get the recent context history for a session with compression."""
        try:
            context_key = f"session:{session_id}:context"
            # Fetch more entries than limit to allow for compression
            entries = await self.redis.lrange(context_key, 0, limit * 2 - 1)

            contexts = []
            for entry in entries:
                data = json.loads(entry)
                contexts.append(
                    EditContext(
                        prompt=data["prompt"],
                        edit_type=data["edit_type"],
                        target_elements=json.loads(data["target_elements"]),
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        processing_time_ms=data["processing_time_ms"],
                    )
                )

            # Apply compression if we have more contexts than needed
            if len(contexts) > limit:
                contexts = compress_with_summarization(
                    contexts, detailed_window=limit // 2, summary_window=limit
                )

            return contexts

        except Exception as e:
            logger.error(f"Failed to get context history for session {session_id}: {e}")
            return []

    # Session Cleanup
    async def cleanup_session(self, session_id: str) -> bool:
        """Remove all data associated with a session."""
        try:
            # Get all keys for this session
            patterns = [
                f"session:{session_id}:metadata",
                f"session:{session_id}:state:v*",
                f"session:{session_id}:context",
            ]

            keys_to_delete = []
            for pattern in patterns:
                keys = await self.redis.keys(pattern)
                keys_to_delete.extend(keys)

            if keys_to_delete:
                await self.redis.delete(*keys_to_delete)

            logger.info(f"Cleaned up session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            return False

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions. Returns number of sessions cleaned."""
        try:
            # This is a simplified version - in production you'd want more sophisticated cleanup
            # For now, we rely on Redis TTL for automatic cleanup
            logger.info("Session cleanup relies on Redis TTL")
            return 0

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    # User Session Management
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active session IDs for a user."""
        try:
            user_sessions_key = f"user:{user_id}:sessions"
            sessions = await self.redis.smembers(user_sessions_key)
            return list(sessions)

        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return []

    async def increment_edit_count(self, session_id: str) -> bool:
        """Increment the total edit count for a session."""
        try:
            session_key = f"session:{session_id}:metadata"
            await self.redis.hincrby(session_key, "total_edits", 1)
            return True
        except Exception as e:
            logger.error(
                f"Failed to increment edit count for session {session_id}: {e}"
            )
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the state store including circuit breaker and degradation status.

        Returns:
            Dictionary with health metrics
        """
        circuit_stats = self.circuit_breaker.get_stats()
        degradation_status = self.degradation_manager.get_degradation_status()

        return {
            "redis_connected": self._redis is not None,
            "circuit_breaker": circuit_stats,
            "degradation": degradation_status,
            "healthy": (
                circuit_stats["state"] == "closed"
                and not degradation_status["degraded_mode"]
            ),
        }

    async def reset_circuit_breaker(self):
        """Manually reset the circuit breaker (for admin operations)."""
        await self.circuit_breaker.reset()
        logger.info("Circuit breaker manually reset")

        # Try to reconnect if in degraded mode
        if self.degradation_manager.is_degraded():
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Failed to reconnect after circuit breaker reset: {e}")
