# tests/test_state_store.py
"""
Unit tests for Redis state store functionality.
Tests storage and retrieval operations for design sessions, states, and contexts.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.core.state_store import RedisStateStore
from app.core.models import (
    DesignSession, DesignState, EditContext, SessionMetadata,
    EditType, SessionStatus
)


@pytest.fixture
def sample_session():
    """Create a sample design session for testing."""
    return DesignSession(
        session_id="test-session-123",
        user_id="user-456",
        initial_prompt="Create a login form",
        current_version=1,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        last_activity=datetime(2024, 1, 1, 12, 0, 0),
        status=SessionStatus.ACTIVE
    )


@pytest.fixture
def sample_design_state():
    """Create a sample design state for testing."""
    return DesignState(
        wireframe_json={"type": "form", "elements": [{"type": "input", "label": "username"}]},
        metadata={"created_by": "ai", "edit_count": 1},
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        version=1
    )


@pytest.fixture
def sample_edit_context():
    """Create a sample edit context for testing."""
    return EditContext(
        prompt="Make the button bigger",
        edit_type=EditType.STYLE,
        target_elements=["button-1"],
        timestamp=datetime(2024, 1, 1, 12, 5, 0),
        processing_time_ms=150
    )


@pytest.fixture
def mock_redis():
    """Create a mock Redis connection."""
    mock = AsyncMock()
    mock.ping = AsyncMock()
    mock.hset = AsyncMock()
    mock.hgetall = AsyncMock()
    mock.sadd = AsyncMock()
    mock.expire = AsyncMock()
    mock.lpush = AsyncMock()
    mock.ltrim = AsyncMock()
    mock.lrange = AsyncMock()
    mock.keys = AsyncMock()
    mock.delete = AsyncMock()
    mock.smembers = AsyncMock()
    mock.hincrby = AsyncMock()
    mock.close = AsyncMock()
    return mock


class TestRedisStateStore:
    """Test cases for RedisStateStore class."""
    
    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self, mock_redis):
        """Test Redis connection and disconnection."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore("redis://localhost:6379")
            
            # Test connection
            await store.connect()
            assert store._redis is not None
            mock_redis.ping.assert_called_once()
            
            # Test disconnection
            await store.disconnect()
            assert store._redis is None
            mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, mock_redis, sample_session):
        """Test successful session creation."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            # Mock successful Redis operations
            mock_redis.hset.return_value = True
            mock_redis.sadd.return_value = True
            mock_redis.expire.return_value = True
            
            result = await store.create_session(sample_session)
            
            assert result is True
            
            # Verify Redis calls
            expected_session_key = f"session:{sample_session.session_id}:metadata"
            expected_user_key = f"user:{sample_session.user_id}:sessions"
            
            mock_redis.hset.assert_called()
            mock_redis.sadd.assert_called_with(expected_user_key, sample_session.session_id)
            assert mock_redis.expire.call_count == 2  # Called for both keys
    
    @pytest.mark.asyncio
    async def test_create_session_failure(self, mock_redis, sample_session):
        """Test session creation failure handling."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            # Mock Redis failure
            mock_redis.hset.side_effect = Exception("Redis error")
            
            result = await store.create_session(sample_session)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_session_metadata_success(self, mock_redis, sample_session):
        """Test successful session metadata retrieval."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            # Mock Redis response
            mock_redis.hgetall.return_value = {
                "session_id": sample_session.session_id,
                "user_id": sample_session.user_id,
                "initial_prompt": sample_session.initial_prompt,
                "current_version": str(sample_session.current_version),
                "created_at": sample_session.created_at.isoformat(),
                "last_activity": sample_session.last_activity.isoformat(),
                "status": sample_session.status.value,
                "total_edits": "0"
            }
            
            result = await store.get_session_metadata(sample_session.session_id)
            
            assert result is not None
            assert isinstance(result, SessionMetadata)
            assert result.session_id == sample_session.session_id
            assert result.user_id == sample_session.user_id
            assert result.current_version == sample_session.current_version
    
    @pytest.mark.asyncio
    async def test_get_session_metadata_not_found(self, mock_redis):
        """Test session metadata retrieval when session doesn't exist."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            # Mock empty Redis response
            mock_redis.hgetall.return_value = {}
            
            result = await store.get_session_metadata("nonexistent-session")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_store_design_state_success(self, mock_redis, sample_design_state):
        """Test successful design state storage."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            version = 1
            
            # Mock successful Redis operations
            mock_redis.hset.return_value = True
            mock_redis.expire.return_value = True
            
            result = await store.store_design_state(session_id, version, sample_design_state)
            
            assert result is True
            
            # Verify Redis calls
            expected_state_key = f"session:{session_id}:state:v{version}"
            expected_session_key = f"session:{session_id}:metadata"
            
            # Should be called twice: once for state, once for updating current version
            assert mock_redis.hset.call_count == 2
            mock_redis.expire.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_design_state_success(self, mock_redis, sample_design_state):
        """Test successful design state retrieval."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            version = 1
            
            # Mock Redis response
            mock_redis.hgetall.return_value = {
                "wireframe_json": json.dumps(sample_design_state.wireframe_json),
                "metadata": json.dumps(sample_design_state.metadata),
                "created_at": sample_design_state.created_at.isoformat(),
                "version": str(version)
            }
            
            result = await store.get_design_state(session_id, version)
            
            assert result is not None
            assert isinstance(result, DesignState)
            assert result.wireframe_json == sample_design_state.wireframe_json
            assert result.version == version
    
    @pytest.mark.asyncio
    async def test_get_design_state_latest_version(self, mock_redis, sample_design_state):
        """Test getting latest design state when no version specified."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock session metadata call
            metadata_response = {
                "session_id": session_id,
                "user_id": "user-456",
                "initial_prompt": "test prompt",
                "current_version": "2",
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
                "status": "active",
                "total_edits": "1"
            }
            
            # Mock state data call
            state_response = {
                "wireframe_json": json.dumps(sample_design_state.wireframe_json),
                "metadata": json.dumps(sample_design_state.metadata),
                "created_at": sample_design_state.created_at.isoformat(),
                "version": "2"
            }
            
            mock_redis.hgetall.side_effect = [metadata_response, state_response]
            
            result = await store.get_design_state(session_id)
            
            assert result is not None
            assert result.version == 2
    
    @pytest.mark.asyncio
    async def test_add_context_entry_success(self, mock_redis, sample_edit_context):
        """Test successful context entry addition."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock successful Redis operations
            mock_redis.lpush.return_value = 1
            mock_redis.ltrim.return_value = True
            mock_redis.expire.return_value = True
            
            result = await store.add_context_entry(session_id, sample_edit_context)
            
            assert result is True
            
            # Verify Redis calls
            expected_key = f"session:{session_id}:context"
            mock_redis.lpush.assert_called_once()
            mock_redis.ltrim.assert_called_with(expected_key, 0, 9)  # Keep last 10
            mock_redis.expire.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_context_history_success(self, mock_redis, sample_edit_context):
        """Test successful context history retrieval."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock Redis response
            context_data = {
                "prompt": sample_edit_context.prompt,
                "edit_type": sample_edit_context.edit_type.value,
                "target_elements": json.dumps(sample_edit_context.target_elements),
                "timestamp": sample_edit_context.timestamp.isoformat(),
                "processing_time_ms": sample_edit_context.processing_time_ms
            }
            
            mock_redis.lrange.return_value = [json.dumps(context_data)]
            
            result = await store.get_context_history(session_id)
            
            assert len(result) == 1
            assert isinstance(result[0], EditContext)
            assert result[0].prompt == sample_edit_context.prompt
            assert result[0].edit_type == sample_edit_context.edit_type
    
    @pytest.mark.asyncio
    async def test_get_all_versions(self, mock_redis):
        """Test getting all version numbers for a session."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock Redis keys response
            mock_redis.keys.return_value = [
                f"session:{session_id}:state:v1",
                f"session:{session_id}:state:v3",
                f"session:{session_id}:state:v2"
            ]
            
            result = await store.get_all_versions(session_id)
            
            assert result == [1, 2, 3]  # Should be sorted
    
    @pytest.mark.asyncio
    async def test_cleanup_session_success(self, mock_redis):
        """Test successful session cleanup."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock Redis keys response
            mock_redis.keys.side_effect = [
                [f"session:{session_id}:metadata"],
                [f"session:{session_id}:state:v1", f"session:{session_id}:state:v2"],
                [f"session:{session_id}:context"]
            ]
            mock_redis.delete.return_value = 4
            
            result = await store.cleanup_session(session_id)
            
            assert result is True
            mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_increment_edit_count(self, mock_redis):
        """Test incrementing edit count for a session."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock successful Redis operation
            mock_redis.hincrby.return_value = 2
            
            result = await store.increment_edit_count(session_id)
            
            assert result is True
            expected_key = f"session:{session_id}:metadata"
            mock_redis.hincrby.assert_called_with(expected_key, "total_edits", 1)
    
    @pytest.mark.asyncio
    async def test_update_session_activity(self, mock_redis):
        """Test updating session activity timestamp."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-123"
            
            # Mock successful Redis operation
            mock_redis.hset.return_value = True
            
            result = await store.update_session_activity(session_id)
            
            assert result is True
            expected_key = f"session:{session_id}:metadata"
            mock_redis.hset.assert_called()
            # Verify the call includes the session key and last_activity field
            call_args = mock_redis.hset.call_args
            assert call_args[0][0] == expected_key
            assert call_args[0][1] == "last_activity"
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, mock_redis):
        """Test getting all sessions for a user."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            user_id = "user-456"
            
            # Mock Redis response
            mock_redis.smembers.return_value = {"session-1", "session-2", "session-3"}
            
            result = await store.get_user_sessions(user_id)
            
            assert len(result) == 3
            assert "session-1" in result
            assert "session-2" in result
            assert "session-3" in result
    
    def test_redis_property_without_connection(self):
        """Test that accessing redis property without connection raises error."""
        store = RedisStateStore()
        
        with pytest.raises(RuntimeError, match="Redis connection not initialized"):
            _ = store.redis