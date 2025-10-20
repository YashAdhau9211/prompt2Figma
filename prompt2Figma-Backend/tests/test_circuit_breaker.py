# tests/test_circuit_breaker.py
"""
Unit tests for the Circuit Breaker pattern implementation.
Tests circuit state transitions, failure handling, and recovery.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.core.circuit_breaker import (
    CircuitBreaker, CircuitState, CircuitBreakerError, circuit_breaker
)


class TestCircuitBreaker:
    """Test suite for CircuitBreaker class."""
    
    @pytest.fixture
    def breaker(self):
        """Create a circuit breaker with test-friendly settings."""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=2,  # 2 seconds for faster tests
            success_threshold=2
        )
    
    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, breaker):
        """Test that circuit breaker starts in CLOSED state."""
        assert breaker.state == CircuitState.CLOSED
        stats = breaker.get_stats()
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_successful_call_passes_through(self, breaker):
        """Test that successful calls pass through when circuit is closed."""
        async def successful_operation():
            return "success"
        
        result = await breaker.call(successful_operation)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_failed_call_increments_failure_count(self, breaker):
        """Test that failed calls increment the failure counter."""
        async def failing_operation():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await breaker.call(failing_operation)
        
        stats = breaker.get_stats()
        assert stats["failure_count"] == 1
        assert breaker.state == CircuitState.CLOSED  # Still closed, below threshold
    
    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold_failures(self, breaker):
        """Test that circuit opens after reaching failure threshold."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Fail 3 times (threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        assert breaker.state == CircuitState.OPEN
        stats = breaker.get_stats()
        assert stats["state"] == "open"
        assert stats["failure_count"] == 3
    
    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, breaker):
        """Test that open circuit rejects calls immediately."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        assert breaker.state == CircuitState.OPEN
        
        # Next call should be rejected without executing
        async def should_not_execute():
            pytest.fail("This should not be executed")
        
        with pytest.raises(CircuitBreakerError) as exc_info:
            await breaker.call(should_not_execute)
        
        assert "Circuit breaker is OPEN" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_circuit_enters_half_open_after_timeout(self, breaker):
        """Test that circuit enters HALF_OPEN state after recovery timeout."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for recovery timeout
        await asyncio.sleep(2.1)
        
        # Next call should enter HALF_OPEN state
        async def test_operation():
            return "testing"
        
        result = await breaker.call(test_operation)
        assert result == "testing"
        # After one success, still in HALF_OPEN (needs 2 successes)
        assert breaker.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_circuit_closes_after_successful_recovery(self, breaker):
        """Test that circuit closes after enough successful calls in HALF_OPEN."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        # Wait for recovery timeout
        await asyncio.sleep(2.1)
        
        # Make successful calls to close circuit
        async def successful_operation():
            return "success"
        
        # First success - still HALF_OPEN
        await breaker.call(successful_operation)
        assert breaker.state == CircuitState.HALF_OPEN
        
        # Second success - should close
        await breaker.call(successful_operation)
        assert breaker.state == CircuitState.CLOSED
        
        stats = breaker.get_stats()
        assert stats["failure_count"] == 0
    
    @pytest.mark.asyncio
    async def test_circuit_reopens_on_failure_during_recovery(self, breaker):
        """Test that circuit reopens if call fails during HALF_OPEN state."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        # Wait for recovery timeout
        await asyncio.sleep(2.1)
        
        # Fail during recovery
        with pytest.raises(ValueError):
            await breaker.call(failing_operation)
        
        # Should be back to OPEN
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_manual_reset(self, breaker):
        """Test manual reset of circuit breaker."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        assert breaker.state == CircuitState.OPEN
        
        # Manual reset
        await breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        stats = breaker.get_stats()
        assert stats["failure_count"] == 0
        assert stats["success_count"] == 0
    
    @pytest.mark.asyncio
    async def test_get_stats_includes_all_metrics(self, breaker):
        """Test that get_stats returns all expected metrics."""
        stats = breaker.get_stats()
        
        assert "state" in stats
        assert "failure_count" in stats
        assert "success_count" in stats
        assert "last_failure_time" in stats
        assert "time_until_recovery" in stats
        assert "failure_threshold" in stats
        assert "success_threshold" in stats
    
    @pytest.mark.asyncio
    async def test_time_until_recovery_calculation(self, breaker):
        """Test that time until recovery is calculated correctly."""
        async def failing_operation():
            raise ValueError("Test error")
        
        # Open the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_operation)
        
        stats = breaker.get_stats()
        time_until_recovery = stats["time_until_recovery"]
        
        # Should be close to 2 seconds (recovery timeout)
        assert 1.5 <= time_until_recovery <= 2.5
        
        # Wait a bit
        await asyncio.sleep(1)
        
        stats = breaker.get_stats()
        new_time = stats["time_until_recovery"]
        
        # Should be less than before
        assert new_time < time_until_recovery


class TestCircuitBreakerDecorator:
    """Test suite for circuit_breaker decorator."""
    
    @pytest.mark.asyncio
    async def test_decorator_applies_circuit_breaker(self):
        """Test that decorator applies circuit breaker to function."""
        @circuit_breaker(failure_threshold=2, recovery_timeout=1)
        async def test_function():
            return "success"
        
        result = await test_function()
        assert result == "success"
        
        # Check that circuit breaker is attached
        assert hasattr(test_function, 'circuit_breaker')
        assert isinstance(test_function.circuit_breaker, CircuitBreaker)
    
    @pytest.mark.asyncio
    async def test_decorator_opens_circuit_on_failures(self):
        """Test that decorated function opens circuit on failures."""
        call_count = 0
        
        @circuit_breaker(failure_threshold=2, recovery_timeout=1)
        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Test error")
        
        # Fail twice to open circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                await failing_function()
        
        assert call_count == 2
        assert failing_function.circuit_breaker.state == CircuitState.OPEN
        
        # Next call should be rejected
        with pytest.raises(CircuitBreakerError):
            await failing_function()
        
        # Call count should not increase (function not executed)
        assert call_count == 2
    
    @pytest.mark.asyncio
    async def test_decorator_can_access_stats(self):
        """Test that we can access circuit breaker stats through decorator."""
        @circuit_breaker(failure_threshold=3)
        async def test_function():
            return "success"
        
        await test_function()
        
        stats = test_function.circuit_breaker.get_stats()
        assert stats["state"] == "closed"
        assert stats["failure_count"] == 0


class TestCircuitBreakerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_calls_with_circuit_breaker(self):
        """Test that circuit breaker handles concurrent calls correctly."""
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=2)
        call_count = 0
        
        async def concurrent_operation():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate some work
            return "success"
        
        # Make multiple concurrent calls
        tasks = [breaker.call(concurrent_operation) for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(r == "success" for r in results)
        assert call_count == 10
    
    @pytest.mark.asyncio
    async def test_different_exception_types(self):
        """Test that circuit breaker handles different exception types."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        async def value_error():
            raise ValueError("Value error")
        
        async def type_error():
            raise TypeError("Type error")
        
        # Different exceptions should all count as failures
        with pytest.raises(ValueError):
            await breaker.call(value_error)
        
        with pytest.raises(TypeError):
            await breaker.call(type_error)
        
        assert breaker.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_zero_failure_threshold(self):
        """Test circuit breaker with zero failure threshold (always open)."""
        breaker = CircuitBreaker(failure_threshold=0)
        
        async def any_operation():
            return "success"
        
        # Should work initially (closed state)
        result = await breaker.call(any_operation)
        assert result == "success"
