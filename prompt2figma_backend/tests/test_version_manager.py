# tests/test_version_manager.py
"""
Unit tests for the VersionManager class.
Tests version operations, integrity checking, and compression functionality.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.version_manager import VersionManager, VersionMetadata, VersionDiff
from app.core.models import DesignState, SessionMetadata, EditType, SessionStatus
from app.core.state_store import RedisStateStore


@pytest.fixture
def mock_state_store():
    """Create a mock state store for testing."""
    store = MagicMock(spec=RedisStateStore)
    store.redis = AsyncMock()
    store.session_ttl = timedelta(hours=24)
    return store


@pytest.fixture
def version_manager(mock_state_store):
    """Create a VersionManager instance with mocked dependencies."""
    return VersionManager(mock_state_store)


@pytest.fixture
def sample_session_metadata():
    """Sample session metadata for testing."""
    return SessionMetadata(
        session_id="test-session-123",
        user_id="user-456",
        initial_prompt="Create a login form",
        current_version=1,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        status=SessionStatus.ACTIVE,
        total_edits=0
    )


@pytest.fixture
def sample_wireframe():
    """Sample wireframe JSON for testing."""
    return {
        "elements": [
            {
                "id": "elem-1",
                "type": "input",
                "position": {"x": 100, "y": 100},
                "size": {"width": 200, "height": 40},
                "properties": {"placeholder": "Username"}
            },
            {
                "id": "elem-2", 
                "type": "button",
                "position": {"x": 100, "y": 200},
                "size": {"width": 100, "height": 40},
                "properties": {"text": "Login"}
            }
        ],
        "layout": {"type": "vertical"}
    }


@pytest.fixture
def sample_design_state(sample_wireframe):
    """Sample design state for testing."""
    return DesignState(
        wireframe_json=sample_wireframe,
        metadata={"test": "data"},
        created_at=datetime.utcnow(),
        version=1
    )


class TestVersionManager:
    """Test cases for VersionManager functionality."""
    
    @pytest.mark.asyncio
    async def test_create_version_success(self, version_manager, mock_state_store, sample_session_metadata, sample_wireframe):
        """Test successful version creation."""
        # Setup mocks
        mock_state_store.get_session_metadata.return_value = sample_session_metadata
        mock_state_store.store_design_state.return_value = True
        mock_state_store.get_all_versions.return_value = [1]
        
        changes = {
            "edit_type": "modify",
            "target_elements": ["elem-1"],
            "processing_time_ms": 1500,
            "summary": "Updated username field"
        }
        
        # Execute
        new_version = await version_manager.create_version(
            "test-session-123",
            sample_wireframe,
            changes,
            {"additional": "metadata"}
        )
        
        # Verify
        assert new_version == 2
        mock_state_store.get_session_metadata.assert_called_once_with("test-session-123")
        mock_state_store.store_design_state.assert_called_once()
        
        # Verify the design state was created correctly
        call_args = mock_state_store.store_design_state.call_args
        session_id, version, design_state = call_args[0]
        
        assert session_id == "test-session-123"
        assert version == 2
        assert design_state.wireframe_json == sample_wireframe
        assert design_state.version == 2
        assert "content_hash" in design_state.metadata
        assert design_state.metadata["changes"] == changes
    
    @pytest.mark.asyncio
    async def test_create_version_session_not_found(self, version_manager, mock_state_store):
        """Test version creation when session doesn't exist."""
        mock_state_store.get_session_metadata.return_value = None
        
        with pytest.raises(ValueError, match="Session test-session not found"):
            await version_manager.create_version(
                "test-session",
                {},
                {},
                {}
            )
    
    @pytest.mark.asyncio
    async def test_create_version_storage_failure(self, version_manager, mock_state_store, sample_session_metadata):
        """Test version creation when storage fails."""
        mock_state_store.get_session_metadata.return_value = sample_session_metadata
        mock_state_store.store_design_state.return_value = False
        
        with pytest.raises(RuntimeError, match="Failed to store design state"):
            await version_manager.create_version(
                "test-session-123",
                {},
                {},
                {}
            )
    
    @pytest.mark.asyncio
    async def test_get_version_diff_success(self, version_manager, mock_state_store):
        """Test successful version diff calculation."""
        # Create two different design states
        from_wireframe = {
            "elements": [
                {"id": "elem-1", "type": "input", "properties": {"placeholder": "Username"}}
            ]
        }
        
        to_wireframe = {
            "elements": [
                {"id": "elem-1", "type": "input", "properties": {"placeholder": "Email"}},
                {"id": "elem-2", "type": "button", "properties": {"text": "Submit"}}
            ]
        }
        
        from_state = DesignState(
            wireframe_json=from_wireframe,
            metadata={"version": 1},
            created_at=datetime.utcnow(),
            version=1
        )
        
        to_state = DesignState(
            wireframe_json=to_wireframe,
            metadata={"version": 2},
            created_at=datetime.utcnow(),
            version=2
        )
        
        mock_state_store.get_design_state.side_effect = [from_state, to_state]
        
        # Execute
        diff = await version_manager.get_version_diff("test-session", 1, 2)
        
        # Verify
        assert diff is not None
        assert diff.from_version == 1
        assert diff.to_version == 2
        assert len(diff.added_elements) == 1  # elem-2 was added
        assert diff.added_elements[0]["id"] == "elem-2"
        assert len(diff.modified_elements) == 1  # elem-1 was modified
        assert diff.modified_elements[0]["id"] == "elem-1"
        assert "1 elements added, 1 elements modified" in diff.summary
    
    @pytest.mark.asyncio
    async def test_get_version_diff_missing_version(self, version_manager, mock_state_store):
        """Test version diff when one version is missing."""
        mock_state_store.get_design_state.side_effect = [None, None]
        
        diff = await version_manager.get_version_diff("test-session", 1, 2)
        
        assert diff is None
    
    @pytest.mark.asyncio
    async def test_get_version_metadata_success(self, version_manager, mock_state_store):
        """Test successful version metadata retrieval."""
        metadata_data = {
            "version": "2",
            "created_at": datetime.utcnow().isoformat(),
            "changes_summary": "Added button",
            "edit_type": "add",
            "target_elements": '["elem-2"]',
            "processing_time_ms": "1200",
            "content_hash": "abc123",
            "compressed": "false"
        }
        
        mock_state_store.redis.hgetall.return_value = metadata_data
        
        # Execute
        metadata = await version_manager.get_version_metadata("test-session", 2)
        
        # Verify
        assert metadata is not None
        assert metadata.version == 2
        assert metadata.changes_summary == "Added button"
        assert metadata.edit_type == EditType.ADD
        assert metadata.target_elements == ["elem-2"]
        assert metadata.processing_time_ms == 1200
        assert metadata.content_hash == "abc123"
        assert metadata.compressed is False
    
    @pytest.mark.asyncio
    async def test_get_version_metadata_not_found(self, version_manager, mock_state_store):
        """Test version metadata retrieval when not found."""
        mock_state_store.redis.hgetall.return_value = {}
        
        metadata = await version_manager.get_version_metadata("test-session", 999)
        
        assert metadata is None
    
    @pytest.mark.asyncio
    async def test_compress_old_versions_success(self, version_manager, mock_state_store, sample_design_state):
        """Test successful compression of old versions."""
        # Setup: 15 versions, keep 10 recent, compress 5 old ones
        all_versions = list(range(1, 16))  # Versions 1-15
        mock_state_store.get_all_versions.return_value = all_versions
        
        # Mock version metadata - none are compressed yet
        async def mock_get_version_metadata(session_id, version):
            if version <= 5:  # Versions to be compressed
                return VersionMetadata(
                    version=version,
                    created_at=datetime.utcnow(),
                    changes_summary="test",
                    edit_type=EditType.MODIFY,
                    target_elements=[],
                    processing_time_ms=1000,
                    content_hash="hash",
                    compressed=False
                )
            return None
        
        version_manager.get_version_metadata = mock_get_version_metadata
        mock_state_store.get_design_state.return_value = sample_design_state
        mock_state_store.store_design_state.return_value = True
        
        # Execute
        compressed_count = await version_manager.compress_old_versions("test-session", 10)
        
        # Verify
        assert compressed_count == 5  # Should compress versions 1-5
        assert mock_state_store.store_design_state.call_count == 5
    
    @pytest.mark.asyncio
    async def test_compress_old_versions_no_compression_needed(self, version_manager, mock_state_store):
        """Test compression when no compression is needed."""
        # Only 5 versions, keep 10 - no compression needed
        mock_state_store.get_all_versions.return_value = [1, 2, 3, 4, 5]
        
        compressed_count = await version_manager.compress_old_versions("test-session", 10)
        
        assert compressed_count == 0
    
    @pytest.mark.asyncio
    async def test_calculate_session_metrics_success(self, version_manager, mock_state_store, sample_session_metadata):
        """Test successful session metrics calculation."""
        # Setup session with 3 versions (2 edits)
        sample_session_metadata.last_activity = sample_session_metadata.created_at + timedelta(minutes=30)
        mock_state_store.get_session_metadata.return_value = sample_session_metadata
        mock_state_store.get_all_versions.return_value = [1, 2, 3]
        
        # Mock version metadata for versions 2 and 3
        async def mock_get_version_metadata(session_id, version):
            if version == 2:
                return VersionMetadata(
                    version=2,
                    created_at=datetime.utcnow(),
                    changes_summary="Added button",
                    edit_type=EditType.ADD,
                    target_elements=["elem-2"],
                    processing_time_ms=1500,
                    content_hash="hash2",
                    compressed=False
                )
            elif version == 3:
                return VersionMetadata(
                    version=3,
                    created_at=datetime.utcnow(),
                    changes_summary="Modified input",
                    edit_type=EditType.MODIFY,
                    target_elements=["elem-1"],
                    processing_time_ms=1200,
                    content_hash="hash3",
                    compressed=False
                )
            return None
        
        version_manager.get_version_metadata = mock_get_version_metadata
        
        # Execute
        metrics = await version_manager.calculate_session_metrics("test-session")
        
        # Verify
        assert metrics is not None
        assert metrics.total_edits == 2  # 3 versions - 1 initial = 2 edits
        assert metrics.session_duration_minutes == 30
        assert metrics.edit_types_distribution[EditType.ADD] == 1
        assert metrics.edit_types_distribution[EditType.MODIFY] == 1
        assert metrics.average_processing_time_ms == 1350  # (1500 + 1200) / 2
    
    @pytest.mark.asyncio
    async def test_verify_version_integrity_success(self, version_manager, mock_state_store):
        """Test successful version integrity verification."""
        wireframe = {"elements": [{"id": "test", "type": "input"}]}
        content_hash = version_manager._calculate_content_hash(wireframe)
        
        design_state = DesignState(
            wireframe_json=wireframe,
            metadata={"content_hash": content_hash},
            created_at=datetime.utcnow(),
            version=1
        )
        
        mock_state_store.get_design_state.return_value = design_state
        
        # Execute
        is_valid = await version_manager.verify_version_integrity("test-session", 1)
        
        # Verify
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_verify_version_integrity_hash_mismatch(self, version_manager, mock_state_store):
        """Test version integrity verification with hash mismatch."""
        wireframe = {"elements": [{"id": "test", "type": "input"}]}
        
        design_state = DesignState(
            wireframe_json=wireframe,
            metadata={"content_hash": "wrong_hash"},
            created_at=datetime.utcnow(),
            version=1
        )
        
        mock_state_store.get_design_state.return_value = design_state
        
        # Execute
        is_valid = await version_manager.verify_version_integrity("test-session", 1)
        
        # Verify
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_verify_version_integrity_no_hash(self, version_manager, mock_state_store):
        """Test version integrity verification when no hash is stored."""
        wireframe = {"elements": [{"id": "test", "type": "input"}]}
        
        design_state = DesignState(
            wireframe_json=wireframe,
            metadata={},  # No content_hash
            created_at=datetime.utcnow(),
            version=1
        )
        
        mock_state_store.get_design_state.return_value = design_state
        
        # Execute
        is_valid = await version_manager.verify_version_integrity("test-session", 1)
        
        # Verify
        assert is_valid is False
    
    def test_calculate_content_hash_consistency(self, version_manager):
        """Test that content hash calculation is consistent."""
        wireframe1 = {"elements": [{"id": "1", "type": "input"}], "layout": {"type": "grid"}}
        wireframe2 = {"layout": {"type": "grid"}, "elements": [{"id": "1", "type": "input"}]}  # Different order
        
        hash1 = version_manager._calculate_content_hash(wireframe1)
        hash2 = version_manager._calculate_content_hash(wireframe2)
        
        # Should be the same due to sort_keys=True in JSON serialization
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64-character hex string
    
    def test_calculate_diff_comprehensive(self, version_manager):
        """Test comprehensive diff calculation between design states."""
        from_wireframe = {
            "elements": [
                {"id": "elem-1", "type": "input", "properties": {"placeholder": "Username"}},
                {"id": "elem-2", "type": "button", "properties": {"text": "Login"}},
                {"id": "elem-3", "type": "text", "properties": {"content": "Welcome"}}
            ]
        }
        
        to_wireframe = {
            "elements": [
                {"id": "elem-1", "type": "input", "properties": {"placeholder": "Email"}},  # Modified
                {"id": "elem-4", "type": "checkbox", "properties": {"label": "Remember me"}},  # Added
                {"id": "elem-2", "type": "button", "properties": {"text": "Login"}}  # Unchanged
                # elem-3 removed
            ]
        }
        
        from_state = DesignState(
            wireframe_json=from_wireframe,
            metadata={"theme": "light"},
            created_at=datetime.utcnow(),
            version=1
        )
        
        to_state = DesignState(
            wireframe_json=to_wireframe,
            metadata={"theme": "dark"},
            created_at=datetime.utcnow(),
            version=2
        )
        
        # Execute
        diff = version_manager._calculate_diff(from_state, to_state)
        
        # Verify
        assert len(diff["added"]) == 1
        assert diff["added"][0]["id"] == "elem-4"
        
        assert len(diff["removed"]) == 1
        assert diff["removed"][0]["id"] == "elem-3"
        
        assert len(diff["modified"]) == 1
        assert diff["modified"][0]["id"] == "elem-1"
        assert diff["modified"][0]["from"]["properties"]["placeholder"] == "Username"
        assert diff["modified"][0]["to"]["properties"]["placeholder"] == "Email"
        
        assert "theme" in diff["metadata_changes"]
        assert diff["metadata_changes"]["theme"]["from"] == "light"
        assert diff["metadata_changes"]["theme"]["to"] == "dark"
        
        assert "1 elements added, 1 elements removed, 1 elements modified" in diff["summary"]
    
    def test_create_compressed_state(self, version_manager, sample_design_state):
        """Test creation of compressed design state."""
        # Add some detailed styling to test compression
        sample_design_state.wireframe_json["elements"][0]["style"] = {
            "backgroundColor": "#ffffff",
            "border": "1px solid #ccc",
            "borderRadius": "4px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
        }
        
        # Execute
        compressed_state = version_manager._create_compressed_state(sample_design_state)
        
        # Verify
        assert compressed_state.wireframe_json["compressed"] is True
        assert compressed_state.metadata["compressed"] is True
        assert "original_size" in compressed_state.metadata
        
        # Check that detailed styling is removed but essential data remains
        compressed_element = compressed_state.wireframe_json["elements"][0]
        assert "id" in compressed_element
        assert "type" in compressed_element
        assert "position" in compressed_element
        assert "size" in compressed_element
        assert "style" not in compressed_element  # Detailed styling removed
    
    @pytest.mark.asyncio
    async def test_check_and_compress_versions_threshold_exceeded(self, version_manager, mock_state_store):
        """Test automatic compression when version threshold is exceeded."""
        # Set up version manager with low thresholds for testing
        version_manager.max_versions_per_session = 5
        version_manager.compression_threshold = 3
        
        # Mock 6 versions (exceeds max of 5)
        mock_state_store.get_all_versions.return_value = [1, 2, 3, 4, 5, 6]
        
        # Mock the compress_old_versions method
        version_manager.compress_old_versions = AsyncMock(return_value=2)
        
        # Execute
        await version_manager._check_and_compress_versions("test-session")
        
        # Verify
        version_manager.compress_old_versions.assert_called_once_with("test-session", 3)


