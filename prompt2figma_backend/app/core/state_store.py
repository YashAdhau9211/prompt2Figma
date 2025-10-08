# app/core/state_store.py
"""
Redis-based state store for the Stateful Iterative Design Engine.
Handles storage and retrieval of design sessions, states, and context history.
"""

import json
import redis.asyncio as redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.core.models import (
    DesignState, DesignSession, SessionMetadata, EditContext
)

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
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
        self.session_ttl = timedelta(hours=24)  # Sessions expire after 24 hours
        self.context_limit = 10  # Keep last 10 context entries
    
    async def connect(self):
        """Initialize Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
            await self._redis.ping()  # Test connection
            logger.info("Connected to Redis state store")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis state store")
    
    @property
    def redis(self) -> redis.Redis:
        """Get Redis connection, ensuring it's initialized."""
        if self._redis is None:
            raise RuntimeError("Redis connection not initialized. Call connect() first.")
        return self._redis
    
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
                "total_edits": 0
            }
            
            await self.redis.hset(session_key, mapping=session_data)
            await self.redis.expire(session_key, self.session_ttl)
            
            # Add to user's session list
            await self.redis.sadd(user_sessions_key, session.session_id)
            await self.redis.expire(user_sessions_key, self.session_ttl)
            
            logger.info(f"Created session {session.session_id} for user {session.user_id}")
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
                total_edits=int(data.get("total_edits", 0))
            )
            
        except Exception as e:
            logger.error(f"Failed to get session metadata {session_id}: {e}")
            return None
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Update the last activity timestamp for a session."""
        try:
            session_key = f"session:{session_id}:metadata"
            await self.redis.hset(session_key, "last_activity", datetime.utcnow().isoformat())
            return True
        except Exception as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False
    
    # Design State Management
    async def store_design_state(self, session_id: str, version: int, state: DesignState) -> bool:
        """Store a versioned design state."""
        try:
            state_key = f"session:{session_id}:state:v{version}"
            
            state_data = {
                "wireframe_json": json.dumps(state.wireframe_json),
                "metadata": json.dumps(state.metadata),
                "created_at": state.created_at.isoformat(),
                "version": version
            }
            
            await self.redis.hset(state_key, mapping=state_data)
            await self.redis.expire(state_key, self.session_ttl)
            
            # Update current version in session metadata
            session_key = f"session:{session_id}:metadata"
            await self.redis.hset(session_key, "current_version", version)
            
            logger.info(f"Stored design state v{version} for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store design state {session_id} v{version}: {e}")
            return False
    
    async def get_design_state(self, session_id: str, version: Optional[int] = None) -> Optional[DesignState]:
        """Retrieve a design state. If version is None, gets the latest version."""
        try:
            if version is None:
                # Get current version from session metadata
                metadata = await self.get_session_metadata(session_id)
                if not metadata:
                    return None
                version = metadata.current_version
            
            state_key = f"session:{session_id}:state:v{version}"
            data = await self.redis.hgetall(state_key)
            
            if not data:
                return None
            
            return DesignState(
                wireframe_json=json.loads(data["wireframe_json"]),
                metadata=json.loads(data["metadata"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                version=int(data["version"])
            )
            
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
                "processing_time_ms": context.processing_time_ms
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
    
    async def get_context_history(self, session_id: str, limit: int = 10) -> List[EditContext]:
        """Get the recent context history for a session."""
        try:
            context_key = f"session:{session_id}:context"
            entries = await self.redis.lrange(context_key, 0, limit - 1)
            
            contexts = []
            for entry in entries:
                data = json.loads(entry)
                contexts.append(EditContext(
                    prompt=data["prompt"],
                    edit_type=data["edit_type"],
                    target_elements=json.loads(data["target_elements"]),
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    processing_time_ms=data["processing_time_ms"]
                ))
            
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
                f"session:{session_id}:context"
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
            logger.error(f"Failed to increment edit count for session {session_id}: {e}")
            return False