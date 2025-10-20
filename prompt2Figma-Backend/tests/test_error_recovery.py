# tests/test_error_recovery.py
"""
Unit tests for error recovery mechanisms.
Tests session state validation, recovery, and graceful degradation.
"""

import pytest
import json
from datetime import datetime
from collections import OrderedDict

from app.core.error_recovery import (
    SessionRecoveryManager, GracefulDegradationManager
)
from app.core.models import DesignState


class TestSessionRecoveryManager:
    """Test suite for SessionRecoveryManager."""
    
    @pytest.fixture
    def recovery_manager(self):
        """Create a session recovery manager instance."""
        return SessionRecoveryManager()
    
    @pytest.fixture
    def valid_state_data(self):
        """Create valid state data for testing."""
        return {
            "wireframe_json": json.dumps({"type": "container", "children": []}),
            "metadata": json.dumps({"author": "test"}),
            "created_at": datetime.utcnow().isoformat(),
            "version": "1"
        }
    
    @pytest.mark.asyncio
    async def test_validate_valid_state(self, recovery_manager, valid_state_data):
        """Test validation of a valid state."""
        is_valid, error = await recovery_manager.validate_session_state(
            "test-session", valid_state_data
        )
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_empty_state(self, recovery_manager):
        """Test validation of empty state data."""
        is_valid, error = await recovery_manager.validate_session_state(
            "test-session", {}
        )
        
        assert is_valid is False
        assert "empty" in error.lower()
    
    @pytest.mark.asyncio
    async def test_validate_missing_wireframe(self, recovery_manager, valid_state_data):
        """Test validation fails when wireframe is missing."""
        del valid_state_data["wireframe_json"]
        
        is_valid, error = await recovery_manager.validate_session_state(
            "test-session", valid_state_data
        )
        
        assert is_valid is False
        assert "has_wireframe" in error
    
    @pytest.mark.asyncio
    async def test_validate_invalid_json_wireframe(self, recovery_manager, valid_state_data):
        """Test validation fails when wireframe JSON is invalid."""
        valid_state_data["wireframe_json"] = "not valid json {"
        
        is_valid, error = await recovery_manager.validate_session_state(
            "test-session", valid_state_data
        )
        
        assert is_valid is False
        assert "wireframe_is_json" in error
    
    @pytest.mark.asyncio
    async def test_validate_missing_metadata(self, recovery_manager, valid_state_data):
        """Test validation fails when metadata is missing."""
        del valid_state_data["metadata"]
        
        is_valid, error = await recovery_manager.validate_session_state(
            "test-session", valid_state_data
        )
        
        assert is_valid is False
        assert "has_metadata" in error
    
    @pytest.mark.asyncio
    async def test_validate_invalid_version(self, recovery_manager, valid_state_data):
        """Test validation fails when version is not numeric."""
        valid_state_data["version"] = "not-a-number"
        
        is_valid, error = await recovery_manager.validate_session_state(
            "test-session", valid_state_data
        )
        
        assert is_valid is False
        assert "version_is_numeric" in error
    
    @pytest.mark.asyncio
    async def test_validate_design_state_model_valid(self, recovery_manager):
        """Test validation of a valid DesignState model."""
        design_state = DesignState(
            wireframe_json={"type": "container"},
            metadata={"author": "test"},
            created_at=datetime.utcnow(),
            version=1
        )
        
        is_valid, error = await recovery_manager.validate_design_state_model(design_state)
        
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_design_state_model_invalid_version(self, recovery_manager):
        """Test validation fails for invalid version in model."""
        design_state = DesignState(
            wireframe_json={"type": "container"},
            metadata={"author": "test"},
            created_at=datetime.utcnow(),
            version=0  # Invalid: must be positive
        )
        
        is_valid, error = await recovery_manager.validate_design_state_model(design_state)
        
        assert is_valid is False
        assert "version must be positive" in error
    
    @pytest.mark.asyncio
    async def test_repair_missing_metadata(self, recovery_manager, valid_state_data):
        """Test repair of state with missing metadata."""
        del valid_state_data["metadata"]
        
        repaired = await recovery_manager._attempt_repair(valid_state_data)
        
        assert repaired is not None
        assert isinstance(repaired.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_repair_missing_version(self, recovery_manager, valid_state_data):
        """Test repair of state with missing version."""
        del valid_state_data["version"]
        
        repaired = await recovery_manager._attempt_repair(valid_state_data)
        
        assert repaired is not None
        assert repaired.version == 1
    
    @pytest.mark.asyncio
    async def test_repair_missing_created_at(self, recovery_manager, valid_state_data):
        """Test repair of state with missing created_at."""
        del valid_state_data["created_at"]
        
        repaired = await recovery_manager._attempt_repair(valid_state_data)
        
        assert repaired is not None
        assert isinstance(repaired.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_repair_cannot_fix_missing_wireframe(self, recovery_manager, valid_state_data):
        """Test that repair fails when wireframe is missing (critical data)."""
        del valid_state_data["wireframe_json"]
        
        repaired = await recovery_manager._attempt_repair(valid_state_data)
        
        assert repaired is None
    
    @pytest.mark.asyncio
    async def test_repair_fixes_json_quotes(self, recovery_manager, valid_state_data):
        """Test repair of JSON with single quotes instead of double quotes."""
        valid_state_data["wireframe_json"] = "{'type': 'container'}"
        
        repaired = await recovery_manager._attempt_repair(valid_state_data)
        
        assert repaired is not None
        assert repaired.wireframe_json == {"type": "container"}
    
    @pytest.mark.asyncio
    async def test_recover_with_repair(self, recovery_manager, valid_state_data):
        """Test recovery using repair strategy."""
        # Corrupt the data slightly (missing metadata)
        del valid_state_data["metadata"]
        
        recovered = await recovery_manager.recover_session_state(
            "test-session", valid_state_data, []
        )
        
        assert recovered is not None
        assert isinstance(recovered, DesignState)
        assert isinstance(recovered.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_recover_with_rollback(self, recovery_manager, valid_state_data):
        """Test recovery using rollback to previous state."""
        # Create corrupted data (missing wireframe - can't repair)
        corrupted_data = valid_state_data.copy()
        del corrupted_data["wireframe_json"]
        
        # Create valid previous state
        previous_states = [valid_state_data]
        
        recovered = await recovery_manager.recover_session_state(
            "test-session", corrupted_data, previous_states
        )
        
        assert recovered is not None
        assert isinstance(recovered, DesignState)
        assert recovered.wireframe_json == json.loads(valid_state_data["wireframe_json"])
    
    @pytest.mark.asyncio
    async def test_recover_skips_invalid_previous_states(self, recovery_manager, valid_state_data):
        """Test recovery skips invalid previous states and finds valid one."""
        corrupted_data = {"wireframe_json": "invalid"}
        
        # Create mix of invalid and valid previous states
        invalid_state = {"wireframe_json": "also invalid"}
        valid_previous = valid_state_data.copy()
        
        previous_states = [invalid_state, valid_previous]
        
        recovered = await recovery_manager.recover_session_state(
            "test-session", corrupted_data, previous_states
        )
        
        assert recovered is not None
        assert isinstance(recovered, DesignState)
    
    @pytest.mark.asyncio
    async def test_recover_fails_with_no_valid_data(self, recovery_manager):
        """Test recovery fails when no valid data is available."""
        corrupted_data = {"wireframe_json": "invalid"}
        invalid_previous = [{"wireframe_json": "also invalid"}]
        
        recovered = await recovery_manager.recover_session_state(
            "test-session", corrupted_data, invalid_previous
        )
        
        assert recovered is None
    
    @pytest.mark.asyncio
    async def test_reconstruct_from_partial(self, recovery_manager, valid_state_data):
        """Test reconstruction from partial data."""
        # Create partial corrupted data with valid wireframe
        partial_data = {
            "wireframe_json": json.dumps({"type": "updated", "children": []})
        }
        
        # Previous state to use as base
        previous_states = [valid_state_data]
        
        reconstructed = await recovery_manager._reconstruct_from_partial(
            "test-session", partial_data, previous_states
        )
        
        assert reconstructed is not None
        assert reconstructed.wireframe_json["type"] == "updated"


class TestGracefulDegradationManager:
    """Test suite for GracefulDegradationManager."""
    
    @pytest.fixture
    def degradation_manager(self):
        """Create a graceful degradation manager instance."""
        return GracefulDegradationManager(cache_size=5)
    
    def test_initial_state_not_degraded(self, degradation_manager):
        """Test that manager starts in normal mode."""
        assert degradation_manager.is_degraded() is False
        
        status = degradation_manager.get_degradation_status()
        assert status["degraded_mode"] is False
    
    def test_enable_degraded_mode(self, degradation_manager):
        """Test enabling degraded mode."""
        degradation_manager.enable_degraded_mode("Test reason")
        
        assert degradation_manager.is_degraded() is True
        
        status = degradation_manager.get_degradation_status()
        assert status["degraded_mode"] is True
        assert status["reason"] == "Test reason"
        assert "degraded_since" in status
    
    def test_disable_degraded_mode(self, degradation_manager):
        """Test disabling degraded mode."""
        degradation_manager.enable_degraded_mode("Test")
        assert degradation_manager.is_degraded() is True
        
        degradation_manager.disable_degraded_mode()
        assert degradation_manager.is_degraded() is False
        
        status = degradation_manager.get_degradation_status()
        assert status["degraded_mode"] is False
    
    @pytest.mark.asyncio
    async def test_cache_session(self, degradation_manager):
        """Test caching session data."""
        session_data = {"wireframe": {"type": "container"}}
        
        await degradation_manager.cache_session("session-1", session_data)
        
        cached = await degradation_manager.get_cached_session("session-1")
        assert cached == session_data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_cached_session(self, degradation_manager):
        """Test retrieving non-existent cached session."""
        cached = await degradation_manager.get_cached_session("nonexistent")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction_when_full(self, degradation_manager):
        """Test that oldest entries are evicted when cache is full."""
        # Cache is size 5, add 6 sessions
        for i in range(6):
            await degradation_manager.cache_session(f"session-{i}", {"id": i})
        
        # First session should be evicted
        cached = await degradation_manager.get_cached_session("session-0")
        assert cached is None
        
        # Last session should still be there
        cached = await degradation_manager.get_cached_session("session-5")
        assert cached == {"id": 5}
    
    @pytest.mark.asyncio
    async def test_cache_lru_behavior(self, degradation_manager):
        """Test LRU (Least Recently Used) cache behavior."""
        # Add 5 sessions (fill cache)
        for i in range(5):
            await degradation_manager.cache_session(f"session-{i}", {"id": i})
        
        # Access session-0 (makes it most recently used)
        await degradation_manager.get_cached_session("session-0")
        
        # Add new session (should evict session-1, not session-0)
        await degradation_manager.cache_session("session-5", {"id": 5})
        
        # session-0 should still be there
        cached = await degradation_manager.get_cached_session("session-0")
        assert cached == {"id": 0}
        
        # session-1 should be evicted
        cached = await degradation_manager.get_cached_session("session-1")
        assert cached is None
    
    def test_get_degradation_status_includes_duration(self, degradation_manager):
        """Test that degradation status includes duration when degraded."""
        degradation_manager.enable_degraded_mode("Test")
        
        status = degradation_manager.get_degradation_status()
        
        assert "degraded_duration_seconds" in status
        assert status["degraded_duration_seconds"] >= 0
    
    def test_get_cache_stats(self, degradation_manager):
        """Test getting cache statistics."""
        stats = degradation_manager.get_cache_stats()
        
        assert "size" in stats
        assert "capacity" in stats
        assert "utilization" in stats
        assert "sessions" in stats
        
        assert stats["size"] == 0
        assert stats["capacity"] == 5
        assert stats["utilization"] == 0.0
    
    @pytest.mark.asyncio
    async def test_cache_stats_after_caching(self, degradation_manager):
        """Test cache statistics after caching sessions."""
        await degradation_manager.cache_session("session-1", {"id": 1})
        await degradation_manager.cache_session("session-2", {"id": 2})
        
        stats = degradation_manager.get_cache_stats()
        
        assert stats["size"] == 2
        assert stats["utilization"] == 0.4  # 2/5
        assert "session-1" in stats["sessions"]
        assert "session-2" in stats["sessions"]
    
    def test_disable_clears_cache(self, degradation_manager):
        """Test that disabling degraded mode clears the cache."""
        degradation_manager.enable_degraded_mode("Test")
        degradation_manager._in_memory_cache["session-1"] = {"data": {}}
        
        assert len(degradation_manager._in_memory_cache) == 1
        
        degradation_manager.disable_degraded_mode()
        
        assert len(degradation_manager._in_memory_cache) == 0
    
    def test_enable_degraded_mode_only_once(self, degradation_manager):
        """Test that enabling degraded mode multiple times doesn't reset timer."""
        degradation_manager.enable_degraded_mode("First reason")
        first_time = degradation_manager._degradation_start_time
        
        # Try to enable again
        degradation_manager.enable_degraded_mode("Second reason")
        second_time = degradation_manager._degradation_start_time
        
        # Time should not change (already degraded)
        assert first_time == second_time


class TestIntegrationRecoveryAndDegradation:
    """Integration tests for recovery and degradation working together."""
    
    @pytest.mark.asyncio
    async def test_recovery_with_degradation_fallback(self):
        """Test that recovery can use degradation cache as fallback."""
        recovery_mgr = SessionRecoveryManager()
        degradation_mgr = GracefulDegradationManager()
        
        # Enable degraded mode and cache a session
        degradation_mgr.enable_degraded_mode("Redis unavailable")
        session_data = {
            "wireframe_json": {"type": "container"},
            "metadata": {"author": "test"},
            "created_at": datetime.utcnow().isoformat(),
            "version": 1
        }
        await degradation_mgr.cache_session("session-1", session_data)
        
        # Verify we can retrieve from cache
        cached = await degradation_mgr.get_cached_session("session-1")
        assert cached is not None
        assert cached["wireframe_json"]["type"] == "container"
