# tests/test_session_manager.py
"""
Unit tests for the DesignSessionManager class.
Tests session lifecycle management, state operations, and error handling.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from app.core.session_manager import DesignSessionManager, SessionManagerError
from app.core.state_store import RedisStateStore
from app.core.models import (
    DesignSession, DesignState, SessionMetadata, EditContext, 
    SessionStatus, EditType, SessionMetrics
)


class TestDesignSessionManager:
    """Test suite for DesignSessionManager."""
    
    @pytest.fixture
    def mock_state_store(self):
        """Create a mock RedisStateStore for testing."""
        return AsyncMock(spec=RedisStateStore)
    
    @pytest.fixture
    def session_manager(self, mock_state_store):
        """Create a DesignSessionManager instance with mocked dependencies."""
        return DesignSessionManager(state_store=mock_state_store, session_timeout_hours=24)
    
    @pytest.fixture
    def sample_session(self):
        """Create a sample DesignSession for testing."""
        return DesignSession(
            session_id="test-session-123",
            user_id="user-456",
            initial_prompt="Create a login form",
            current_version=1,
            status=SessionStatus.ACTIVE
        )
    
    @pytest.fixture
    def sample_design_state(self):
        """Create a sample DesignState for testing."""
        return DesignState(
            wireframe_json={"type": "form", "elements": ["input", "button"]},
            metadata={"theme": "dark"},
            version=1
        )
    
    @pytest.fixture
    def sample_edit_context(self):
        """Create a sample EditContext for testing."""
        return EditContext(
            prompt="Make the button blue",
            edit_type=EditType.STYLE,
            target_elements=["button"],
            processing_time_ms=150
        )


class TestSessionCreation(TestDesignSessionManager):
    """Test session creation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_session_success(self, session_manager, mock_state_store):
        """Test successful session creation."""
        # Arrange
        mock_state_store.create_session.return_value = True
        user_id = "user-123"
        initial_prompt = "Create a dashboard"
        
        # Act
        session = await session_manager.create_session(user_id, initial_prompt)
        
        # Assert
        assert session.user_id == user_id
        assert session.initial_prompt == initial_prompt
        assert session.current_version == 1
        assert session.status == SessionStatus.ACTIVE
        assert session.session_id is not None
        mock_state_store.create_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_redis_failure(self, session_manager, mock_state_store):
        """Test session creation when Redis storage fails."""
        # Arrange
        mock_state_store.create_session.return_value = False
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Failed to store session"):
            await session_manager.create_session("user-123", "test prompt")
    
    @pytest.mark.asyncio
    async def test_create_session_exception(self, session_manager, mock_state_store):
        """Test session creation when an exception occurs."""
        # Arrange
        mock_state_store.create_session.side_effect = Exception("Redis connection error")
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Session creation failed"):
            await session_manager.create_session("user-123", "test prompt")


class TestSessionRetrieval(TestDesignSessionManager):
    """Test session retrieval functionality."""
    
    @pytest.mark.asyncio
    async def test_get_session_success(self, session_manager, mock_state_store, sample_session):
        """Test successful session retrieval."""
        # Arrange
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=sample_session.current_version,
            created_at=sample_session.created_at,
            last_activity=datetime.utcnow(),  # Recent activity
            status=sample_session.status,
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        
        # Act
        result = await session_manager.get_session(sample_session.session_id)
        
        # Assert
        assert result is not None
        assert result.session_id == sample_session.session_id
        assert result.user_id == sample_session.user_id
        mock_state_store.update_session_activity.assert_called_once_with(sample_session.session_id)
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager, mock_state_store):
        """Test session retrieval when session doesn't exist."""
        # Arrange
        mock_state_store.get_session_metadata.return_value = None
        
        # Act
        result = await session_manager.get_session("nonexistent-session")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_session_expired(self, session_manager, mock_state_store, sample_session):
        """Test session retrieval when session has expired."""
        # Arrange
        expired_time = datetime.utcnow() - timedelta(hours=25)  # Expired
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=sample_session.current_version,
            created_at=expired_time,
            last_activity=expired_time,
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.redis = AsyncMock()
        
        # Act
        result = await session_manager.get_session(sample_session.session_id)
        
        # Assert
        assert result is None
        # Should mark session as expired
        mock_state_store.redis.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_exception(self, session_manager, mock_state_store):
        """Test session retrieval when an exception occurs."""
        # Arrange
        mock_state_store.get_session_metadata.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Session retrieval failed"):
            await session_manager.get_session("test-session")


