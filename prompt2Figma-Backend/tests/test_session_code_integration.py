# tests/test_session_code_integration.py
"""
Integration tests for session-to-code generation workflow.
Tests the integration between iterative design sessions and code generation pipeline.

Requirements: 5.2, 5.3
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.core.models import (
    DesignSession, DesignState, SessionStatus, EditType, EditContext
)
from app.core.state_store import RedisStateStore
from app.core.session_manager import DesignSessionManager
from app.api.v1.schemas import GenerateCodeRequest, GenerateCodeResponse


@pytest.fixture
def sample_wireframe():
    """Sample wireframe JSON for testing."""
    return {
        "componentName": "TestApp",
        "type": "Frame",
      