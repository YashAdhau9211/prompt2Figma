# tests/test_analytics_api.py
"""
Integration tests for analytics API endpoints.
Tests the analytics endpoints for session insights and metrics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import os

# Set required environment variables before importing app
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_STATE_STORE_URL", "redis://localhost:6379/1")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from fastapi.testclient import TestClient
from app.main import app
from app.core.models import (
    SessionMetrics, EditType, SessionMetadata, SessionStatus, DesignSession
)
from app.core.analytics import AnalyticsManager


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_analytics_manager():
    """Create a mock analytics manager."""
    manager = MagicMock(spec=AnalyticsManager)
    
    # Mock calculate_session_metrics
    manager.calculate_session_metrics = AsyncMock(return_value=SessionMetrics(
        total_edits=10,
        session_duration_minutes=60,
        edit_types_distribution={
            EditType.MODIFY: 5,
            EditType.ADD: 3,
            EditType.STYLE: 2
        },
        average_processing_time_ms=1500.0
    ))
    
    # Mock get_daily_analytics
    manager.get_daily_analytics = AsyncMock(return_value={
        "date": "2024-01-15",
        "total_edits": 50,
        "edit_types": {
            "modify": 25,
            "add": 15,
            "style": 10
        },
        "success_count": 48,
        "failure_count": 2,
        "success_rate": 96.0,
        "average_processing_time_ms": 1400.0
    })
    
    # Mock get_edit_type_trends
    manager.get_edit_type_trends = AsyncMock(return_value={
        "modify": [10, 12, 15, 14, 13, 16, 18],
        "add": [5, 6, 7, 6, 5, 7, 8],
        "style": [3, 4, 3, 5, 4, 4, 5]
    })
    
    # Mock get_performance_trends
    manager.get_performance_trends = AsyncMock(return_value={
        "period": {
            "start_date": "2024-01-09",
            "end_date": "2024-01-15",
            "days": 7
        },
        "trends": {
            "dates": ["2024-01-09", "2024-01-10", "2024-01-11", "2024-01-12", "2024-01-13", "2024-01-14", "2024-01-15"],
            "average_processing_times_ms": [1400, 1450, 1380, 1420, 1390, 1410, 1400],
            "success_rates": [95.0, 96.0, 94.5, 97.0, 95.5, 96.5, 96.0],
            "total_edits": [45, 48, 42, 50, 46, 49, 50]
        },
        "overall": {
            "average_processing_time_ms": 1407.14,
            "average_success_rate": 95.79,
            "total_edits": 330
        }
    })
    
    # Mock get_user_engagement_metrics
    manager.get_user_engagement_metrics = AsyncMock(return_value={
        "user_id": "user-123",
        "total_sessions": 5,
        "total_edits": 50,
        "average_edits_per_session": 10.0,
        "total_session_duration_minutes": 300.0,
        "average_session_duration_minutes": 60.0
    })
    
    # Mock get_most_common_edit_types
    manager.get_most_common_edit_types = AsyncMock(return_value=[
        {"edit_type": "modify", "count": 25},
        {"edit_type": "add", "count": 15},
        {"edit_type": "style", "count": 10}
    ])
    
    return manager


@pytest.fixture
def mock_session_manager():
    """Create a mock session manager."""
    manager = MagicMock()
    
    # Mock get_session
    manager.get_session = AsyncMock(return_value=DesignSession(
        session_id="test-session-123",
        user_id="user-123",
        initial_prompt="Create a login form",
        current_version=5,
        status=SessionStatus.ACTIVE
    ))
    
    return manager


class TestSessionAnalyticsEndpoint:
    """Tests for session analytics endpoint."""
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    @patch("app.api.v1.iterative_design.get_session_manager")
    def test_get_session_analytics_success(
        self, mock_get_session_mgr, mock_get_analytics_mgr, 
        client, mock_analytics_manager, mock_session_manager
    ):
        """Test successful retrieval of session analytics."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        mock_get_session_mgr.return_value = mock_session_manager
        
        response = client.get("/design-sessions/analytics/session/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session_id"] == "test-session-123"
        assert "metrics" in data
        assert data["metrics"]["total_edits"] == 10
        assert data["metrics"]["session_duration_minutes"] == 60
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    @patch("app.api.v1.iterative_design.get_session_manager")
    def test_get_session_analytics_not_found(
        self, mock_get_session_mgr, mock_get_analytics_mgr, client
    ):
        """Test session analytics for non-existent session."""
        mock_session_mgr = MagicMock()
        mock_session_mgr.get_session = AsyncMock(return_value=None)
        mock_get_session_mgr.return_value = mock_session_mgr
        
        response = client.get("/design-sessions/analytics/session/nonexistent")
        
        assert response.status_code == 404


class TestDailyAnalyticsEndpoint:
    """Tests for daily analytics endpoint."""
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_daily_analytics_success(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test successful retrieval of daily analytics."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/daily")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "analytics" in data
        assert data["analytics"]["total_edits"] == 50
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_daily_analytics_with_date(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test daily analytics with specific date."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/daily?date=2024-01-15")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_daily_analytics_invalid_date(
        self, mock_get_analytics_mgr, client
    ):
        """Test daily analytics with invalid date format."""
        response = client.get("/design-sessions/analytics/daily?date=invalid-date")
        
        assert response.status_code == 400


class TestAnalyticsTrendsEndpoint:
    """Tests for analytics trends endpoint."""
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_analytics_trends_success(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test successful retrieval of analytics trends."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/trends")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "edit_type_trends" in data
        assert "performance_trends" in data
        assert data["period_days"] == 7
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_analytics_trends_custom_days(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test analytics trends with custom number of days."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/trends?days=14")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_analytics_trends_invalid_days(
        self, mock_get_analytics_mgr, client
    ):
        """Test analytics trends with invalid days parameter."""
        response = client.get("/design-sessions/analytics/trends?days=100")
        
        assert response.status_code == 400


class TestUserAnalyticsEndpoint:
    """Tests for user analytics endpoint."""
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_user_analytics_success(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test successful retrieval of user analytics."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/user/user-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user_id"] == "user-123"
        assert "engagement_metrics" in data
        assert data["engagement_metrics"]["total_sessions"] == 5


class TestPopularEditTypesEndpoint:
    """Tests for popular edit types endpoint."""
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_popular_edit_types_success(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test successful retrieval of popular edit types."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/edit-types/popular")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "popular_edit_types" in data
        assert len(data["popular_edit_types"]) == 3
        assert data["popular_edit_types"][0]["edit_type"] == "modify"
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_popular_edit_types_custom_limit(
        self, mock_get_analytics_mgr, client, mock_analytics_manager
    ):
        """Test popular edit types with custom limit."""
        mock_get_analytics_mgr.return_value = mock_analytics_manager
        
        response = client.get("/design-sessions/analytics/edit-types/popular?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @patch("app.api.v1.iterative_design.get_analytics_manager")
    def test_get_popular_edit_types_invalid_limit(
        self, mock_get_analytics_mgr, client
    ):
        """Test popular edit types with invalid limit."""
        response = client.get("/design-sessions/analytics/edit-types/popular?limit=100")
        
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
