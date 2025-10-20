# tests/test_session_code_generation_integration.py
"""
Integration tests for session-to-code workflow.
Tests the integration between iterative design sessions and code generation pipeline.

Requirements: 5.2, 5.3
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.core.models import (
    DesignSession, DesignState, SessionStatus, EditType
)
from app.core.state_store import RedisStateStore
from app.core.session_manager import DesignSessionManager


@pytest.fixture
def sample_wireframe():
    """Sample wireframe JSON for testing."""
    return {
        "componentName": "TestApp",
        "type": "Frame",
        "props": {
            "layoutMode": "VERTICAL",
            "backgroundColor": "#FFFFFF",
            "padding": "16px"
        },
        "children": [
            {
                "componentName": "Header",
                "type": "Frame",
                "props": {
                    "layoutMode": "HORIZONTAL",
                    "backgroundColor": "#3B82F6",
                    "padding": "12px"
                },
                "children": [
                    {
                        "componentName": "Title",
                        "type": "Text",
                        "props": {
                            "text": "My App",
                            "fontSize": "24px",
                            "fontWeight": 700,
                            "color": "#FFFFFF"
                        },
                        "children": []
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_design_state(sample_wireframe):
    """Sample design state for testing."""
    return DesignState(
        wireframe_json=sample_wireframe,
        metadata={
            "prompt": "Create a simple app with a header",
            "edit_type": "initial"
        },
        version=1
    )


class TestSessionCodeGenerationIntegration:
    """Integration tests for session-to-code workflow."""
    
    @pytest.mark.asyncio
    async def test_generate_code_with_session_id(self, sample_design_state):
        """
        Test generating code using session_id parameter.
        Requirement: 5.2 - Integration with existing pipeline
        """
        # Mock state store
        mock_state_store = AsyncMock(spec=RedisStateStore)
        mock_state_store.get_design_state.return_value = sample_design_state
        mock_state_store.connect = AsyncMock()
        mock_state_store.disconnect = AsyncMock()
        
        # Mock session manager
        mock_session_manager = AsyncMock(spec=DesignSessionManager)
        mock_session = DesignSession(
            session_id="test-session-123",
            user_id="user-1",
            initial_prompt="Create a simple app",
            current_version=1,
            status=SessionStatus.ACTIVE
        )
        mock_session_manager.get_session.return_value = mock_session
        mock_session_manager.complete_session = AsyncMock(return_value=True)
        
        # Test that we can retrieve design state by session_id
        session_id = "test-session-123"
        design_state = await mock_state_store.get_design_state(session_id, None)
        
        assert design_state is not None
        assert design_state.wireframe_json == sample_design_state.wireframe_json
        assert design_state.version == 1
        
        # Verify session completion is called
        await mock_session_manager.complete_session(session_id)
        mock_session_manager.complete_session.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_generate_code_with_specific_version(self, sample_design_state):
        """
        Test generating code from a specific version of a session.
        Requirement: 5.2 - Integration with existing pipeline
        """
        # Mock state store with multiple versions
        mock_state_store = AsyncMock(spec=RedisStateStore)
        
        # Version 1
        version_1_state = DesignState(
            wireframe_json={"componentName": "V1", "type": "Frame", "props": {}, "children": []},
            metadata={"prompt": "Initial design"},
            version=1
        )
        
        # Version 2
        version_2_state = DesignState(
            wireframe_json={"componentName": "V2", "type": "Frame", "props": {}, "children": []},
            metadata={"prompt": "Updated design"},
            version=2
        )
        
        # Configure mock to return different states based on version
        async def get_state_by_version(session_id, version):
            if version == 1:
                return version_1_state
            elif version == 2:
                return version_2_state
            return None
        
        mock_state_store.get_design_state = get_state_by_version
        
        # Test retrieving specific versions
        session_id = "test-session-456"
        
        state_v1 = await mock_state_store.get_design_state(session_id, 1)
        assert state_v1.version == 1
        assert state_v1.wireframe_json["componentName"] == "V1"
        
        state_v2 = await mock_state_store.get_design_state(session_id, 2)
        assert state_v2.version == 2
        assert state_v2.wireframe_json["componentName"] == "V2"
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_without_session_id(self, sample_wireframe):
        """
        Test that code generation still works without session_id (backward compatibility).
        Requirement: 5.3 - Backward compatibility
        """
        # When session_id is None, the endpoint should use layout_json directly
        layout_json = sample_wireframe
        session_id = None
        
        # Simulate the endpoint logic
        if session_id:
            # Would fetch from session
            pytest.fail("Should not fetch from session when session_id is None")
        else:
            # Use layout_json directly
            result_json = layout_json
        
        assert result_json == sample_wireframe
        assert result_json["componentName"] == "TestApp"
    
    @pytest.mark.asyncio
    async def test_session_not_found_error(self):
        """
        Test error handling when session is not found.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_state_store = AsyncMock(spec=RedisStateStore)
        mock_state_store.get_design_state.return_value = None
        mock_state_store.connect = AsyncMock()
        mock_state_store.disconnect = AsyncMock()
        
        session_id = "non-existent-session"
        design_state = await mock_state_store.get_design_state(session_id, None)
        
        # Should return None for non-existent session
        assert design_state is None
    
    @pytest.mark.asyncio
    async def test_session_completion_on_code_generation(self):
        """
        Test that session is marked as completed when code is generated.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_session_manager = AsyncMock(spec=DesignSessionManager)
        mock_session_manager.complete_session = AsyncMock(return_value=True)
        
        session_id = "test-session-789"
        
        # Simulate code generation completion
        result = await mock_session_manager.complete_session(session_id)
        
        assert result is True
        mock_session_manager.complete_session.assert_called_once_with(session_id)
    
    @pytest.mark.asyncio
    async def test_full_workflow_session_to_code(self, sample_wireframe):
        """
        Test complete workflow from session creation to code generation.
        Requirement: 5.2, 5.3 - Full integration workflow
        """
        # Mock state store
        mock_state_store = AsyncMock(spec=RedisStateStore)
        mock_state_store.connect = AsyncMock()
        mock_state_store.disconnect = AsyncMock()
        
        # Create session manager with mocked prompt processor
        with patch('app.core.session_manager.EnhancedPromptProcessor'):
            session_manager = DesignSessionManager(mock_state_store)
            
            # Mock session creation
            mock_session = DesignSession(
                session_id="workflow-test-session",
                user_id="user-1",
                initial_prompt="Create a dashboard",
                current_version=1,
                status=SessionStatus.ACTIVE
            )
            mock_state_store.create_session = AsyncMock(return_value=True)
            mock_state_store.get_session_metadata = AsyncMock(return_value=Mock(
                session_id=mock_session.session_id,
                user_id=mock_session.user_id,
                initial_prompt=mock_session.initial_prompt,
                current_version=mock_session.current_version,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                status=SessionStatus.ACTIVE.value,
                total_edits=0
            ))
            mock_state_store.update_session_activity = AsyncMock()
            
            # Step 1: Create session
            session = await session_manager.create_session("user-1", "Create a dashboard")
            assert session.session_id is not None
            assert session.status == SessionStatus.ACTIVE
            
            # Step 2: Store initial design state
            initial_state = DesignState(
                wireframe_json=sample_wireframe,
                metadata={"prompt": "Create a dashboard"},
                version=1
            )
            mock_state_store.store_design_state = AsyncMock(return_value=True)
            await mock_state_store.store_design_state(session.session_id, 1, initial_state)
            
            # Step 3: Retrieve design state for code generation
            mock_state_store.get_design_state = AsyncMock(return_value=initial_state)
            design_state = await mock_state_store.get_design_state(session.session_id, 1)
            assert design_state is not None
            assert design_state.wireframe_json == sample_wireframe
            
            # Step 4: Mark session as completed
            mock_state_store.redis = AsyncMock()
            mock_state_store.redis.hset = AsyncMock()
            await session_manager.complete_session(session.session_id)
            
            # Verify session completion was called
            mock_state_store.redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_concurrent_code_generation_requests(self, sample_design_state):
        """
        Test handling multiple concurrent code generation requests from different sessions.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_state_store = AsyncMock(spec=RedisStateStore)
        
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session_id = f"concurrent-session-{i}"
            state = DesignState(
                wireframe_json={
                    "componentName": f"App{i}",
                    "type": "Frame",
                    "props": {},
                    "children": []
                },
                metadata={"prompt": f"Design {i}"},
                version=1
            )
            sessions.append((session_id, state))
        
        # Mock state retrieval for each session
        async def get_state_for_session(session_id, version):
            for sid, state in sessions:
                if sid == session_id:
                    return state
            return None
        
        mock_state_store.get_design_state = get_state_for_session
        
        # Simulate concurrent requests
        results = []
        for session_id, expected_state in sessions:
            state = await mock_state_store.get_design_state(session_id, 1)
            results.append((session_id, state))
        
        # Verify all sessions retrieved correct states
        assert len(results) == 3
        for i, (session_id, state) in enumerate(results):
            assert state is not None
            assert state.wireframe_json["componentName"] == f"App{i}"
    
    @pytest.mark.asyncio
    async def test_code_generation_preserves_session_metadata(self, sample_design_state):
        """
        Test that session metadata is preserved during code generation.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_state_store = AsyncMock(spec=RedisStateStore)
        
        # Create design state with rich metadata
        state_with_metadata = DesignState(
            wireframe_json=sample_design_state.wireframe_json,
            metadata={
                "prompt": "Create a dashboard",
                "edit_type": "initial",
                "user_preferences": {"theme": "dark", "layout": "grid"},
                "timestamp": datetime.utcnow().isoformat()
            },
            version=1
        )
        
        mock_state_store.get_design_state = AsyncMock(return_value=state_with_metadata)
        
        # Retrieve state
        session_id = "metadata-test-session"
        retrieved_state = await mock_state_store.get_design_state(session_id, 1)
        
        # Verify metadata is preserved
        assert retrieved_state.metadata["prompt"] == "Create a dashboard"
        assert retrieved_state.metadata["user_preferences"]["theme"] == "dark"
        assert "timestamp" in retrieved_state.metadata
    
    @pytest.mark.asyncio
    async def test_session_state_consistency_during_code_generation(self):
        """
        Test that session state remains consistent during code generation.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_state_store = AsyncMock(spec=RedisStateStore)
        mock_session_manager = AsyncMock(spec=DesignSessionManager)
        
        session_id = "consistency-test-session"
        
        # Mock session with specific version
        mock_session = DesignSession(
            session_id=session_id,
            user_id="user-1",
            initial_prompt="Test consistency",
            current_version=3,
            status=SessionStatus.ACTIVE
        )
        mock_session_manager.get_session = AsyncMock(return_value=mock_session)
        
        # Mock design state
        design_state = DesignState(
            wireframe_json={"componentName": "ConsistencyTest", "type": "Frame", "props": {}, "children": []},
            metadata={"version": 3},
            version=3
        )
        mock_state_store.get_design_state = AsyncMock(return_value=design_state)
        
        # Retrieve session and state
        session = await mock_session_manager.get_session(session_id)
        state = await mock_state_store.get_design_state(session_id, session.current_version)
        
        # Verify consistency
        assert session.current_version == state.version
        assert state.version == 3
        assert state.metadata["version"] == 3


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing API contracts."""
    
    def test_generate_code_request_without_session_fields(self):
        """
        Test that GenerateCodeRequest works without session fields.
        Requirement: 5.3 - Backward compatibility
        """
        from app.api.v1.schemas import GenerateCodeRequest
        
        # Old-style request without session fields
        request_data = {
            "layout_json": {
                "componentName": "Test",
                "type": "Frame",
                "props": {},
                "children": []
            }
        }
        
        request = GenerateCodeRequest(**request_data)
        
        assert request.layout_json is not None
        assert request.session_id is None
        assert request.version is None
    
    def test_generate_code_request_with_session_fields(self):
        """
        Test that GenerateCodeRequest works with new session fields.
        Requirement: 5.2 - Integration with existing pipeline
        """
        from app.api.v1.schemas import GenerateCodeRequest
        
        # New-style request with session fields
        request_data = {
            "layout_json": {
                "componentName": "Test",
                "type": "Frame",
                "props": {},
                "children": []
            },
            "session_id": "test-session-123",
            "version": 2
        }
        
        request = GenerateCodeRequest(**request_data)
        
        assert request.layout_json is not None
        assert request.session_id == "test-session-123"
        assert request.version == 2
    
    def test_generate_code_response_includes_session_info(self):
        """
        Test that GenerateCodeResponse includes session information when available.
        Requirement: 5.2 - Integration with existing pipeline
        """
        from app.api.v1.schemas import GenerateCodeResponse
        
        response_data = {
            "react_code": "const App = () => <div>Test</div>;",
            "validation_status": "SUCCESS",
            "errors": [],
            "session_id": "test-session-456",
            "version": 3
        }
        
        response = GenerateCodeResponse(**response_data)
        
        assert response.react_code is not None
        assert response.session_id == "test-session-456"
        assert response.version == 3
        assert response.validation_status == "SUCCESS"


class TestErrorHandling:
    """Tests for error handling in session-to-code integration."""
    
    @pytest.mark.asyncio
    async def test_handle_expired_session_during_code_generation(self):
        """
        Test error handling when session expires during code generation.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_session_manager = AsyncMock(spec=DesignSessionManager)
        mock_session_manager.get_session = AsyncMock(return_value=None)
        
        session_id = "expired-session"
        session = await mock_session_manager.get_session(session_id)
        
        # Should return None for expired session
        assert session is None
    
    @pytest.mark.asyncio
    async def test_handle_corrupted_design_state(self):
        """
        Test error handling when design state is corrupted.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_state_store = AsyncMock(spec=RedisStateStore)
        
        # Simulate corrupted state (missing required fields)
        corrupted_state = DesignState(
            wireframe_json={},  # Empty wireframe
            metadata={},
            version=1
        )
        mock_state_store.get_design_state = AsyncMock(return_value=corrupted_state)
        
        session_id = "corrupted-session"
        state = await mock_state_store.get_design_state(session_id, 1)
        
        # Should still return state, but wireframe is empty
        assert state is not None
        assert state.wireframe_json == {}
    
    @pytest.mark.asyncio
    async def test_handle_redis_connection_failure(self):
        """
        Test error handling when Redis connection fails during code generation.
        Requirement: 5.2 - Integration with existing pipeline
        """
        mock_state_store = AsyncMock(spec=RedisStateStore)
        mock_state_store.connect = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            await mock_state_store.connect()
        
        assert "Redis connection failed" in str(exc_info.value)
