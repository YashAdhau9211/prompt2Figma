# tests/test_api_iterative_design.py
"""
Tests for iterative design API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.core.models import (
    DesignSession, DesignState, SessionStatus,
    EditResult, SessionMetadata
)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create a mock design session."""
    return DesignSession(
        session_id="test-session-123",
        user_id="test-user",
        initial_prompt="Create a login form",
        current_version=1,
        status=SessionStatus.ACTIVE
    )


@pytest.fixture
def mock_design_state():
    """Create a mock design state."""
    return DesignState(
        wireframe_json={
            "type": "container",
            "id": "root",
            "children": [
                {
                    "type": "text",
                    "id": "title",
                    "content": "Login Form",
                    "styles": {"fontSize": "24px"}
                }
            ]
        },
        metadata={"initial": True},
        version=1
    )


class TestCreateSessionEndpoint:
    """Tests for POST /design-sessions endpoint."""
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    @patch('app.tasks.pipeline.generate_wireframe_json')
    def test_create_session_success(self, mock_wireframe_task, mock_get_manager, client, mock_session, mock_design_state):
        """Test successful session creation."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.create_session.return_value = mock_session
        mock_manager.update_session_state.return_value = True
        mock_get_manager.return_value = mock_manager
        
        # Mock Celery task
        mock_task = MagicMock()
        mock_task.get.return_value = mock_design_state.wireframe_json
        mock_wireframe_task.apply_async.return_value = mock_task
        
        # Make request
        response = client.post(
            "/api/v1/design-sessions",
            json={"prompt": "Create a login form", "user_id": "test-user"}
        )
        
        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "wireframe_json" in data
        assert "version" in data
        assert data["version"] == 1
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    def test_create_session_with_fallback_wireframe(self, mock_get_manager, client, mock_session):
        """Test session creation with fallback wireframe when generation fails."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.create_session.return_value = mock_session
        mock_manager.update_session_state.return_value = True
        mock_get_manager.return_value = mock_manager
        
        # Make request
        with patch('app.tasks.pipeline.generate_wireframe_json') as mock_task:
            mock_task.apply_async.side_effect = Exception("Generation failed")
            
            response = client.post(
                "/api/v1/design-sessions",
                json={"prompt": "Create a login form"}
            )
        
        # Should still succeed with fallback
        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "wireframe_json" in data


class TestEditSessionEndpoint:
    """Tests for POST /design-sessions/{id}/edit endpoint."""
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    def test_edit_session_success(self, mock_get_manager, client, mock_session, mock_design_state):
        """Test successful session edit."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.get_session.return_value = mock_session
        mock_manager.state_store.get_design_state.return_value = mock_design_state
        
        edit_result = EditResult(
            success=True,
            new_version=2,
            updated_wireframe={"type": "container", "children": []},
            changes_summary="Applied edit",
            processing_time_ms=100
        )
        mock_manager.apply_edit.return_value = edit_result
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.post(
            f"/api/v1/design-sessions/{mock_session.session_id}/edit",
            json={"edit_prompt": "Add a submit button"}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == mock_session.session_id
        assert data["version"] == 2
        assert "wireframe_json" in data
        assert "changes_summary" in data
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    def test_edit_session_not_found(self, mock_get_manager, client):
        """Test editing non-existent session."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.get_session.return_value = None
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.post(
            "/api/v1/design-sessions/nonexistent-session/edit",
            json={"edit_prompt": "Add a button"}
        )
        
        # Assertions
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetSessionHistoryEndpoint:
    """Tests for GET /design-sessions/{id}/history endpoint."""
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    def test_get_history_success(self, mock_get_manager, client, mock_session):
        """Test successful history retrieval."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.get_session.return_value = mock_session
        
        history = [
            DesignState(
                wireframe_json={"type": "container", "children": []},
                metadata={"initial": True},
                version=1
            ),
            DesignState(
                wireframe_json={"type": "container", "children": [{"type": "button"}]},
                metadata={"edit": "Added button"},
                version=2
            )
        ]
        mock_manager.get_session_history.return_value = history
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get(f"/api/v1/design-sessions/{mock_session.session_id}/history")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == mock_session.session_id
        assert data["total_versions"] == 2
        assert len(data["versions"]) == 2
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    def test_get_history_not_found(self, mock_get_manager, client):
        """Test history retrieval for non-existent session."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.get_session.return_value = None
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get("/api/v1/design-sessions/nonexistent-session/history")
        
        # Assertions
        assert response.status_code == 404


class TestGetSessionDetailsEndpoint:
    """Tests for GET /design-sessions/{id} endpoint."""
    
    @patch('app.api.v1.iterative_design.get_session_manager')
    def test_get_session_details_success(self, mock_get_manager, client, mock_session, mock_design_state):
        """Test successful session details retrieval."""
        # Setup mocks
        mock_manager = AsyncMock()
        mock_manager.get_session.return_value = mock_session
        mock_manager.state_store.get_design_state.return_value = mock_design_state
        mock_manager.state_store.get_context_history.return_value = []
        
        mock_metadata = SessionMetadata(
            session_id=mock_session.session_id,
            user_id=mock_session.user_id,
            initial_prompt=mock_session.initial_prompt,
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        mock_manager.state_store.get_session_metadata.return_value = mock_metadata
        mock_get_manager.return_value = mock_manager
        
        # Make request
        response = client.get(f"/api/v1/design-sessions/{mock_session.session_id}")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == mock_session.session_id
        assert data["user_id"] == mock_session.user_id
        assert "current_wireframe" in data
        assert "recent_edits" in data
