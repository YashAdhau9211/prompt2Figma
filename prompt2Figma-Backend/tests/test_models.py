# tests/test_models.py
"""
Unit tests for core data models.
Tests validation, serialization, and model behavior.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
import uuid

from app.core.models import (
    DesignState, DesignSession, EditContext, SessionMetadata,
    EditResult, SessionMetrics, CreateSessionRequest, CreateSessionResponse,
    EditSessionRequest, EditSessionResponse, SessionHistoryResponse,
    IterativeDesignError, EditType, SessionStatus
)


class TestEditType:
    """Test EditType enum."""
    
    def test_edit_type_values(self):
        """Test that EditType has expected values."""
        assert EditType.MODIFY == "modify"
        assert EditType.ADD == "add"
        assert EditType.REMOVE == "remove"
        assert EditType.STYLE == "style"
        assert EditType.LAYOUT == "layout"


class TestSessionStatus:
    """Test SessionStatus enum."""
    
    def test_session_status_values(self):
        """Test that SessionStatus has expected values."""
        assert SessionStatus.ACTIVE == "active"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.EXPIRED == "expired"


class TestDesignState:
    """Test DesignState model."""
    
    def test_design_state_creation(self):
        """Test creating a valid DesignState."""
        wireframe = {"type": "form", "elements": []}
        metadata = {"created_by": "ai"}
        created_at = datetime.utcnow()
        
        state = DesignState(
            wireframe_json=wireframe,
            metadata=metadata,
            created_at=created_at,
            version=1
        )
        
        assert state.wireframe_json == wireframe
        assert state.metadata == metadata
        assert state.created_at == created_at
        assert state.version == 1
    
    def test_design_state_defaults(self):
        """Test DesignState with default values."""
        wireframe = {"type": "button"}
        
        state = DesignState(
            wireframe_json=wireframe,
            version=1
        )
        
        assert state.wireframe_json == wireframe
        assert state.metadata == {}
        assert isinstance(state.created_at, datetime)
        assert state.version == 1
    
    def test_design_state_validation(self):
        """Test DesignState validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            DesignState()
        
        with pytest.raises(ValidationError):
            DesignState(wireframe_json={"type": "button"})  # Missing version


class TestEditContext:
    """Test EditContext model."""
    
    def test_edit_context_creation(self):
        """Test creating a valid EditContext."""
        prompt = "Make the button bigger"
        edit_type = EditType.STYLE
        target_elements = ["button-1", "button-2"]
        timestamp = datetime.utcnow()
        
        context = EditContext(
            prompt=prompt,
            edit_type=edit_type,
            target_elements=target_elements,
            timestamp=timestamp,
            processing_time_ms=150
        )
        
        assert context.prompt == prompt
        assert context.edit_type == edit_type
        assert context.target_elements == target_elements
        assert context.timestamp == timestamp
        assert context.processing_time_ms == 150
    
    def test_edit_context_defaults(self):
        """Test EditContext with default values."""
        context = EditContext(
            prompt="Test prompt",
            edit_type=EditType.MODIFY
        )
        
        assert context.prompt == "Test prompt"
        assert context.edit_type == EditType.MODIFY
        assert context.target_elements == []
        assert isinstance(context.timestamp, datetime)
        assert context.processing_time_ms == 0


