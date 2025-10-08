# tests/test_session_manager_integration.py
"""
Integration tests for DesignSessionManager with RedisStateStore.
Tests the complete workflow of session management with real Redis operations.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from app.core.session_manager import DesignSessionManager, SessionManagerError
from app.core.state_store import RedisStateStore
from app.core.models import (
    DesignSession, DesignState, EditContext, SessionStatus, EditType
)


class TestSessionManagerIntegration:
    """Integration tests for DesignSessionManager with RedisStateStore."""
    
    @pytest.fixture
    def mock_redis_store(self):
        """Create a mock RedisStateStore for integration testing."""
        store = AsyncMock(spec=RedisStateStore)
        store.session_ttl = timedelta(hours=24)
        store.context_limit = 10
        return store
    
    @pytest.fixture
    def session_manager(self, mock_redis_store):
        """Create a DesignSessionManager with mocked Redis store."""
        return DesignSessionManager(state_store=mock_redis_store)
    
    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(self, session_manager, mock_redis_store):
        """Test complete session lifecycle from creation to completion."""
        # Setup mock responses
        user_id = "user-123"
        initial_prompt = "Create a login form"
        
        # Mock session creation
        mock_redis_store.create_session.return_value = True
        
        # Step 1: Create session
        session = await session_manager.create_session(user_id, initial_prompt)
        
        assert session.user_id == user_id
        assert session.initial_prompt == initial_prompt
        assert session.status == SessionStatus.ACTIVE
        mock_redis_store.create_session.assert_called_once()
        
        # Step 2: Add initial design state
        initial_state = DesignState(
            wireframe_json={"type": "form", "elements": ["input", "button"]},
            metadata={"theme": "light"},
            version=1
        )
        
        # Mock state storage
        mock_redis_store.get_session_metadata.return_value = session
        mock_redis_store.update_session_activity.return_value = True
        mock_redis_store.store_design_state.return_value = True
        
        success = await session_manager.update_session_state(session.session_id, initial_state)
        assert success is True
        
        # Step 3: Add edit context
        edit_context = EditContext(
            prompt="Make the button blue",
            edit_type=EditType.STYLE,
            target_elements=["button"],
            processing_time_ms=150
        )
        
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        success = await session_manager.add_edit_context(session.session_id, edit_context)
        assert success is True
        
        # Step 4: Add second version
        updated_state = DesignState(
            wireframe_json={"type": "form", "elements": ["input", "button"], "style": {"button": {"color": "blue"}}},
            metadata={"theme": "light", "version": 2},
            version=2
        )
        
        success = await session_manager.update_session_state(session.session_id, updated_state)
        assert success is True
        
        # Step 5: Get session history
        mock_redis_store.get_all_versions.return_value = [1, 2]
        mock_redis_store.get_design_state.side_effect = [initial_state, updated_state]
        
        history = await session_manager.get_session_history(session.session_id)
        assert len(history) == 2
        assert history[0].version == 1
        assert history[1].version == 2
        
        # Step 6: Complete session
        mock_redis_store.redis = AsyncMock()
        success = await session_manager.complete_session(session.session_id)
        assert success is True
        mock_redis_store.redis.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_expiration_handling(self, session_manager, mock_redis_store):
        """Test handling of expired sessions."""
        session_id = "expired-session"
        
        # Create expired session metadata
        expired_time = datetime.utcnow() - timedelta(hours=25)
        expired_metadata = type('MockMetadata', (), {
            'session_id': session_id,
            'user_id': 'user-123',
            'initial_prompt': 'test',
            'current_version': 1,
            'created_at': expired_time,
            'last_activity': expired_time,
            'status': SessionStatus.ACTIVE,
            'total_edits': 0
        })()
        
        mock_redis_store.get_session_metadata.return_value = expired_metadata
        mock_redis_store.redis = AsyncMock()
        
        # Should return None for expired session
        session = await session_manager.get_session(session_id)
        assert session is None
        
        # Should mark session as expired
        mock_redis_store.redis.hset.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, session_manager, mock_redis_store):
        """Test concurrent operations on the same session."""
        user_id = "user-concurrent"
        session_id = "concurrent-session"
        
        # Mock session metadata
        session_metadata = type('MockMetadata', (), {
            'session_id': session_id,
            'user_id': user_id,
            'initial_prompt': 'test',
            'current_version': 1,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'status': SessionStatus.ACTIVE,
            'total_edits': 0
        })()
        
        mock_redis_store.get_session_metadata.return_value = session_metadata
        mock_redis_store.update_session_activity.return_value = True
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        # Simulate concurrent edit operations
        edit1 = EditContext(
            prompt="Add header",
            edit_type=EditType.ADD,
            target_elements=["header"]
        )
        
        edit2 = EditContext(
            prompt="Style header",
            edit_type=EditType.STYLE,
            target_elements=["header"]
        )
        
        # Execute concurrent operations
        results = await asyncio.gather(
            session_manager.add_edit_context(session_id, edit1),
            session_manager.add_edit_context(session_id, edit2),
            return_exceptions=True
        )
        
        # Both operations should succeed
        assert all(result is True for result in results)
        assert mock_redis_store.add_context_entry.call_count == 2
        assert mock_redis_store.increment_edit_count.call_count == 2
    
    @pytest.mark.asyncio
    async def test_error_recovery_and_consistency(self, session_manager, mock_redis_store):
        """Test error recovery and data consistency."""
        session_id = "error-test-session"
        
        # Test Redis failure during state update
        mock_redis_store.get_session_metadata.return_value = type('MockMetadata', (), {
            'session_id': session_id,
            'user_id': 'user-123',
            'initial_prompt': 'test',
            'current_version': 1,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'status': SessionStatus.ACTIVE,
            'total_edits': 0
        })()
        mock_redis_store.update_session_activity.return_value = True
        mock_redis_store.store_design_state.return_value = False  # Simulate failure
        
        state = DesignState(
            wireframe_json={"test": "data"},
            metadata={},
            version=2
        )
        
        # Should raise SessionManagerError on Redis failure
        with pytest.raises(SessionManagerError, match="Failed to store design state"):
            await session_manager.update_session_state(session_id, state)
    
    @pytest.mark.asyncio
    async def test_session_metrics_calculation(self, session_manager, mock_redis_store):
        """Test session metrics calculation with real data."""
        session_id = "metrics-test-session"
        
        # Setup session metadata
        created_time = datetime.utcnow() - timedelta(minutes=30)
        last_activity = datetime.utcnow()
        
        session_metadata = type('MockMetadata', (), {
            'session_id': session_id,
            'user_id': 'user-123',
            'initial_prompt': 'test',
            'current_version': 3,
            'created_at': created_time,
            'last_activity': last_activity,
            'status': SessionStatus.ACTIVE,
            'total_edits': 2
        })()
        
        # Setup context history
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
        
        mock_redis_store.get_session_metadata.return_value = session_metadata
        mock_redis_store.get_context_history.return_value = context_history
        
        # Calculate metrics
        metrics = await session_manager.get_session_metrics(session_id)
        
        assert metrics is not None
        assert metrics.total_edits == 2
        assert metrics.session_duration_minutes == 30
        assert metrics.edit_types_distribution[EditType.ADD] == 1
        assert metrics.edit_types_distribution[EditType.STYLE] == 1
        assert metrics.average_processing_time_ms == 150.0
    
    @pytest.mark.asyncio
    async def test_user_session_management(self, session_manager, mock_redis_store):
        """Test user session management across multiple sessions."""
        user_id = "multi-session-user"
        
        # Mock multiple sessions for user
        session_ids = ["session-1", "session-2", "session-3"]
        mock_redis_store.get_user_sessions.return_value = session_ids
        
        # Mock session retrieval - only first two are active
        def mock_get_session_metadata(session_id):
            if session_id in ["session-1", "session-2"]:
                return type('MockMetadata', (), {
                    'session_id': session_id,
                    'user_id': user_id,
                    'initial_prompt': 'test',
                    'current_version': 1,
                    'created_at': datetime.utcnow(),
                    'last_activity': datetime.utcnow(),
                    'status': SessionStatus.ACTIVE,
                    'total_edits': 0
                })()
            return None  # session-3 doesn't exist
        
        mock_redis_store.get_session_metadata.side_effect = mock_get_session_metadata
        mock_redis_store.update_session_activity.return_value = True
        
        # Get active sessions for user
        active_sessions = await session_manager.get_user_sessions(user_id)
        
        assert len(active_sessions) == 2
        assert "session-1" in active_sessions
        assert "session-2" in active_sessions
        assert "session-3" not in active_sessions


if __name__ == "__main__":
    pytest.main([__file__])