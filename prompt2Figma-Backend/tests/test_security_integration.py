# tests/test_security_integration.py
"""
Integration tests for security features in the iterative design system.
Tests the complete security workflow including session ID validation, rate limiting, and input sanitization.
"""

import pytest
import asyncio
from datetime import datetime

from app.core.security import (
    SessionIDGenerator, RateLimiter, InputSanitizer,
    SecurityMonitor, SecurityError, get_rate_limiter, get_security_monitor
)


class TestSessionIDSecurity:
    """Test session ID security features."""
    
    def test_session_id_generation_security(self):
        """Test that session IDs are cryptographically secure."""
        # Generate multiple session IDs
        session_ids = [SessionIDGenerator.generate() for _ in range(100)]
        
        # All should be unique
        assert len(set(session_ids)) == 100
        
        # All should be valid format
        assert all(SessionIDGenerator.validate(sid) for sid in session_ids)
        
        # All should be 32 characters
        assert all(len(sid) == 32 for sid in session_ids)
        
        # All should be hexadecimal
        assert all(all(c in '0123456789abcdef' for c in sid) for sid in session_ids)
    
    def test_session_id_validation_security(self):
        """Test that session ID validation is strict."""
        # Valid session ID
        valid_id = SessionIDGenerator.generate()
        assert SessionIDGenerator.validate(valid_id) is True
        
        # Invalid formats
        assert SessionIDGenerator.validate("") is False
        assert SessionIDGenerator.validate(None) is False
        assert SessionIDGenerator.validate("short") is False
        assert SessionIDGenerator.validate("g" * 32) is False
        assert SessionIDGenerator.validate(12345) is False


class TestCompleteSecurityWorkflow:
    """Test complete security workflow integration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_workflow(self):
        """Test a complete end-to-end security workflow."""
        # Step 1: Generate secure session ID
        session_id = SessionIDGenerator.generate()
        assert SessionIDGenerator.validate(session_id)
        
        # Step 2: Sanitize user input
        user_prompt = "Create a login form with email and password"
        sanitized_prompt, warnings = InputSanitizer.sanitize_prompt(user_prompt)
        assert sanitized_prompt is not None
        assert len(warnings) == 0
        
        # Step 3: Check rate limits
        limiter = RateLimiter(max_requests_per_minute=10)
        allowed, reason = await limiter.check_rate_limit(session_id)
        assert allowed is True
        
        # Step 4: Log security event
        monitor = SecurityMonitor()
        await monitor.log_security_event(
            "session_created",
            session_id=session_id,
            details={"prompt": sanitized_prompt},
            severity="info"
        )
        
        # Step 5: Verify event was logged
        events = await monitor.get_session_events(session_id)
        assert len(events) == 1
        assert events[0]["event_type"] == "session_created"
        
        # Step 6: Simulate multiple edits
        for i in range(5):
            edit_prompt = f"Edit {i}: Add a button"
            sanitized_edit, _ = InputSanitizer.sanitize_prompt(edit_prompt)
            
            allowed, _ = await limiter.check_rate_limit(session_id)
            if allowed:
                await monitor.log_security_event(
                    "edit_applied",
                    session_id=session_id,
                    details={"edit": sanitized_edit},
                    severity="info"
                )
        
        # Step 7: Verify all events were logged
        all_events = await monitor.get_session_events(session_id)
        assert len(all_events) >= 1
        
        # Step 8: Get rate limit stats
        stats = limiter.get_session_stats(session_id)
        assert stats["requests_last_minute"] > 0
    
    @pytest.mark.asyncio
    async def test_security_under_attack(self):
        """Test security measures under simulated attack."""
        monitor = SecurityMonitor()
        limiter = RateLimiter(max_requests_per_minute=3)
        
        # Simulate rapid requests (attack)
        session_id = SessionIDGenerator.generate()
        blocked_count = 0
        allowed_count = 0
        
        for i in range(10):
            allowed, reason = await limiter.check_rate_limit(session_id)
            
            if not allowed:
                blocked_count += 1
                await monitor.log_security_event(
                    "rate_limit_exceeded",
                    session_id=session_id,
                    details={"attempt": i, "reason": reason},
                    severity="warning"
                )
            else:
                allowed_count += 1
        
        # Should have blocked some requests
        assert blocked_count > 0
        assert allowed_count == 3  # Only first 3 should be allowed
        
        # Should have logged warnings
        warnings = await monitor.get_recent_events(severity="warning")
        assert len(warnings) == blocked_count
    
    @pytest.mark.asyncio
    async def test_malicious_input_detection_workflow(self):
        """Test detection and logging of malicious inputs."""
        monitor = SecurityMonitor()
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "javascript:alert(1)",
            "<iframe src='evil.com'></iframe>",
        ]
        
        detected_count = 0
        for malicious_input in malicious_inputs:
            try:
                InputSanitizer.sanitize_prompt(malicious_input)
                # Should not reach here
                assert False, "Should have raised SecurityError"
            except SecurityError as e:
                detected_count += 1
                await monitor.log_security_event(
                    "malicious_input_detected",
                    details={"input": malicious_input[:50], "error": str(e)},
                    severity="error"
                )
        
        # Should have detected all malicious attempts
        assert detected_count == len(malicious_inputs)
        
        # Should have logged all errors
        errors = await monitor.get_recent_events(severity="error")
        assert len(errors) == len(malicious_inputs)
    
    @pytest.mark.asyncio
    async def test_concurrent_session_security(self):
        """Test security measures with concurrent sessions."""
        limiter = RateLimiter(max_requests_per_minute=5)
        monitor = SecurityMonitor()
        
        # Create multiple sessions
        sessions = [SessionIDGenerator.generate() for _ in range(5)]
        
        # Each session should have independent rate limits
        for session_id in sessions:
            for i in range(5):
                allowed, _ = await limiter.check_rate_limit(session_id)
                assert allowed is True
                
                await monitor.log_security_event(
                    "request",
                    session_id=session_id,
                    details={"request_num": i},
                    severity="info"
                )
        
        # Verify each session has its own events
        for session_id in sessions:
            events = await monitor.get_session_events(session_id)
            assert len(events) == 5
    
    @pytest.mark.asyncio
    async def test_security_recovery_after_reset(self):
        """Test that security measures can be reset and recovered."""
        limiter = RateLimiter(max_requests_per_minute=2)
        session_id = SessionIDGenerator.generate()
        
        # Use up the limit
        for i in range(2):
            allowed, _ = await limiter.check_rate_limit(session_id)
            assert allowed is True
        
        # Should be blocked
        allowed, _ = await limiter.check_rate_limit(session_id)
        assert allowed is False
        
        # Reset limits
        await limiter.reset_session_limits(session_id)
        
        # Should be allowed again
        allowed, _ = await limiter.check_rate_limit(session_id)
        assert allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