class TestVersionManagerIntegration:
    """Integration tests for VersionManager with real-like scenarios."""
    
    @pytest.mark.asyncio
    async def test_full_version_lifecycle(self, version_manager, mock_state_store):
        """Test complete version lifecycle: create, diff, compress, verify."""
        # Setup initial session
        session_metadata = SessionMetadata(
            session_id="integration-test",
            user_id="user-123",
            initial_prompt="Create a form",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.store_design_state.return_value = True
        mock_state_store.get_all_versions.return_value = [1, 2]
        
        # Create version 2
        wireframe_v2 = {
            "elements": [
                {"id": "input-1", "type": "input", "properties": {"placeholder": "Name"}}
            ]
        }
        
        changes = {
            "edit_type": "add",
            "target_elements": ["input-1"],
            "processing_time_ms": 1200,
            "summary": "Added name input"
        }
        
        new_version = await version_manager.create_version(
            "integration-test",
            wireframe_v2,
            changes,
            {"step": "add_input"}
        )
        
        assert new_version == 2
        
        # Verify version was stored correctly
        store_call = mock_state_store.store_design_state.call_args
        stored_session_id, stored_version, stored_state = store_call[0]
        
        assert stored_session_id == "integration-test"
        assert stored_version == 2
        assert stored_state.wireframe_json == wireframe_v2
        assert stored_state.metadata["changes"] == changes
        assert "content_hash" in stored_state.metadata
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, version_manager, mock_state_store):
        """Test error handling in various failure scenarios."""
        # Test session not found
        mock_state_store.get_session_metadata.return_value = None
        
        with pytest.raises(ValueError):
            await version_manager.create_version("nonexistent", {}, {}, {})
        
        # Test storage failure
        session_metadata = SessionMetadata(
            session_id="test-session",
            user_id="user-123",
            initial_prompt="Test",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        mock_state_store.get_session_metadata.return_value = session_metadata
        mock_state_store.store_design_state.return_value = False
        
        with pytest.raises(RuntimeError):
            await version_manager.create_version("test-session", {}, {}, {})
        
        # Test graceful handling of missing versions in diff
        mock_state_store.get_design_state.return_value = None
        
        diff = await version_manager.get_version_diff("test-session", 1, 2)
        assert diff is None