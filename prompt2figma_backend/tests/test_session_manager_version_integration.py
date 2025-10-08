# tests/test_session_manager_version_integration.py
"""
Integration tests for SessionManager and VersionManager integration.
Tests the interaction between session management and version tracking.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.session_manager import DesignSessionManager, SessionManagerError
from app.core.version_manager import VersionManager
from app.core.models import (
    DesignSession, DesignState, EditResult, SessionMetadata, 
    SessionStatus, EditType, VersionDiff
)
from app.core.state_store import RedisStateStore


@pytest.fixture
def mock_state_store():
    """Create a mock state store for testing."""
    store = MagicMock(spec=RedisStateStore)
    store.redis = AsyncMock()
    store.session_ttl = timedelta(hours=24)
    return store


@pytest.fixture
def session_manager(mock_state_store):
    """Create a SessionManager instance with mocked dependencies."""
    return DesignSessionManager(mock_state_store)


@pytest.fixture
def sample_session():
    """Sample design session for testing."""
    return DesignSession(
        session_id="test-session-123",
        user_id="user-456",
        initial_prompt="Create a login form",
        current_version=1,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        status=SessionStatus.ACTIVE
    )


@pytest.fixture
def sample_wireframe():
    """Sample wireframe JSON for testing."""
    return {
        "elements": [
            {
                "id": "input-1",
                "type": "input",
                "position": {"x": 100, "y": 100},
                "size": {"width": 200, "height": 40},
                "properties": {"placeholder": "Username"}
            },
            {
                "id": "button-1",
                "type": "button", 
                "position": {"x": 100, "y": 200},
                "size": {"width": 100, "height": 40},
                "properties": {"text": "Login"}
            }
        ],
        "layout": {"type": "vertical"}
    }


class TestSessionManagerVersionIntegration:
    """Test cases for SessionManager and VersionManager integration."""
    
    @pytest.mark.asyncio
    async def test_apply_edit_success(self, session_manager, mock_state_store, sample_session, sample_wireframe):
        """Test successful edit application using version manager."""
        # Setup mocks
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=sample_session.status,
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.store_design_state.return_value = True
        mock_state_store.add_context_entry.return_value = True
        mock_state_store.increment_edit_count.return_value = True
        mock_state_store.get_all_versions.return_value = [1, 2]
        
        # Mock version manager methods
        session_manager.version_manager.create_version = AsyncMock(return_value=2)
        
        changes = {
            "prompt": "Add a search button",
            "edit_type": "add",
            "target_elements": ["button-2"],
            "processing_time_ms": 1500,
            "summary": "Added search button"
        }
        
        metadata = {"step": "add_search"}
        
        # Execute
        result = await session_manager.apply_edit(
            sample_session.session_id,
            sample_wireframe,
            changes,
            metadata
        )
        
        # Verify
        assert result.success is True
        assert result.new_version == 2
        assert result.updated_wireframe == sample_wireframe
        assert result.changes_summary == "Added search button"
        assert result.processing_time_ms >= 0  # Allow 0 for fast operations
        
        # Verify version manager was called correctly
        session_manager.version_manager.create_version.assert_called_once_with(
            sample_session.session_id,
            sample_wireframe,
            changes,
            metadata
        )
        
        # Verify context was added
        mock_state_store.add_context_entry.assert_called_once()
        mock_state_store.increment_edit_count.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_apply_edit_session_not_found(self, session_manager, mock_state_store):
        """Test edit application when session doesn't exist."""
        mock_state_store.get_session_metadata.return_value = None
        
        with pytest.raises(SessionManagerError, match="Session test-session not found"):
            await session_manager.apply_edit("test-session", {}, {}, {})
    
    @pytest.mark.asyncio
    async def test_apply_edit_inactive_session(self, session_manager, mock_state_store, sample_session):
        """Test edit application on inactive session."""
        # Create inactive session metadata
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=SessionStatus.COMPLETED,  # Inactive status
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        
        with pytest.raises(SessionManagerError, match="Cannot edit inactive session"):
            await session_manager.apply_edit(sample_session.session_id, {}, {}, {})
    
    @pytest.mark.asyncio
    async def test_get_version_diff_success(self, session_manager, mock_state_store, sample_session):
        """Test successful version diff retrieval."""
        # Setup session
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=2,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=sample_session.status,
            total_edits=1
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        
        # Mock version diff
        expected_diff = VersionDiff(
            from_version=1,
            to_version=2,
            added_elements=[{"id": "button-2", "type": "button"}],
            removed_elements=[],
            modified_elements=[],
            metadata_changes={},
            summary="1 elements added"
        )
        
        session_manager.version_manager.get_version_diff = AsyncMock(return_value=expected_diff)
        
        # Execute
        diff = await session_manager.get_version_diff(sample_session.session_id, 1, 2)
        
        # Verify
        assert diff == expected_diff
        session_manager.version_manager.get_version_diff.assert_called_once_with(
            sample_session.session_id, 1, 2
        )
    
    @pytest.mark.asyncio
    async def test_compress_session_versions_success(self, session_manager, mock_state_store, sample_session):
        """Test successful version compression."""
        # Setup session
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=15,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=sample_session.status,
            total_edits=14
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        
        # Mock compression
        session_manager.version_manager.compress_old_versions = AsyncMock(return_value=5)
        
        # Execute
        compressed_count = await session_manager.compress_session_versions(sample_session.session_id, 10)
        
        # Verify
        assert compressed_count == 5
        session_manager.version_manager.compress_old_versions.assert_called_once_with(
            sample_session.session_id, 10
        )
    
    @pytest.mark.asyncio
    async def test_verify_session_integrity_success(self, session_manager, mock_state_store, sample_session):
        """Test successful session integrity verification."""
        # Setup session
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=3,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=sample_session.status,
            total_edits=2
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.get_all_versions.return_value = [1, 2, 3]
        
        # Mock integrity checks - version 2 is corrupted
        async def mock_verify_integrity(session_id, version):
            return version != 2  # Version 2 is corrupted
        
        session_manager.version_manager.verify_version_integrity = mock_verify_integrity
        
        # Execute
        integrity_results = await session_manager.verify_session_integrity(sample_session.session_id)
        
        # Verify
        assert integrity_results["session_id"] == sample_session.session_id
        assert integrity_results["total_versions"] == 3
        assert integrity_results["valid_versions"] == 2
        assert integrity_results["invalid_versions"] == 1
        assert integrity_results["corrupted_versions"] == [2]
    
    @pytest.mark.asyncio
    async def test_get_session_metrics_with_version_manager(self, session_manager, mock_state_store, sample_session):
        """Test session metrics calculation using version manager."""
        # Setup session
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=3,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=sample_session.status,
            total_edits=2
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        
        # Mock version manager metrics
        from app.core.models import SessionMetrics
        expected_metrics = SessionMetrics(
            total_edits=2,
            session_duration_minutes=30,
            edit_types_distribution={EditType.ADD: 1, EditType.MODIFY: 1},
            average_processing_time_ms=1250.0
        )
        
        session_manager.version_manager.calculate_session_metrics = AsyncMock(return_value=expected_metrics)
        
        # Execute
        metrics = await session_manager.get_session_metrics(sample_session.session_id)
        
        # Verify
        assert metrics == expected_metrics
        session_manager.version_manager.calculate_session_metrics.assert_called_once_with(
            sample_session.session_id
        )
    
    @pytest.mark.asyncio
    async def test_get_session_metrics_fallback(self, session_manager, mock_state_store, sample_session):
        """Test session metrics calculation fallback when version manager fails."""
        # Setup session
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=2,
            created_at=sample_session.created_at,
            last_activity=sample_session.created_at + timedelta(minutes=15),
            status=sample_session.status,
            total_edits=1
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        
        # Mock version manager returning None (fallback scenario)
        session_manager.version_manager.calculate_session_metrics = AsyncMock(return_value=None)
        
        # Mock context history for fallback calculation
        from app.core.models import EditContext
        context_history = [
            EditContext(
                prompt="Add button",
                edit_type=EditType.ADD,
                target_elements=["button-1"],
                processing_time_ms=1200
            )
        ]
        
        mock_state_store.get_context_history.return_value = context_history
        
        # Execute
        metrics = await session_manager.get_session_metrics(sample_session.session_id)
        
        # Verify fallback metrics
        assert metrics is not None
        assert metrics.total_edits == 1
        assert metrics.session_duration_minutes == 15
        assert metrics.edit_types_distribution[EditType.ADD] == 1
        assert metrics.average_processing_time_ms == 1200.0
    
    @pytest.mark.asyncio
    async def test_version_manager_initialization(self, session_manager, mock_state_store):
        """Test that version manager is properly initialized in session manager."""
        assert session_manager.version_manager is not None
        assert isinstance(session_manager.version_manager, VersionManager)
        assert session_manager.version_manager.state_store == mock_state_store
    
    @pytest.mark.asyncio
    async def test_error_propagation_from_version_manager(self, session_manager, mock_state_store, sample_session):
        """Test that errors from version manager are properly handled."""
        # Setup session
        session_metadata = SessionMetadata(
            session_id=sample_session.session_id,
            user_id=sample_session.user_id,
            initial_prompt=sample_session.initial_prompt,
            current_version=1,
            created_at=sample_session.created_at,
            last_activity=sample_session.last_activity,
            status=sample_session.status,
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        
        # Mock version manager to raise an exception
        session_manager.version_manager.create_version = AsyncMock(
            side_effect=Exception("Version creation failed")
        )
        
        # Execute and verify error handling
        with pytest.raises(SessionManagerError, match="Edit application failed"):
            await session_manager.apply_edit(sample_session.session_id, {}, {}, {})


class TestSessionManagerVersionIntegrationScenarios:
    """Integration test scenarios for real-world usage patterns."""
    
    @pytest.mark.asyncio
    async def test_complete_edit_workflow(self, session_manager, mock_state_store):
        """Test complete workflow: create session, apply multiple edits, get diff, compress."""
        # Setup initial session
        session_id = "workflow-test-session"
        user_id = "user-123"
        
        # Mock session creation
        mock_state_store.create_session.return_value = True
        
        # Create session
        session = await session_manager.create_session(user_id, "Create a form")
        
        # Setup session metadata for subsequent operations
        session_metadata = SessionMetadata(
            session_id=session.session_id,
            user_id=user_id,
            initial_prompt="Create a form",
            current_version=1,
            created_at=session.created_at,
            last_activity=session.last_activity,
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.store_design_state.return_value = True
        mock_state_store.add_context_entry.return_value = True
        mock_state_store.increment_edit_count.return_value = True
        mock_state_store.get_all_versions.return_value = [1, 2, 3]
        
        # Mock version manager operations
        session_manager.version_manager.create_version = AsyncMock(side_effect=[2, 3])
        session_manager.version_manager.get_version_diff = AsyncMock(
            return_value=VersionDiff(
                from_version=1,
                to_version=3,
                added_elements=[{"id": "input-1"}, {"id": "button-1"}],
                removed_elements=[],
                modified_elements=[],
                metadata_changes={},
                summary="2 elements added"
            )
        )
        session_manager.version_manager.compress_old_versions = AsyncMock(return_value=0)
        
        # Apply first edit
        wireframe_v2 = {"elements": [{"id": "input-1", "type": "input"}]}
        changes_v2 = {"edit_type": "add", "summary": "Added input field"}
        
        result1 = await session_manager.apply_edit(session_id, wireframe_v2, changes_v2, {})
        assert result1.success is True
        assert result1.new_version == 2
        
        # Apply second edit
        wireframe_v3 = {
            "elements": [
                {"id": "input-1", "type": "input"},
                {"id": "button-1", "type": "button"}
            ]
        }
        changes_v3 = {"edit_type": "add", "summary": "Added submit button"}
        
        result2 = await session_manager.apply_edit(session_id, wireframe_v3, changes_v3, {})
        assert result2.success is True
        assert result2.new_version == 3
        
        # Get diff between versions
        diff = await session_manager.get_version_diff(session_id, 1, 3)
        assert diff is not None
        assert diff.from_version == 1
        assert diff.to_version == 3
        assert len(diff.added_elements) == 2
        
        # Compress versions (no compression needed for this small example)
        compressed_count = await session_manager.compress_session_versions(session_id, 2)
        assert compressed_count == 0
        
        # Verify all version manager methods were called
        assert session_manager.version_manager.create_version.call_count == 2
        session_manager.version_manager.get_version_diff.assert_called_once()
        session_manager.version_manager.compress_old_versions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_edit_handling(self, session_manager, mock_state_store):
        """Test handling of concurrent edits to the same session."""
        session_id = "concurrent-test-session"
        
        # Setup session
        session_metadata = SessionMetadata(
            session_id=session_id,
            user_id="user-123",
            initial_prompt="Test concurrent edits",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.update_session_activity.return_value = True
        mock_state_store.store_design_state.return_value = True
        mock_state_store.add_context_entry.return_value = True
        mock_state_store.increment_edit_count.return_value = True
        mock_state_store.get_all_versions.return_value = [1, 2, 3]
        
        # Mock version manager to simulate concurrent version creation
        version_counter = [1]  # Use list for mutable counter
        
        async def mock_create_version(session_id, wireframe, changes, metadata):
            version_counter[0] += 1
            return version_counter[0]
        
        session_manager.version_manager.create_version = mock_create_version
        
        # Simulate concurrent edits
        wireframe1 = {"elements": [{"id": "elem-1", "type": "input"}]}
        wireframe2 = {"elements": [{"id": "elem-2", "type": "button"}]}
        
        changes1 = {"edit_type": "add", "summary": "Added input"}
        changes2 = {"edit_type": "add", "summary": "Added button"}
        
        # Both edits should succeed with different version numbers
        result1 = await session_manager.apply_edit(session_id, wireframe1, changes1, {})
        result2 = await session_manager.apply_edit(session_id, wireframe2, changes2, {})
        
        assert result1.success is True
        assert result2.success is True
        assert result1.new_version != result2.new_version
        assert result1.new_version == 2
        assert result2.new_version == 3