class TestSessionHistory(TestDesignSessionManager):
    """Test session history functionality."""
    
    @pytest.mark.asyncio
    async def test_get_session_history_success(self, session_manager, mock_state_store, sample_session):
        """Test successful session history retrieval."""
        # Arrange
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=2,
            created_at=sample_session.created_at,
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=1
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.get_all_versions.return_value = [1, 2]
        
        # Mock design states
        state1 = DesignState(wireframe_json={"v": 1}, metadata={}, version=1)
        state2 = DesignState(wireframe_json={"v": 2}, metadata={}, version=2)
        mock_state_store.get_design_state.side_effect = [state1, state2]
        
        # Act
        history = await session_manager.get_session_history(sample_session.session_id)
        
        # Assert
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2
        assert mock_state_store.get_design_state.call_count == 2
    
    @pytest.mark.asyncio
    async def test_get_session_history_session_not_found(self, session_manager, mock_state_store):
        """Test session history when session doesn't exist."""
        # Arrange
        mock_state_store.get_session_metadata.return_value = None
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Session .* not found or expired"):
            await session_manager.get_session_history("nonexistent-session")
    
    @pytest.mark.asyncio
    async def test_get_session_history_no_versions(self, session_manager, mock_state_store, sample_session):
        """Test session history when no versions exist."""
        # Arrange
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.get_all_versions.return_value = []
        
        # Act
        history = await session_manager.get_session_history(sample_session.session_id)
        
        # Assert
        assert history == []


class TestSessionStateUpdate(TestDesignSessionManager):
    """Test session state update functionality."""
    
    @pytest.mark.asyncio
    async def test_update_session_state_success(self, session_manager, mock_state_store, sample_session, sample_design_state):
        """Test successful session state update."""
        # Arrange
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.store_design_state.return_value = True
        
        # Act
        result = await session_manager.update_session_state(sample_session.session_id, sample_design_state)
        
        # Assert
        assert result is True
        mock_state_store.store_design_state.assert_called_once_with(
            sample_session.session_id, sample_design_state.version, sample_design_state
        )
    
    @pytest.mark.asyncio
    async def test_update_session_state_session_not_found(self, session_manager, mock_state_store, sample_design_state):
        """Test state update when session doesn't exist."""
        # Arrange
        mock_state_store.get_session_metadata.return_value = None
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Session .* not found or expired"):
            await session_manager.update_session_state("nonexistent-session", sample_design_state)
    
    @pytest.mark.asyncio
    async def test_update_session_state_inactive_session(self, session_manager, mock_state_store, sample_design_state):
        """Test state update when session is inactive."""
        # Arrange
        metadata = SessionMetadata(
            session_id="test-session",
            user_id="user-123",
            initial_prompt="test",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.COMPLETED,  # Inactive
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Cannot update inactive session"):
            await session_manager.update_session_state("test-session", sample_design_state)


class TestEditContext(TestDesignSessionManager):
    """Test edit context functionality."""
    
    @pytest.mark.asyncio
    async def test_add_edit_context_success(self, session_manager, mock_state_store, sample_session, sample_edit_context):
        """Test successful edit context addition."""
        # Arrange
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.add_context_entry.return_value = True
        mock_state_store.increment_edit_count.return_value = True
        
        # Act
        result = await session_manager.add_edit_context(sample_session.session_id, sample_edit_context)
        
        # Assert
        assert result is True
        mock_state_store.add_context_entry.assert_called_once_with(sample_session.session_id, sample_edit_context)
        mock_state_store.increment_edit_count.assert_called_once_with(sample_session.session_id)
    
    @pytest.mark.asyncio
    async def test_add_edit_context_session_not_found(self, session_manager, mock_state_store, sample_edit_context):
        """Test edit context addition when session doesn't exist."""
        # Arrange
        mock_state_store.get_session_metadata.return_value = None
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Session .* not found or expired"):
            await session_manager.add_edit_context("nonexistent-session", sample_edit_context)


class TestSessionCompletion(TestDesignSessionManager):
    """Test session completion functionality."""
    
    @pytest.mark.asyncio
    async def test_complete_session_success(self, session_manager, mock_state_store, sample_session):
        """Test successful session completion."""
        # Arrange
        metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.redis = AsyncMock()
        
        # Act
        result = await session_manager.complete_session(sample_session.session_id)
        
        # Assert
        assert result is True
        mock_state_store.redis.hset.assert_called_once_with(
            f"session:{sample_session.session_id}:metadata", 
            "status", 
            SessionStatus.COMPLETED.value
        )
    
    @pytest.mark.asyncio
    async def test_complete_session_not_found(self, session_manager, mock_state_store):
        """Test session completion when session doesn't exist."""
        # Arrange
        mock_state_store.get_session_metadata.return_value = None
        
        # Act & Assert
        with pytest.raises(SessionManagerError, match="Session .* not found"):
            await session_manager.complete_session("nonexistent-session")


class TestSessionCleanup(TestDesignSessionManager):
    """Test session cleanup functionality."""
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager, mock_state_store):
        """Test cleanup of expired sessions."""
        # Arrange
        mock_state_store.cleanup_expired_sessions.return_value = 3
        
        # Act
        cleaned_count = await session_manager.cleanup_expired_sessions()
        
        # Assert
        assert cleaned_count == 3
        mock_state_store.cleanup_expired_sessions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, session_manager, mock_state_store):
        """Test getting user sessions."""
        # Arrange
        user_id = "user-123"
        session_ids = ["session-1", "session-2", "session-3"]
        mock_state_store.get_user_sessions.return_value = session_ids
        
        # Mock session retrieval - only first two are active
        active_session = DesignSession(
            session_id="session-1",
            user_id=user_id,
            initial_prompt="test",
            status=SessionStatus.ACTIVE
        )
        
        def mock_get_session(session_id):
            if session_id in ["session-1", "session-2"]:
                return active_session
            return None  # session-3 is expired/not found
        
        # We need to mock the internal get_session calls
        with patch.object(session_manager, 'get_session', side_effect=mock_get_session):
            # Act
            active_sessions = await session_manager.get_user_sessions(user_id)
        
        # Assert
        assert len(active_sessions) == 2
        assert "session-1" in active_sessions
        assert "session-2" in active_sessions
        assert "session-3" not in active_sessions


