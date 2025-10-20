# app/core/security.py
"""
Security module for the Stateful Iterative Design Engine.
Implements session ID generation, rate limiting, input sanitization, and security monitoring.
"""

import asyncio
import hashlib
import logging
import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors."""

    pass


class SessionIDGenerator:
    """
    Generates cryptographically secure session IDs.

    Requirements: 2.5
    """

    @staticmethod
    def generate() -> str:
        """
        Generate a cryptographically secure session ID.

        Returns:
            A 32-character hexadecimal session ID
        """
        # Generate 16 random bytes (128 bits) and convert to hex
        random_bytes = secrets.token_bytes(16)
        session_id = random_bytes.hex()

        logger.debug(f"Generated secure session ID: {session_id[:8]}...")
        return session_id

    @staticmethod
    def validate(session_id: str) -> bool:
        """
        Validate that a session ID has the correct format.

        Args:
            session_id: The session ID to validate

        Returns:
            True if valid, False otherwise
        """
        # Session ID should be 32 hexadecimal characters
        if not session_id or not isinstance(session_id, str):
            return False

        if len(session_id) != 32:
            return False

        # Check if all characters are hexadecimal
        try:
            int(session_id, 16)
            return True
        except ValueError:
            return False


class RateLimiter:
    """
    Rate limiter for edit requests per session.

    Implements a sliding window rate limiting algorithm to prevent abuse.

    Requirements: 2.5, 5.5
    """

    def __init__(
        self,
        max_requests_per_minute: int = 10,
        max_requests_per_hour: int = 100,
        max_requests_per_day: int = 500,
    ):
        """
        Initialize the rate limiter.

        Args:
            max_requests_per_minute: Maximum requests allowed per minute
            max_requests_per_hour: Maximum requests allowed per hour
            max_requests_per_day: Maximum requests allowed per day
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_hour = max_requests_per_hour
        self.max_requests_per_day = max_requests_per_day

        # Store request timestamps per session
        self._request_history: Dict[str, List[datetime]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(self, session_id: str) -> Tuple[bool, str]:
        """
        Check if a request is allowed based on rate limits.

        Args:
            session_id: The session identifier

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        async with self._lock:
            now = datetime.utcnow()

            # Get request history for this session
            history = self._request_history[session_id]

            # Remove old requests outside the day window
            cutoff_day = now - timedelta(days=1)
            history = [ts for ts in history if ts > cutoff_day]
            self._request_history[session_id] = history

            # Check daily limit
            if len(history) >= self.max_requests_per_day:
                logger.warning(
                    f"Rate limit exceeded for session {session_id}: daily limit"
                )
                return False, "Daily rate limit exceeded. Please try again tomorrow."

            # Check hourly limit
            cutoff_hour = now - timedelta(hours=1)
            recent_hour = [ts for ts in history if ts > cutoff_hour]
            if len(recent_hour) >= self.max_requests_per_hour:
                logger.warning(
                    f"Rate limit exceeded for session {session_id}: hourly limit"
                )
                return False, "Hourly rate limit exceeded. Please try again later."

            # Check minute limit
            cutoff_minute = now - timedelta(minutes=1)
            recent_minute = [ts for ts in history if ts > cutoff_minute]
            if len(recent_minute) >= self.max_requests_per_minute:
                logger.warning(
                    f"Rate limit exceeded for session {session_id}: minute limit"
                )
                return (
                    False,
                    "Rate limit exceeded. Please wait a moment before trying again.",
                )

            # Add current request to history
            history.append(now)

            return True, "Request allowed"

    async def reset_session_limits(self, session_id: str):
        """
        Reset rate limits for a specific session.

        Args:
            session_id: The session identifier
        """
        async with self._lock:
            if session_id in self._request_history:
                del self._request_history[session_id]
                logger.info(f"Reset rate limits for session {session_id}")

    def get_session_stats(self, session_id: str) -> Dict[str, int]:
        """
        Get rate limit statistics for a session.

        Args:
            session_id: The session identifier

        Returns:
            Dictionary with request counts for different time windows
        """
        now = datetime.utcnow()
        history = self._request_history.get(session_id, [])

        cutoff_minute = now - timedelta(minutes=1)
        cutoff_hour = now - timedelta(hours=1)
        cutoff_day = now - timedelta(days=1)

        return {
            "requests_last_minute": len([ts for ts in history if ts > cutoff_minute]),
            "requests_last_hour": len([ts for ts in history if ts > cutoff_hour]),
            "requests_last_day": len([ts for ts in history if ts > cutoff_day]),
            "limit_minute": self.max_requests_per_minute,
            "limit_hour": self.max_requests_per_hour,
            "limit_day": self.max_requests_per_day,
        }


class InputSanitizer:
    """
    Sanitizes user input to prevent injection attacks and malicious content.

    Requirements: 3.3
    """

    # Patterns for detecting potentially malicious content
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--\s*$)",
        r"(;\s*DROP\b)",
    ]

    # Patterns for detecting script injection
    SCRIPT_INJECTION_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    # Patterns for detecting command injection
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\$\(",
        r">\s*/dev/",
    ]

    # Maximum lengths for different input types
    MAX_PROMPT_LENGTH = 3000
    MAX_USER_ID_LENGTH = 100
    MAX_SESSION_ID_LENGTH = 64

    @classmethod
    def sanitize_prompt(cls, prompt: str) -> Tuple[str, List[str]]:
        """
        Sanitize a user prompt for security issues.

        Args:
            prompt: The user's prompt text

        Returns:
            Tuple of (sanitized_prompt, warnings)

        Raises:
            SecurityError: If the prompt contains dangerous content
        """
        warnings = []

        # Check if prompt is empty or None
        if not prompt:
            raise SecurityError("Prompt cannot be empty")

        # Check length
        if len(prompt) > cls.MAX_PROMPT_LENGTH:
            raise SecurityError(
                f"Prompt exceeds maximum length of {cls.MAX_PROMPT_LENGTH} characters"
            )

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise SecurityError(
                    "Prompt contains potentially malicious SQL patterns"
                )

        # Check for script injection patterns
        for pattern in cls.SCRIPT_INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                raise SecurityError(
                    "Prompt contains potentially malicious script patterns"
                )

        # Check for command injection patterns
        for pattern in cls.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, prompt):
                warnings.append("Prompt contains special characters that were escaped")

        # Remove null bytes
        sanitized = prompt.replace("\x00", "")

        # Normalize whitespace
        sanitized = " ".join(sanitized.split())

        # Escape HTML entities
        sanitized = (
            sanitized.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )

        if sanitized != prompt:
            warnings.append("Prompt was sanitized for security")

        return sanitized, warnings

    @classmethod
    def sanitize_user_id(cls, user_id: str) -> str:
        """
        Sanitize a user ID.

        Args:
            user_id: The user identifier

        Returns:
            Sanitized user ID

        Raises:
            SecurityError: If the user ID is invalid
        """
        if not user_id:
            raise SecurityError("User ID cannot be empty")

        if len(user_id) > cls.MAX_USER_ID_LENGTH:
            raise SecurityError(
                f"User ID exceeds maximum length of {cls.MAX_USER_ID_LENGTH}"
            )

        # Only allow alphanumeric, hyphens, underscores, and dots
        if not re.match(r"^[a-zA-Z0-9._-]+$", user_id):
            raise SecurityError("User ID contains invalid characters")

        return user_id

    @classmethod
    def sanitize_session_id(cls, session_id: str) -> str:
        """
        Sanitize and validate a session ID.

        Args:
            session_id: The session identifier

        Returns:
            Sanitized session ID

        Raises:
            SecurityError: If the session ID is invalid
        """
        if not session_id:
            raise SecurityError("Session ID cannot be empty")

        if len(session_id) > cls.MAX_SESSION_ID_LENGTH:
            raise SecurityError(
                f"Session ID exceeds maximum length of {cls.MAX_SESSION_ID_LENGTH}"
            )

        # Validate session ID format
        if not SessionIDGenerator.validate(session_id):
            raise SecurityError("Invalid session ID format")

        return session_id


class SecurityMonitor:
    """
    Monitors and logs security events.

    Requirements: 2.5
    """

    def __init__(self):
        """Initialize the security monitor."""
        self._events: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._max_events = 1000  # Keep last 1000 events in memory

    async def log_security_event(
        self,
        event_type: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ):
        """
        Log a security event.

        Args:
            event_type: Type of security event
            session_id: Optional session identifier
            user_id: Optional user identifier
            details: Optional additional details
            severity: Event severity (info, warning, error, critical)
        """
        async with self._lock:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "session_id": session_id,
                "user_id": user_id,
                "details": details or {},
                "severity": severity,
            }

            self._events.append(event)

            # Keep only the most recent events
            if len(self._events) > self._max_events:
                self._events = self._events[-self._max_events :]

            # Log to standard logger
            log_message = f"Security event: {event_type}"
            if session_id:
                log_message += f" [session: {session_id}]"
            if user_id:
                log_message += f" [user: {user_id}]"

            if severity == "critical":
                logger.critical(log_message, extra=event)
            elif severity == "error":
                logger.error(log_message, extra=event)
            elif severity == "warning":
                logger.warning(log_message, extra=event)
            else:
                logger.info(log_message, extra=event)

    async def get_recent_events(
        self,
        limit: int = 100,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent security events.

        Args:
            limit: Maximum number of events to return
            severity: Filter by severity level
            event_type: Filter by event type

        Returns:
            List of security events
        """
        async with self._lock:
            events = self._events.copy()

        # Apply filters
        if severity:
            events = [e for e in events if e["severity"] == severity]

        if event_type:
            events = [e for e in events if e["event_type"] == event_type]

        # Return most recent events
        return events[-limit:]

    async def get_session_events(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get security events for a specific session.

        Args:
            session_id: The session identifier
            limit: Maximum number of events to return

        Returns:
            List of security events for the session
        """
        async with self._lock:
            events = [e for e in self._events if e.get("session_id") == session_id]

        return events[-limit:]

    async def get_security_stats(self) -> Dict[str, Any]:
        """
        Get security statistics.

        Returns:
            Dictionary with security statistics
        """
        async with self._lock:
            events = self._events.copy()

        # Count events by severity
        severity_counts = defaultdict(int)
        for event in events:
            severity_counts[event["severity"]] += 1

        # Count events by type
        type_counts = defaultdict(int)
        for event in events:
            type_counts[event["event_type"]] += 1

        # Get recent critical events
        recent_critical = [e for e in events[-100:] if e["severity"] == "critical"]

        return {
            "total_events": len(events),
            "severity_distribution": dict(severity_counts),
            "event_type_distribution": dict(type_counts),
            "recent_critical_events": len(recent_critical),
            "oldest_event": events[0]["timestamp"] if events else None,
            "newest_event": events[-1]["timestamp"] if events else None,
        }


# Global instances
_rate_limiter: Optional[RateLimiter] = None
_security_monitor: Optional[SecurityMonitor] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_security_monitor() -> SecurityMonitor:
    """Get the global security monitor instance."""
    global _security_monitor
    if _security_monitor is None:
        _security_monitor = SecurityMonitor()
    return _security_monitor
