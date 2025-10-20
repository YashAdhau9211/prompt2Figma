# tests/test_security.py
"""
Security tests for the Stateful Iterative Design Engine.
Tests session ID generation, rate limiting, input sanitization, and security monitoring.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.core.security import (
    SessionIDGenerator, RateLimiter, InputSanitizer,
    SecurityMonitor, SecurityError
)


class TestSessionIDGenerator:
    """Test secure session ID generation and validation."""
    
    def test_generate_session_id(self):
        """Test that session IDs are generated correctly."""
        session_id = SessionIDGenerator.generate()
        
        # Should be 32 characters
        assert len(session_id) == 32
        
        # Should be hexadecimal
        assert all(c in '0123456789abcdef' for c in session_id)
    
    def test_session_id_uniqueness(self):
        """Test that generated session IDs are unique."""
        ids = set()
        for _ in range(1000):
            session_id = SessionIDGenerator.generate()
            ids.add(session_id)
        
        # All IDs should be unique
        assert len(ids) == 1000
    
    def test_validate_valid_session_id(self):
        """Test validation of valid session IDs."""
        session_id = SessionIDGenerator.generate()
        assert SessionIDGenerator.validate(session_id) is True
    
    def test_validate_invalid_session_id_length(self):
        """Test validation rejects incorrect length."""
        assert SessionIDGenerator.validate("abc123") is False
        assert SessionIDGenerator.validate("a" * 31) is False
        assert SessionIDGenerator.validate("a" * 33) is False
    
    def test_validate_invalid_session_id_characters(self):
        """Test validation rejects non-hexadecimal characters."""
        assert SessionIDGenerator.validate("g" * 32) is False
        assert SessionIDGenerator.validate("xyz" + "a" * 29) is False
    
    def test_validate_empty_session_id(self):
        """Test validation rejects empty or None."""
        assert SessionIDGenerator.validate("") is False
        assert SessionIDGenerator.validate(None) is False
    
    def test_validate_non_string_session_id(self):
        """Test validation rejects non-string types."""
        assert SessionIDGenerator.validate(12345) is False
        assert SessionIDGenerator.validate([]) is False


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_limits(self):
        """Test that requests within limits are allowed."""
        limiter = RateLimiter(
            max_requests_per_minute=5,
            max_requests_per_hour=20,
            max_requests_per_day=50
        )
        
        session_id = "test_session_123"
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, reason = await limiter.check_rate_limit(session_id)
            assert allowed is True
            assert "allowed" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_minute_limit(self):
        """Test that minute limit is enforced."""
        limiter = RateLimiter(
            max_requests_per_minute=3,
            max_requests_per_hour=100,
            max_requests_per_day=500
        )
        
        session_id = "test_session_minute"
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed, _ = await limiter.check_rate_limit(session_id)
            assert allowed is True
        
        # 4th request should be blocked
        allowed, reason = await limiter.check_rate_limit(session_id)
        assert allowed is False
        assert "minute" in reason.lower() or "wait" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_hourly_limit(self):
        """Test that hourly limit is enforced."""
        limiter = RateLimiter(
            max_requests_per_minute=100,
            max_requests_per_hour=5,
            max_requests_per_day=500
        )
        
        session_id = "test_session_hour"
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed, _ = await limiter.check_rate_limit(session_id)
            assert allowed is True
        
        # 6th request should be blocked
        allowed, reason = await limiter.check_rate_limit(session_id)
        assert allowed is False
        assert "hour" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_daily_limit(self):
        """Test that daily limit is enforced."""
        limiter = RateLimiter(
            max_requests_per_minute=100,
            max_requests_per_hour=100,
            max_requests_per_day=3
        )
        
        session_id = "test_session_day"
        
        # First 3 requests should be allowed
        for i in range(3):
            allowed, _ = await limiter.check_rate_limit(session_id)
            assert allowed is True
        
        # 4th request should be blocked
        allowed, reason = await limiter.check_rate_limit(session_id)
        assert allowed is False
        assert "day" in reason.lower() or "daily" in reason.lower()
    
    @pytest.mark.asyncio
    async def test_rate_limiter_different_sessions(self):
        """Test that rate limits are per-session."""
        limiter = RateLimiter(
            max_requests_per_minute=2,
            max_requests_per_hour=10,
            max_requests_per_day=50
        )
        
        session1 = "session_1"
        session2 = "session_2"
        
        # Use up session1's limit
        for i in range(2):
            allowed, _ = await limiter.check_rate_limit(session1)
            assert allowed is True
        
        # session1 should be blocked
        allowed, _ = await limiter.check_rate_limit(session1)
        assert allowed is False
        
        # session2 should still be allowed
        allowed, _ = await limiter.check_rate_limit(session2)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_reset(self):
        """Test resetting rate limits for a session."""
        limiter = RateLimiter(
            max_requests_per_minute=2,
            max_requests_per_hour=10,
            max_requests_per_day=50
        )
        
        session_id = "test_session_reset"
        
        # Use up the limit
        for i in range(2):
            await limiter.check_rate_limit(session_id)
        
        # Should be blocked
        allowed, _ = await limiter.check_rate_limit(session_id)
        assert allowed is False
        
        # Reset limits
        await limiter.reset_session_limits(session_id)
        
        # Should be allowed again
        allowed, _ = await limiter.check_rate_limit(session_id)
        assert allowed is True
    
    @pytest.mark.asyncio
    async def test_rate_limiter_get_stats(self):
        """Test getting rate limit statistics."""
        limiter = RateLimiter(
            max_requests_per_minute=10,
            max_requests_per_hour=50,
            max_requests_per_day=200
        )
        
        session_id = "test_session_stats"
        
        # Make some requests
        for i in range(5):
            await limiter.check_rate_limit(session_id)
        
        # Get stats
        stats = limiter.get_session_stats(session_id)
        
        assert stats["requests_last_minute"] == 5
        assert stats["requests_last_hour"] == 5
        assert stats["requests_last_day"] == 5
        assert stats["limit_minute"] == 10
        assert stats["limit_hour"] == 50
        assert stats["limit_day"] == 200


class TestInputSanitizer:
    """Test input sanitization functionality."""
    
    def test_sanitize_valid_prompt(self):
        """Test sanitizing a valid prompt."""
        prompt = "Create a login form with email and password fields"
        sanitized, warnings = InputSanitizer.sanitize_prompt(prompt)
        
        assert sanitized is not None
        assert len(warnings) == 0
    
    def test_sanitize_empty_prompt(self):
        """Test that empty prompts are rejected."""
        with pytest.raises(SecurityError, match="cannot be empty"):
            InputSanitizer.sanitize_prompt("")
        
        with pytest.raises(SecurityError, match="cannot be empty"):
            InputSanitizer.sanitize_prompt(None)
    
    def test_sanitize_prompt_too_long(self):
        """Test that overly long prompts are rejected."""
        long_prompt = "a" * 10000
        with pytest.raises(SecurityError, match="exceeds maximum length"):
            InputSanitizer.sanitize_prompt(long_prompt)
    
    def test_sanitize_sql_injection(self):
        """Test detection of SQL injection patterns."""
        malicious_prompts = [
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM passwords",
            "admin'--",
            "1; DELETE FROM sessions",
        ]
        
        for prompt in malicious_prompts:
            with pytest.raises(SecurityError, match="SQL"):
                InputSanitizer.sanitize_prompt(prompt)
    
    def test_sanitize_script_injection(self):
        """Test detection of script injection patterns."""
        malicious_prompts = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<iframe src='evil.com'></iframe>",
        ]
        
        for prompt in malicious_prompts:
            with pytest.raises(SecurityError, match="script"):
                InputSanitizer.sanitize_prompt(prompt)
    
    def test_sanitize_html_entities(self):
        """Test that HTML entities are escaped."""
        prompt = "Create a form with <input> and 'quotes' & \"double quotes\""
        sanitized, warnings = InputSanitizer.sanitize_prompt(prompt)
        
        assert "&lt;" in sanitized
        assert "&gt;" in sanitized
        assert "&amp;" in sanitized
        assert "&quot;" in sanitized
        assert "&#x27;" in sanitized
        assert len(warnings) > 0
    
    def test_sanitize_whitespace_normalization(self):
        """Test that whitespace is normalized."""
        prompt = "Create   a    form\n\nwith   multiple    spaces"
        sanitized, warnings = InputSanitizer.sanitize_prompt(prompt)
        
        # Should have single spaces
        assert "  " not in sanitized
        assert "\n" not in sanitized
    
    def test_sanitize_null_bytes(self):
        """Test that null bytes are removed."""
        prompt = "Create a form\x00with null bytes"
        sanitized, warnings = InputSanitizer.sanitize_prompt(prompt)
        
        assert "\x00" not in sanitized
    
    def test_sanitize_valid_user_id(self):
        """Test sanitizing valid user IDs."""
        valid_ids = [
            "user123",
            "john.doe",
            "user_name",
            "test-user",
            "User123",
        ]
        
        for user_id in valid_ids:
            sanitized = InputSanitizer.sanitize_user_id(user_id)
            assert sanitized == user_id
    
    def test_sanitize_invalid_user_id(self):
        """Test that invalid user IDs are rejected."""
        invalid_ids = [
            "",
            None,
            "user@example.com",
            "user name",
            "user;drop",
            "user<script>",
            "a" * 200,
        ]
        
        for user_id in invalid_ids:
            with pytest.raises(SecurityError):
                InputSanitizer.sanitize_user_id(user_id)
    
    def test_sanitize_valid_session_id(self):
        """Test sanitizing valid session IDs."""
        session_id = SessionIDGenerator.generate()
        sanitized = InputSanitizer.sanitize_session_id(session_id)
        assert sanitized == session_id
    
    def test_sanitize_invalid_session_id(self):
        """Test that invalid session IDs are rejected."""
        invalid_ids = [
            "",
            None,
            "invalid",
            "xyz123",
            "a" * 100,
        ]
        
        for session_id in invalid_ids:
            with pytest.raises(SecurityError):
                InputSanitizer.sanitize_session_id(session_id)


class TestSecurityMonitor:
    """Test security monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_log_security_event(self):
        """Test logging security events."""
        monitor = SecurityMonitor()
        
        await monitor.log_security_event(
            "test_event",
            session_id="session123",
            user_id="user456",
            details={"key": "value"},
            severity="info"
        )
        
        events = await monitor.get_recent_events(limit=10)
        assert len(events) == 1
        assert events[0]["event_type"] == "test_event"
        assert events[0]["session_id"] == "session123"
        assert events[0]["user_id"] == "user456"
        assert events[0]["severity"] == "info"
    
    @pytest.mark.asyncio
    async def test_log_multiple_events(self):
        """Test logging multiple security events."""
        monitor = SecurityMonitor()
        
        for i in range(10):
            await monitor.log_security_event(
                f"event_{i}",
                session_id=f"session_{i}",
                severity="info"
            )
        
        events = await monitor.get_recent_events(limit=20)
        assert len(events) == 10
    
    @pytest.mark.asyncio
    async def test_filter_events_by_severity(self):
        """Test filtering events by severity."""
        monitor = SecurityMonitor()
        
        await monitor.log_security_event("event1", severity="info")
        await monitor.log_security_event("event2", severity="warning")
        await monitor.log_security_event("event3", severity="error")
        await monitor.log_security_event("event4", severity="critical")
        
        # Get only warnings
        warnings = await monitor.get_recent_events(severity="warning")
        assert len(warnings) == 1
        assert warnings[0]["event_type"] == "event2"
        
        # Get only errors
        errors = await monitor.get_recent_events(severity="error")
        assert len(errors) == 1
        assert errors[0]["event_type"] == "event3"
    
    @pytest.mark.asyncio
    async def test_filter_events_by_type(self):
        """Test filtering events by type."""
        monitor = SecurityMonitor()
        
        await monitor.log_security_event("login", severity="info")
        await monitor.log_security_event("logout", severity="info")
        await monitor.log_security_event("login", severity="info")
        
        # Get only login events
        logins = await monitor.get_recent_events(event_type="login")
        assert len(logins) == 2
        assert all(e["event_type"] == "login" for e in logins)
    
    @pytest.mark.asyncio
    async def test_get_session_events(self):
        """Test getting events for a specific session."""
        monitor = SecurityMonitor()
        
        await monitor.log_security_event("event1", session_id="session1")
        await monitor.log_security_event("event2", session_id="session2")
        await monitor.log_security_event("event3", session_id="session1")
        
        # Get events for session1
        session1_events = await monitor.get_session_events("session1")
        assert len(session1_events) == 2
        assert all(e["session_id"] == "session1" for e in session1_events)
    
    @pytest.mark.asyncio
    async def test_get_security_stats(self):
        """Test getting security statistics."""
        monitor = SecurityMonitor()
        
        await monitor.log_security_event("event1", severity="info")
        await monitor.log_security_event("event2", severity="warning")
        await monitor.log_security_event("event3", severity="error")
        await monitor.log_security_event("event4", severity="critical")
        await monitor.log_security_event("event5", severity="info")
        
        stats = await monitor.get_security_stats()
        
        assert stats["total_events"] == 5
        assert stats["severity_distribution"]["info"] == 2
        assert stats["severity_distribution"]["warning"] == 1
        assert stats["severity_distribution"]["error"] == 1
        assert stats["severity_distribution"]["critical"] == 1
        assert stats["recent_critical_events"] == 1
    
    @pytest.mark.asyncio
    async def test_event_limit(self):
        """Test that old events are removed when limit is reached."""
        monitor = SecurityMonitor()
        monitor._max_events = 10  # Set low limit for testing
        
        # Log more events than the limit
        for i in range(20):
            await monitor.log_security_event(f"event_{i}")
        
        events = await monitor.get_recent_events(limit=100)
        
        # Should only keep the most recent 10
        assert len(events) == 10
        assert events[0]["event_type"] == "event_10"
        assert events[-1]["event_type"] == "event_19"