class TestSessionMetrics(TestDesignSessionManager):
    """Test session metrics functionality."""
    
    @pytest.mark.asyncio
    async def test_get_session_metrics_success(self, session_manager, mock_state_store):
        """Test successful session metrics calculation."""
        # Arrange
        session_id = "test-session"
        created_time = datetime.utcnow() - timedelta(minutes=30)
        last_activity = datetime.utcnow()
        
        metadata = SessionMetadata(
            session_id=session_id,
            user_id="user-123",
            initial_prompt="test",
            current_version=3,
            created_at=created_time,
            last_activity=last_activity,
            status=SessionStatus.ACTIVE,
            total_edits=2
        )
        
        context_history = [
            EditContext(
                prompt="Add button",
                edit_type=EditType.ADD,
                target_elements=["button"],
                processing_time_ms=100
            ),
            EditContext(
                prompt="Style button",
                edit_type=EditType.STYLE,
                target_elements=["button"],
                processing_time_ms=200
            )
        ]
        
        mock_state_store.get_session_metadata.return_value = metadata
        mock_state_store.get_context_history.return_value = context_history
        
        # Act
        metrics = await session_manager.get_session_metrics(session_id)
        
        # Assert
        assert metrics is not None
        assert metrics.total_edits == 2
        assert metrics.session_duration_minutes == 30
        assert metrics.edit_types_distribution[EditType.ADD] == 1
        assert metrics.edit_types_distribution[EditType.STYLE] == 1
        assert metrics.average_processing_time_ms == 150.0
    
    @pytest.mark.asyncio
    async def test_get_session_metrics_not_found(self, session_manager, mock_state_store):
        """Test session metrics when session doesn't exist."""
        # Arrange
        mock_state_store.get_session_metadata.return_value = None
        
        # Act
        metrics = await session_manager.get_session_metrics("nonexistent-session")
        
        # Assert
        assert metrics is None


class TestErrorHandling(TestDesignSessionManager):
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_session_manager_error_propagation(self, session_manager, mock_state_store):
        """Test that SessionManagerError is properly propagated."""
        # Arrange
        mock_state_store.get_session_metadata.side_effect = Exception("Redis error")
        
        # Act & Assert
        with pytest.raises(SessionManagerError):
            await session_manager.get_session("test-session")
    
    def test_is_session_expired(self, session_manager):
        """Test session expiration logic."""
        # Arrange
        now = datetime.utcnow()
        
        # Recent activity - not expired
        recent_metadata = SessionMetadata(
            session_id="test",
            user_id="user",
            initial_prompt="test",
            current_version=1,
            created_at=now,
            last_activity=now - timedelta(hours=1),  # 1 hour ago
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        # Old activity - expired
        old_metadata = SessionMetadata(
            session_id="test",
            user_id="user",
            initial_prompt="test",
            current_version=1,
            created_at=now,
            last_activity=now - timedelta(hours=25),  # 25 hours ago
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        # Act & Assert
        assert not session_manager._is_session_expired(recent_metadata)
        assert session_manager._is_session_expired(old_metadata)


if __name__ == "__main__":
    pytest.main([__file__])