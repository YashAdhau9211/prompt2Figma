# tests/test_error_handling_integration.py
"""
Integration tests for error handling and recovery mechanisms.
Tests the complete error handling flow including circuit breaker, recovery, and degradation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.core.state_store import RedisStateStore
from app.core.session_manager import DesignSessionManager
from app.core.circuit_breaker import CircuitBreakerError, CircuitState
from app.core.models import DesignSession, DesignState, SessionStatus


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with RedisStateStore."""
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_protects_redis_operations(self):
        """Test that circuit breaker protects Redis operations from cascading failures."""
        store = RedisStateStore("redis://localhost:6379")
        
        # Mock Redis to simulate failures
        with patch.object(store, '_redis', None):
            # Simulate connection failures
            async def failing_connect():
                raise ConnectionError("Redis unavailable")
            
            # Try to connect multiple times to open circuit
            for _ in range(5):
                try:
                    await store.circuit_breaker.call(failing_connect)
                except ConnectionError:
                    pass
            
            # Circuit should be open now
            assert store.circuit_breaker.state == CircuitState.OPEN
            
            # Next call should be rejected by circuit breaker
            with pytest.raises(CircuitBreakerError):
                await store.circuit_breaker.call(failing_connect)
    
    @pytest.mark.asyncio
    async def test_degraded_mode_activates_on_circuit_open(self):
        """Test that degraded mode activates when circuit breaker opens."""
        store = RedisStateStore("redis://localhost:6379")
        
        # Initially not degraded
        assert not store.degradation_manager.is_degraded()
        
        # Simulate failures to open circuit
        async def failing_operation():
            raise ConnectionError("Redis unavailable")
        
        # Fail enough times to open circuit
        for _ in range(5):
            try:
                await store._execute_with_circuit_breaker(failing_operation)
            except (ConnectionError, CircuitBreakerError):
                pass
        
        # Circuit should be open
        assert store.circuit_breaker.state == CircuitState.OPEN
        
        # Degraded mode should be enabled
        assert store.degradation_manager.is_degraded()
    
    @pytest.mark.asyncio
    async def test_health_status_reflects_circuit_and_degradation(self):
        """Test that health status includes circuit breaker and degradation info."""
        store = RedisStateStore("redis://localhost:6379")
        
        health = store.get_health_status()
        
        assert "circuit_breaker" in health
        assert "degradation" in health
        assert "healthy" in health
        
        # Initially should be healthy
        assert health["circuit_breaker"]["state"] == "closed"
        assert health["degradation"]["degraded_mode"] is False


class TestSessionRecoveryIntegration:
    """Test session recovery integration with state store."""
    
    @pytest.mark.asyncio
    async def test_corrupted_state_recovery_flow(self):
        """Test complete flow of detecting and recovering corrupted state."""
        # Test recovery manager directly without Redis
        from app.core.error_recovery import SessionRecoveryManager
        
        recovery_mgr = SessionRecoveryManager()
        
        # Mock corrupted data
        corrupted_data = {
            "wireframe_json": "invalid json {",
            "metadata": "{}",
            "created_at": datetime.utcnow().isoformat(),
            "version": "1"
        }
        
        # Mock previous valid state
        valid_data = {
            "wireframe_json": '{"type": "container"}',
            "metadata": '{"author": "test"}',
            "created_at": datetime.utcnow().isoformat(),
            "version": "1"
        }
        
        # Validation will fail
        is_valid, error = await recovery_mgr.validate_session_state(
            "test-session", corrupted_data
        )
        
        assert is_valid is False
        
        # Recovery should succeed using previous state
        recovered = await recovery_mgr.recover_session_state(
            "test-session", corrupted_data, [valid_data]
        )
        
        assert recovered is not None
        assert isinstance(recovered, DesignState)
    
    @pytest.mark.asyncio
    async def test_state_validation_with_valid_data(self):
        """Test that state validation works with valid data."""
        from app.core.error_recovery import SessionRecoveryManager
        
        recovery_mgr = SessionRecoveryManager()
        
        # Create valid state data
        valid_data = {
            "wireframe_json": '{"type": "container"}',
            "metadata": '{"author": "test"}',
            "created_at": datetime.utcnow().isoformat(),
            "version": "1"
        }
        
        # Validation should pass
        is_valid, error = await recovery_mgr.validate_session_state(
            "test-session", valid_data
        )
        
        assert is_valid is True
        assert error is None


class TestGracefulDegradationIntegration:
    """Test graceful degradation integration."""
    
    @pytest.mark.asyncio
    async def test_degraded_mode_uses_cache(self):
        """Test that degraded mode falls back to in-memory cache."""
        store = RedisStateStore("redis://localhost:6379")
        
        # Enable degraded mode
        store.degradation_manager.enable_degraded_mode("Testing")
        
        # Cache a session
        session_data = {
            "wireframe_json": {"type": "container"},
            "metadata": {"author": "test"},
            "created_at": datetime.utcnow().isoformat(),
            "version": 1
        }
        
        await store.degradation_manager.cache_session("test-session", session_data)
        
        # Mock get_session_metadata to return None (simulating Redis unavailable)
        with patch.object(store, 'get_session_metadata', return_value=None):
            # Get design state should use cache
            cached = await store.degradation_manager.get_cached_session("test-session")
            
            assert cached is not None
            assert cached["wireframe_json"]["type"] == "container"
    
    @pytest.mark.asyncio
    async def test_recovery_after_degradation(self):
        """Test that system recovers after degraded mode."""
        store = RedisStateStore("redis://localhost:6379")
        
        # Enable degraded mode
        store.degradation_manager.enable_degraded_mode("Testing")
        assert store.degradation_manager.is_degraded()
        
        # Disable degraded mode (simulating recovery)
        store.degradation_manager.disable_degraded_mode()
        assert not store.degradation_manager.is_degraded()
        
        # Health status should reflect recovery
        health = store.get_health_status()
        assert health["degradation"]["degraded_mode"] is False