class TestSecurityIntegration:
    """Integration tests for security components."""
    
    @pytest.mark.asyncio
    async def test_full_security_workflow(self):
        """Test a complete security workflow."""
        # Generate secure session ID
        session_id = SessionIDGenerator.generate()
        assert SessionIDGenerator.validate(session_id)
        
        # Sanitize user input
        prompt = "Create a login form"
        sanitized_prompt, warnings = InputSanitizer.sanitize_prompt(prompt)
        assert sanitized_prompt is not None
        
        # Check rate limit
        limiter = RateLimiter(max_requests_per_minute=5)
        allowed, reason = await limiter.check_rate_limit(session_id)
        assert allowed is True
        
        # Log security event
        monitor = SecurityMonitor()
        await monitor.log_security_event(
            "session_created",
            session_id=session_id,
            details={"prompt": sanitized_prompt},
            severity="info"
        )
        
        # Verify event was logged
        events = await monitor.get_session_events(session_id)
        assert len(events) == 1
    
    @pytest.mark.asyncio
    async def test_security_under_attack(self):
        """Test security measures under simulated attack."""
        monitor = SecurityMonitor()
        limiter = RateLimiter(max_requests_per_minute=3)
        
        # Simulate rapid requests (attack)
        session_id = SessionIDGenerator.generate()
        blocked_count = 0
        
        for i in range(10):
            allowed, reason = await limiter.check_rate_limit(session_id)
            
            if not allowed:
                blocked_count += 1
                await monitor.log_security_event(
                    "rate_limit_exceeded",
                    session_id=session_id,
                    details={"attempt": i},
                    severity="warning"
                )
        
        # Should have blocked some requests
        assert blocked_count > 0
        
        # Should have logged warnings
        warnings = await monitor.get_recent_events(severity="warning")
        assert len(warnings) == blocked_count
    
    @pytest.mark.asyncio
    async def test_malicious_input_detection(self):
        """Test detection of various malicious inputs."""
        monitor = SecurityMonitor()
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "javascript:alert(1)",
            "<iframe src='evil.com'></iframe>",
        ]
        
        for malicious_input in malicious_inputs:
            try:
                InputSanitizer.sanitize_prompt(malicious_input)
                assert False, "Should have raised SecurityError"
            except SecurityError as e:
                await monitor.log_security_event(
                    "malicious_input_detected",
                    details={"input": malicious_input, "error": str(e)},
                    severity="error"
                )
        
        # Should have logged all malicious attempts
        errors = await monitor.get_recent_events(severity="error")
        assert len(errors) == len(malicious_inputs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
