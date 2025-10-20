# app/core/circuit_breaker.py
"""
Circuit Breaker pattern implementation for Redis connection failures.
Prevents cascading failures by opening the circuit after repeated failures.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """States of the circuit breaker."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open and prevents operation."""

    pass


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        success_threshold: Number of successes needed to close circuit from half-open
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = timedelta(seconds=recovery_timeout)
        self.success_threshold = success_threshold

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()

        logger.info(
            f"Circuit breaker initialized: "
            f"failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s, "
            f"success_threshold={success_threshold}"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args, **kwargs: Arguments for the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerError: If circuit is open
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self._state == CircuitState.OPEN:
                if self._should_attempt_recovery():
                    logger.info(
                        "Circuit breaker entering HALF_OPEN state for recovery attempt"
                    )
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. "
                        f"Recovery attempt in {self._time_until_recovery():.1f}s"
                    )

        # Execute the function
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure(e)
            raise

    async def _on_success(self):
        """Handle successful operation."""
        async with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                logger.debug(
                    f"Circuit breaker success in HALF_OPEN: "
                    f"{self._success_count}/{self.success_threshold}"
                )

                if self._success_count >= self.success_threshold:
                    logger.info("Circuit breaker closing after successful recovery")
                    self._state = CircuitState.CLOSED
                    self._success_count = 0

    async def _on_failure(self, error: Exception):
        """Handle failed operation."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()

            logger.warning(
                f"Circuit breaker failure {self._failure_count}/{self.failure_threshold}: {error}"
            )

            if self._state == CircuitState.HALF_OPEN:
                # Failure during recovery attempt - reopen circuit
                logger.warning(
                    "Circuit breaker reopening after failed recovery attempt"
                )
                self._state = CircuitState.OPEN
                self._success_count = 0
            elif self._failure_count >= self.failure_threshold:
                # Too many failures - open circuit
                logger.error(
                    f"Circuit breaker opening after {self._failure_count} failures"
                )
                self._state = CircuitState.OPEN

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._last_failure_time is None:
            return True

        time_since_failure = datetime.utcnow() - self._last_failure_time
        return time_since_failure >= self.recovery_timeout

    def _time_until_recovery(self) -> float:
        """Calculate seconds until recovery attempt."""
        if self._last_failure_time is None:
            return 0.0

        time_since_failure = datetime.utcnow() - self._last_failure_time
        time_remaining = self.recovery_timeout - time_since_failure
        return max(0.0, time_remaining.total_seconds())

    async def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        async with self._lock:
            logger.info("Circuit breaker manually reset")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current circuit breaker statistics.

        Returns:
            Dictionary with circuit breaker metrics
        """
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": (
                self._last_failure_time.isoformat() if self._last_failure_time else None
            ),
            "time_until_recovery": (
                self._time_until_recovery() if self._state == CircuitState.OPEN else 0.0
            ),
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
        }


def circuit_breaker(
    failure_threshold: int = 5, recovery_timeout: int = 60, success_threshold: int = 2
):
    """
    Decorator for applying circuit breaker pattern to async functions.

    Usage:
        @circuit_breaker(failure_threshold=3, recovery_timeout=30)
        async def my_function():
            # function code
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, success_threshold)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        # Attach breaker instance for access to stats/reset
        wrapper.circuit_breaker = breaker
        return wrapper

    return decorator