class TestSessionManagerErrorHandling:
    """Test error handling in DesignSessionManager."""
    
    @pytest.mark.asyncio
    async def test_session_manager_handles_store_failures(self):
        """Test that session manager handles state store failures gracefully."""
        # Create mock state store
        mock_store = MagicMock(spec=RedisStateStore)
        mock_store.create_session = AsyncMock(return_value=False)
        
        # Mock version manager and prompt processor to avoid initialization issues
        with patch('app.core.session_manager.VersionManager'):
            with patch('app.core.session_manager.EnhancedPromptProcessor'):
                manager = DesignSessionManager(mock_store)
                
                # Attempt to create session - should raise SessionManagerError
                from app.core.session_manager import SessionManagerError
                
                with pytest.raises(SessionManagerError) as exc_info:
                    await manager.create_session("user-1", "test prompt")
                
                assert "Failed to store session" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_session_manager_handles_missing_sessions(self):
        """Test that session manager handles missing sessions gracefully."""
        mock_store = MagicMock(spec=RedisStateStore)
        mock_store.get_session_metadata = AsyncMock(return_value=None)
        
        # Mock version manager and prompt processor
        with patch('app.core.session_manager.VersionManager'):
            with patch('app.core.session_manager.EnhancedPromptProcessor'):
                manager = DesignSessionManager(mock_store)
                
                # Get non-existent session - should return None
                session = await manager.get_session("nonexistent-session")
                
                assert session is None


class TestContextEngineErrorHandling:
    """Test error handling in ContextProcessingEngine."""
    
    @pytest.mark.asyncio
    async def test_context_engine_handles_processing_errors(self):
        """Test that context engine handles processing errors gracefully."""
        from app.core.context_engine import ContextProcessingEngine
        from app.core.models import EditIntent
        
        engine = ContextProcessingEngine()
        
        # Create a design state
        design_state = DesignState(
            wireframe_json={"type": "container"},
            metadata={},
            version=1
        )
        
        # Process with invalid/problematic prompt
        result = await engine.process_edit_with_context(
            design_state,
            "",  # Empty prompt
            []
        )
        
        # Should return a result even with empty prompt
        assert result is not None
        assert result.edit_intent == EditIntent.UNCLEAR
    
    @pytest.mark.asyncio
    async def test_context_engine_fallback_on_reference_resolution_failure(self):
        """Test that context engine falls back gracefully on reference resolution failure."""
        from app.core.context_engine import ContextProcessingEngine
        
        engine = ContextProcessingEngine()
        
        # Create a design state with None wireframe (edge case)
        design_state = DesignState(
            wireframe_json={},
            metadata={},
            version=1
        )
        
        # Process with contextual reference
        result = await engine.process_edit_with_context(
            design_state,
            "make it bigger",
            []
        )
        
        # Should handle gracefully even with empty design
        assert result is not None
        # Confidence should be low due to no elements to reference
        assert result.confidence_score < 0.7


class TestEndToEndErrorScenarios:
    """End-to-end tests for complete error scenarios."""
    
    @pytest.mark.asyncio
    async def test_complete_failure_and_recovery_flow(self):
        """Test complete flow from failure through recovery."""
        store = RedisStateStore("redis://localhost:6379")
        
        # 1. Simulate Redis failures
        async def failing_op():
            raise ConnectionError("Redis down")
        
        # Trigger circuit breaker by calling through _execute_with_circuit_breaker
        for _ in range(5):
            try:
                await store._execute_with_circuit_breaker(failing_op)
            except (ConnectionError, CircuitBreakerError):
                pass
        
        # 2. Verify circuit is open and degraded mode is active
        assert store.circuit_breaker.state == CircuitState.OPEN
        assert store.degradation_manager.is_degraded()
        
        # 3. Cache some data in degraded mode
        await store.degradation_manager.cache_session("session-1", {"data": "test"})
        
        # 4. Simulate recovery - reset circuit breaker
        await store.circuit_breaker.reset()
        
        # 5. Verify circuit is closed
        assert store.circuit_breaker.state == CircuitState.CLOSED
        
        # 6. Disable degraded mode
        store.degradation_manager.disable_degraded_mode()
        
        # 7. Verify system is healthy
        health = store.get_health_status()
        assert health["healthy"] is True
    
    @pytest.mark.asyncio
    async def test_partial_failure_with_graceful_degradation(self):
        """Test system continues operating with partial failures."""
        store = RedisStateStore("redis://localhost:6379")
        
        # Enable degraded mode
        store.degradation_manager.enable_degraded_mode("Partial failure")
        
        # System should still be able to cache and retrieve data
        test_data = {"wireframe": {"type": "test"}}
        await store.degradation_manager.cache_session("session-1", test_data)
        
        cached = await store.degradation_manager.get_cached_session("session-1")
        assert cached == test_data
        
        # Health status should indicate degraded but operational
        health = store.get_health_status()
        assert health["degradation"]["degraded_mode"] is True
        assert health["healthy"] is False  # Not fully healthy, but operational