class TestDesignSession:
    """Test DesignSession model."""
    
    def test_design_session_creation(self):
        """Test creating a valid DesignSession."""
        session_id = "test-session-123"
        user_id = "user-456"
        initial_prompt = "Create a login form"
        
        session = DesignSession(
            session_id=session_id,
            user_id=user_id,
            initial_prompt=initial_prompt
        )
        
        assert session.session_id == session_id
        assert session.user_id == user_id
        assert session.initial_prompt == initial_prompt
        assert session.current_version == 1
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.last_activity, datetime)
        assert session.status == SessionStatus.ACTIVE
    
    def test_design_session_defaults(self):
        """Test DesignSession with default values."""
        session = DesignSession(
            user_id="user-123",
            initial_prompt="Test prompt"
        )
        
        # Should generate a UUID for session_id
        assert session.session_id is not None
        assert len(session.session_id) > 0
        # Verify it's a valid UUID format
        uuid.UUID(session.session_id)  # Should not raise exception
        
        assert session.current_version == 1
        assert session.status == SessionStatus.ACTIVE
    
    def test_design_session_validation(self):
        """Test DesignSession validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            DesignSession()
        
        with pytest.raises(ValidationError):
            DesignSession(user_id="user-123")  # Missing initial_prompt


class TestSessionMetadata:
    """Test SessionMetadata model."""
    
    def test_session_metadata_creation(self):
        """Test creating valid SessionMetadata."""
        metadata = SessionMetadata(
            session_id="session-123",
            user_id="user-456",
            initial_prompt="Test prompt",
            current_version=2,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=5
        )
        
        assert metadata.session_id == "session-123"
        assert metadata.user_id == "user-456"
        assert metadata.current_version == 2
        assert metadata.total_edits == 5
    
    def test_session_metadata_defaults(self):
        """Test SessionMetadata with default values."""
        metadata = SessionMetadata(
            session_id="session-123",
            user_id="user-456",
            initial_prompt="Test prompt",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE
        )
        
        assert metadata.total_edits == 0


class TestEditResult:
    """Test EditResult model."""
    
    def test_edit_result_success(self):
        """Test creating a successful EditResult."""
        result = EditResult(
            success=True,
            new_version=2,
            updated_wireframe={"type": "form"},
            changes_summary="Added input field",
            processing_time_ms=250
        )
        
        assert result.success is True
        assert result.new_version == 2
        assert result.updated_wireframe == {"type": "form"}
        assert result.changes_summary == "Added input field"
        assert result.processing_time_ms == 250
        assert result.errors is None
    
    def test_edit_result_failure(self):
        """Test creating a failed EditResult."""
        errors = ["Invalid prompt", "Context not found"]
        
        result = EditResult(
            success=False,
            new_version=1,  # No change
            updated_wireframe={},
            changes_summary="Failed to apply changes",
            processing_time_ms=100,
            errors=errors
        )
        
        assert result.success is False
        assert result.errors == errors


class TestSessionMetrics:
    """Test SessionMetrics model."""
    
    def test_session_metrics_creation(self):
        """Test creating SessionMetrics."""
        edit_distribution = {
            EditType.STYLE: 3,
            EditType.LAYOUT: 2,
            EditType.ADD: 1
        }
        
        metrics = SessionMetrics(
            total_edits=6,
            session_duration_minutes=15,
            edit_types_distribution=edit_distribution,
            average_processing_time_ms=200.5,
            user_satisfaction_score=4.5
        )
        
        assert metrics.total_edits == 6
        assert metrics.session_duration_minutes == 15
        assert metrics.edit_types_distribution == edit_distribution
        assert metrics.average_processing_time_ms == 200.5
        assert metrics.user_satisfaction_score == 4.5
    
    def test_session_metrics_defaults(self):
        """Test SessionMetrics with default values."""
        metrics = SessionMetrics(
            total_edits=0,
            session_duration_minutes=0,
            average_processing_time_ms=0.0
        )
        
        assert metrics.edit_types_distribution == {}
        assert metrics.user_satisfaction_score is None


class TestAPIModels:
    """Test API request/response models."""
    
    def test_create_session_request(self):
        """Test CreateSessionRequest model."""
        request = CreateSessionRequest(
            prompt="Create a dashboard",
            user_id="user-123"
        )
        
        assert request.prompt == "Create a dashboard"
        assert request.user_id == "user-123"
    
    def test_create_session_request_optional_user(self):
        """Test CreateSessionRequest with optional user_id."""
        request = CreateSessionRequest(prompt="Create a form")
        
        assert request.prompt == "Create a form"
        assert request.user_id is None
    
    def test_create_session_response(self):
        """Test CreateSessionResponse model."""
        wireframe = {"type": "container", "children": []}
        
        response = CreateSessionResponse(
            session_id="session-123",
            wireframe_json=wireframe,
            version=1
        )
        
        assert response.session_id == "session-123"
        assert response.wireframe_json == wireframe
        assert response.version == 1
    
    def test_edit_session_request(self):
        """Test EditSessionRequest model."""
        request = EditSessionRequest(edit_prompt="Add a search bar")
        
        assert request.edit_prompt == "Add a search bar"
    
    def test_edit_session_response(self):
        """Test EditSessionResponse model."""
        wireframe = {"type": "form", "elements": ["search"]}
        
        response = EditSessionResponse(
            session_id="session-123",
            wireframe_json=wireframe,
            version=2,
            changes_summary="Added search bar",
            processing_time_ms=300
        )
        
        assert response.session_id == "session-123"
        assert response.wireframe_json == wireframe
        assert response.version == 2
        assert response.changes_summary == "Added search bar"
        assert response.processing_time_ms == 300
    
    def test_session_history_response(self):
        """Test SessionHistoryResponse model."""
        versions = [
            {"version": 1, "prompt": "Initial"},
            {"version": 2, "prompt": "Edit 1"}
        ]
        
        response = SessionHistoryResponse(
            session_id="session-123",
            versions=versions,
            total_versions=2
        )
        
        assert response.session_id == "session-123"
        assert response.versions == versions
        assert response.total_versions == 2
    
    def test_iterative_design_error(self):
        """Test IterativeDesignError model."""
        error = IterativeDesignError(
            error_code="CONTEXT_LOST",
            message="Session context could not be retrieved",
            recoverable=True,
            suggested_action="Try refreshing the session",
            session_state="corrupted"
        )
        
        assert error.error_code == "CONTEXT_LOST"
        assert error.message == "Session context could not be retrieved"
        assert error.recoverable is True
        assert error.suggested_action == "Try refreshing the session"
        assert error.session_state == "corrupted"
    
    def test_iterative_design_error_minimal(self):
        """Test IterativeDesignError with minimal fields."""
        error = IterativeDesignError(
            error_code="REDIS_ERROR",
            message="Connection failed",
            recoverable=False
        )
        
        assert error.error_code == "REDIS_ERROR"
        assert error.message == "Connection failed"
        assert error.recoverable is False
        assert error.suggested_action is None
        assert error.session_state is None


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_design_state_json_serialization(self):
        """Test DesignState JSON serialization."""
        state = DesignState(
            wireframe_json={"type": "button", "text": "Click me"},
            metadata={"version": "1.0"},
            version=1
        )
        
        # Should be able to serialize to JSON
        json_data = state.model_dump()
        assert "wireframe_json" in json_data
        assert "metadata" in json_data
        assert "version" in json_data
        
        # Should be able to deserialize from JSON
        restored_state = DesignState(**json_data)
        assert restored_state.wireframe_json == state.wireframe_json
        assert restored_state.metadata == state.metadata
        assert restored_state.version == state.version
    
    def test_edit_context_json_serialization(self):
        """Test EditContext JSON serialization."""
        context = EditContext(
            prompt="Change color to blue",
            edit_type=EditType.STYLE,
            target_elements=["button-1"]
        )
        
        json_data = context.model_dump()
        restored_context = EditContext(**json_data)
        
        assert restored_context.prompt == context.prompt
        assert restored_context.edit_type == context.edit_type
        assert restored_context.target_elements == context.target_elements