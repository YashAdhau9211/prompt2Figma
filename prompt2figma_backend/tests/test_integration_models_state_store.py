# tests/test_integration_models_state_store.py
"""
Integration tests for models and state store working together.
Tests the complete flow of creating sessions, storing states, and managing context.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
import json

from app.core.state_store import RedisStateStore
from app.core.models import (
    DesignSession, DesignState, EditContext, SessionMetadata,
    EditType, SessionStatus
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis connection for integration tests."""
    mock = AsyncMock()
    mock.ping = AsyncMock()
    mock.hset = AsyncMock(return_value=True)
    mock.hgetall = AsyncMock()
    mock.sadd = AsyncMock(return_value=True)
    mock.expire = AsyncMock(return_value=True)
    mock.lpush = AsyncMock(return_value=1)
    mock.ltrim = AsyncMock(return_value=True)
    mock.lrange = AsyncMock()
    mock.keys = AsyncMock()
    mock.delete = AsyncMock(return_value=1)
    mock.smembers = AsyncMock()
    mock.hincrby = AsyncMock(return_value=1)
    mock.close = AsyncMock()
    return mock


class TestModelsStateStoreIntegration:
    """Integration tests for models and state store."""
    
    @pytest.mark.asyncio
    async def test_complete_session_workflow(self, mock_redis):
        """Test a complete workflow from session creation to context management."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            # 1. Create a design session
            session = DesignSession(
                user_id="user-123",
                initial_prompt="Create a login form"
            )
            
            # Mock session creation success
            result = await store.create_session(session)
            assert result is True
            
            # 2. Create and store initial design state
            initial_state = DesignState(
                wireframe_json={"type": "form", "elements": []},
                metadata={"created_by": "ai", "version": "1.0"},
                version=1
            )
            
            result = await store.store_design_state(session.session_id, 1, initial_state)
            assert result is True
            
            # 3. Add context for first edit
            edit_context = EditContext(
                prompt="Add username input field",
                edit_type=EditType.ADD,
                target_elements=["form"],
                processing_time_ms=200
            )
            
            result = await store.add_context_entry(session.session_id, edit_context)
            assert result is True
            
            # 4. Create and store updated design state
            updated_state = DesignState(
                wireframe_json={
                    "type": "form", 
                    "elements": [{"type": "input", "name": "username"}]
                },
                metadata={"created_by": "ai", "version": "1.1"},
                version=2
            )
            
            result = await store.store_design_state(session.session_id, 2, updated_state)
            assert result is True
            
            # 5. Increment edit count
            result = await store.increment_edit_count(session.session_id)
            assert result is True
            
            # Verify all Redis operations were called
            assert mock_redis.hset.call_count >= 4  # Session + 2 states + edit count
            assert mock_redis.lpush.call_count == 1  # Context entry
            assert mock_redis.hincrby.call_count == 1  # Edit count increment
    
    @pytest.mark.asyncio
    async def test_session_retrieval_and_state_consistency(self, mock_redis):
        """Test that retrieved sessions and states maintain data consistency."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-456"
            
            # Mock session metadata retrieval
            mock_redis.hgetall.return_value = {
                "session_id": session_id,
                "user_id": "user-789",
                "initial_prompt": "Create a dashboard",
                "current_version": "3",
                "created_at": datetime(2024, 1, 1, 10, 0, 0).isoformat(),
                "last_activity": datetime(2024, 1, 1, 11, 0, 0).isoformat(),
                "status": SessionStatus.ACTIVE.value,
                "total_edits": "2"
            }
            
            # Retrieve session metadata
            metadata = await store.get_session_metadata(session_id)
            
            assert metadata is not None
            assert isinstance(metadata, SessionMetadata)
            assert metadata.session_id == session_id
            assert metadata.user_id == "user-789"
            assert metadata.current_version == 3
            assert metadata.total_edits == 2
            assert metadata.status == SessionStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_context_history_with_multiple_edits(self, mock_redis):
        """Test context history management with multiple edit types."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-789"
            
            # Create multiple edit contexts
            contexts = [
                EditContext(
                    prompt="Add header",
                    edit_type=EditType.ADD,
                    target_elements=["page"],
                    processing_time_ms=150
                ),
                EditContext(
                    prompt="Change button color to blue",
                    edit_type=EditType.STYLE,
                    target_elements=["button-1"],
                    processing_time_ms=120
                ),
                EditContext(
                    prompt="Move sidebar to right",
                    edit_type=EditType.LAYOUT,
                    target_elements=["sidebar"],
                    processing_time_ms=180
                )
            ]
            
            # Add all contexts
            for context in contexts:
                result = await store.add_context_entry(session_id, context)
                assert result is True
            
            # Mock context retrieval
            context_data_list = []
            for context in reversed(contexts):  # Redis LPUSH puts newest first
                context_data = {
                    "prompt": context.prompt,
                    "edit_type": context.edit_type.value,
                    "target_elements": json.dumps(context.target_elements),
                    "timestamp": context.timestamp.isoformat(),
                    "processing_time_ms": context.processing_time_ms
                }
                context_data_list.append(json.dumps(context_data))
            
            mock_redis.lrange.return_value = context_data_list
            
            # Retrieve context history
            retrieved_contexts = await store.get_context_history(session_id)
            
            assert len(retrieved_contexts) == 3
            
            # Verify context data integrity
            for i, context in enumerate(retrieved_contexts):
                assert isinstance(context, EditContext)
                assert context.prompt == contexts[2-i].prompt  # Reversed order
                assert context.edit_type == contexts[2-i].edit_type
                assert context.target_elements == contexts[2-i].target_elements
    
    @pytest.mark.asyncio
    async def test_version_management_consistency(self, mock_redis):
        """Test that version management maintains consistency across operations."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session_id = "test-session-versions"
            
            # Mock version keys retrieval
            mock_redis.keys.return_value = [
                f"session:{session_id}:state:v1",
                f"session:{session_id}:state:v2",
                f"session:{session_id}:state:v3",
                f"session:{session_id}:state:v5",  # Gap in versions
                f"session:{session_id}:state:v4"
            ]
            
            # Get all versions
            versions = await store.get_all_versions(session_id)
            
            # Should be sorted despite Redis returning them out of order
            assert versions == [1, 2, 3, 4, 5]
    
    @pytest.mark.asyncio
    async def test_error_handling_preserves_data_integrity(self, mock_redis):
        """Test that errors don't corrupt data and are handled gracefully."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            session = DesignSession(
                user_id="user-error-test",
                initial_prompt="Test error handling"
            )
            
            # Simulate Redis error during session creation
            mock_redis.hset.side_effect = Exception("Redis connection lost")
            
            result = await store.create_session(session)
            assert result is False  # Should return False, not raise exception
            
            # Reset mock for successful operation
            mock_redis.hset.side_effect = None
            mock_redis.hset.return_value = True
            
            # Should be able to retry successfully
            result = await store.create_session(session)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_model_serialization_through_state_store(self, mock_redis):
        """Test that models serialize/deserialize correctly through the state store."""
        with patch('redis.asyncio.from_url', return_value=mock_redis):
            store = RedisStateStore()
            await store.connect()
            
            # Create a complex design state with nested data
            complex_wireframe = {
                "type": "container",
                "children": [
                    {
                        "type": "header",
                        "text": "Welcome",
                        "styles": {"color": "#333", "fontSize": "24px"}
                    },
                    {
                        "type": "form",
                        "children": [
                            {"type": "input", "name": "email", "required": True},
                            {"type": "button", "text": "Submit", "onClick": "handleSubmit"}
                        ]
                    }
                ]
            }
            
            state = DesignState(
                wireframe_json=complex_wireframe,
                metadata={
                    "created_by": "ai",
                    "complexity_score": 7.5,
                    "tags": ["form", "header", "interactive"]
                },
                version=1
            )
            
            session_id = "test-serialization"
            
            # Store the state
            result = await store.store_design_state(session_id, 1, state)
            assert result is True
            
            # Mock retrieval with the same data
            mock_redis.hgetall.return_value = {
                "wireframe_json": json.dumps(complex_wireframe),
                "metadata": json.dumps(state.metadata),
                "created_at": state.created_at.isoformat(),
                "version": "1"
            }
            
            # Retrieve and verify
            retrieved_state = await store.get_design_state(session_id, 1)
            
            assert retrieved_state is not None
            assert retrieved_state.wireframe_json == complex_wireframe
            assert retrieved_state.metadata == state.metadata
            assert retrieved_state.version == 1
            
            # Verify nested data integrity
            assert retrieved_state.wireframe_json["children"][0]["text"] == "Welcome"
            assert retrieved_state.wireframe_json["children"][1]["children"][0]["required"] is True
            assert retrieved_state.metadata["complexity_score"] == 7.5
            assert "interactive" in retrieved_state.metadata["tags"]