# tests/test_analytics.py
"""
Unit tests for analytics and metrics tracking functionality.
Tests session metrics calculation, edit type tracking, and performance analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.core.analytics import AnalyticsManager
from app.core.models import (
    EditType, SessionMetrics, SessionMetadata, SessionStatus
)
from app.core.state_store import RedisStateStore


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = AsyncMock()
    redis_mock.hincrby = AsyncMock(return_value=1)
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.ltrim = AsyncMock(return_value=True)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.hgetall = AsyncMock(return_value={})
    redis_mock.lrange = AsyncMock(return_value=[])
    redis_mock.hset = AsyncMock(return_value=True)
    return redis_mock


@pytest.fixture
def mock_state_store(mock_redis):
    """Create a mock state store with Redis client."""
    store = MagicMock(spec=RedisStateStore)
    store.redis = mock_redis
    store.get_session_metadata = AsyncMock()
    store.get_user_sessions = AsyncMock(return_value=[])
    return store


@pytest.fixture
def analytics_manager(mock_state_store):
    """Create an analytics manager instance with mocked dependencies."""
    return AnalyticsManager(mock_state_store)


class TestEditTracking:
    """Tests for edit tracking functionality."""
    
    @pytest.mark.asyncio
    async def test_track_edit_success(self, analytics_manager, mock_redis):
        """Test successful edit tracking."""
        session_id = "test-session-123"
        edit_type = EditType.MODIFY
        processing_time = 1500
        
        result = await analytics_manager.track_edit(
            session_id, edit_type, processing_time, success=True
        )
        
        assert result is True
        
        # Verify Redis calls
        assert mock_redis.hincrby.called
        assert mock_redis.lpush.called
        assert mock_redis.ltrim.called
        assert mock_redis.expire.called
    
    @pytest.mark.asyncio
    async def test_track_edit_failure(self, analytics_manager, mock_redis):
        """Test tracking a failed edit."""
        session_id = "test-session-123"
        edit_type = EditType.ADD
        processing_time = 2000
        
        result = await analytics_manager.track_edit(
            session_id, edit_type, processing_time, success=False
        )
        
        assert result is True
        
        # Verify failure status was tracked
        calls = [call for call in mock_redis.hincrby.call_args_list]
        failure_tracked = any(
            "status:failure" in str(call) for call in calls
        )
        assert failure_tracked
    
    @pytest.mark.asyncio
    async def test_track_edit_different_types(self, analytics_manager, mock_redis):
        """Test tracking different edit types."""
        session_id = "test-session-123"
        
        for edit_type in EditType:
            result = await analytics_manager.track_edit(
                session_id, edit_type, 1000, success=True
            )
            assert result is True
    
    @pytest.mark.asyncio
    async def test_track_edit_redis_error(self, analytics_manager, mock_redis):
        """Test handling Redis errors during edit tracking."""
        mock_redis.hincrby.side_effect = Exception("Redis connection error")
        
        session_id = "test-session-123"
        result = await analytics_manager.track_edit(
            session_id, EditType.MODIFY, 1000
        )
        
        # Should return False but not raise exception
        assert result is False


class TestSessionMetricsCalculation:
    """Tests for session metrics calculation."""
    
    @pytest.mark.asyncio
    async def test_calculate_session_metrics_success(
        self, analytics_manager, mock_state_store, mock_redis
    ):
        """Test successful session metrics calculation."""
        session_id = "test-session-123"
        
        # Mock session metadata
        created_at = datetime.utcnow() - timedelta(hours=2)
        last_activity = datetime.utcnow()
        
        mock_state_store.get_session_metadata.return_value = SessionMetadata(
            session_id=session_id,
            user_id="user-123",
            initial_prompt="Create a login form",
            current_version=5,
            created_at=created_at,
            last_activity=last_activity,
            status=SessionStatus.ACTIVE,
            total_edits=10
        )
        
        # Mock analytics data
        mock_redis.hgetall.return_value = {
            "edit_type:modify": "5",
            "edit_type:add": "3",
            "edit_type:style": "2"
        }
        
        # Mock processing times
        mock_redis.lrange.return_value = ["1500", "1200", "1800", "1400", "1600"]
        
        metrics = await analytics_manager.calculate_session_metrics(session_id)
        
        assert metrics is not None
        assert metrics.total_edits == 10
        assert metrics.session_duration_minutes == 120  # 2 hours
        assert EditType.MODIFY in metrics.edit_types_distribution
        assert metrics.edit_types_distribution[EditType.MODIFY] == 5
        assert metrics.average_processing_time_ms == 1500.0
    
    @pytest.mark.asyncio
    async def test_calculate_metrics_no_session(
        self, analytics_manager, mock_state_store
    ):
        """Test metrics calculation when session doesn't exist."""
        mock_state_store.get_session_metadata.return_value = None
        
        metrics = await analytics_manager.calculate_session_metrics("nonexistent")
        
        assert metrics is None
    
    @pytest.mark.asyncio
    async def test_calculate_metrics_no_edits(
        self, analytics_manager, mock_state_store, mock_redis
    ):
        """Test metrics calculation for session with no edits."""
        session_id = "test-session-123"
        
        mock_state_store.get_session_metadata.return_value = SessionMetadata(
            session_id=session_id,
            user_id="user-123",
            initial_prompt="Test",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=0
        )
        
        mock_redis.hgetall.return_value = {}
        mock_redis.lrange.return_value = []
        
        metrics = await analytics_manager.calculate_session_metrics(session_id)
        
        assert metrics is not None
        assert metrics.total_edits == 0
        assert metrics.average_processing_time_ms == 0.0
        assert len(metrics.edit_types_distribution) == 0
    
    @pytest.mark.asyncio
    async def test_calculate_metrics_stores_results(
        self, analytics_manager, mock_state_store, mock_redis
    ):
        """Test that calculated metrics are stored in Redis."""
        session_id = "test-session-123"
        
        mock_state_store.get_session_metadata.return_value = SessionMetadata(
            session_id=session_id,
            user_id="user-123",
            initial_prompt="Test",
            current_version=2,
            created_at=datetime.utcnow() - timedelta(minutes=30),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=5
        )
        
        mock_redis.hgetall.return_value = {"edit_type:modify": "5"}
        mock_redis.lrange.return_value = ["1000", "1200", "1100"]
        
        metrics = await analytics_manager.calculate_session_metrics(session_id)
        
        assert metrics is not None
        # Verify metrics were stored
        assert mock_redis.hset.called


class TestDailyAnalytics:
    """Tests for daily analytics functionality."""
    
    @pytest.mark.asyncio
    async def test_get_daily_analytics_with_data(
        self, analytics_manager, mock_redis
    ):
        """Test getting daily analytics with data."""
        test_date = datetime(2024, 1, 15)
        
        # Mock analytics data
        mock_redis.hgetall.return_value = {
            "edit_type:modify": "10",
            "edit_type:add": "5",
            "edit_type:style": "3",
            "status:success": "16",
            "status:failure": "2"
        }
        
        mock_redis.lrange.return_value = ["1500", "1200", "1800"]
        
        analytics = await analytics_manager.get_daily_analytics(test_date)
        
        assert analytics["date"] == "2024-01-15"
        assert analytics["total_edits"] == 18
        assert analytics["edit_types"]["modify"] == 10
        assert analytics["success_count"] == 16
        assert analytics["failure_count"] == 2
        assert analytics["success_rate"] == 88.89  # 16/18 * 100
        assert analytics["average_processing_time_ms"] == 1500.0
    
    @pytest.mark.asyncio
    async def test_get_daily_analytics_no_data(
        self, analytics_manager, mock_redis
    ):
        """Test getting daily analytics with no data."""
        test_date = datetime(2024, 1, 15)
        mock_redis.hgetall.return_value = {}
        mock_redis.lrange.return_value = []
        
        analytics = await analytics_manager.get_daily_analytics(test_date)
        
        assert analytics["date"] == "2024-01-15"
        assert analytics["total_edits"] == 0
        assert analytics["success_rate"] == 0.0
        assert analytics["average_processing_time_ms"] == 0.0
    
    @pytest.mark.asyncio
    async def test_get_daily_analytics_default_date(
        self, analytics_manager, mock_redis
    ):
        """Test getting daily analytics with default date (today)."""
        mock_redis.hgetall.return_value = {}
        mock_redis.lrange.return_value = []
        
        analytics = await analytics_manager.get_daily_analytics()
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        assert analytics["date"] == today


class TestDateRangeAnalytics:
    """Tests for date range analytics."""
    
    @pytest.mark.asyncio
    async def test_get_date_range_analytics(
        self, analytics_manager, mock_redis
    ):
        """Test getting analytics for a date range."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 3)
        
        mock_redis.hgetall.return_value = {"edit_type:modify": "5"}
        mock_redis.lrange.return_value = ["1000"]
        
        analytics_list = await analytics_manager.get_date_range_analytics(
            start_date, end_date
        )
        
        assert len(analytics_list) == 3  # 3 days inclusive
        assert analytics_list[0]["date"] == "2024-01-01"
        assert analytics_list[1]["date"] == "2024-01-02"
        assert analytics_list[2]["date"] == "2024-01-03"
    
    @pytest.mark.asyncio
    async def test_get_date_range_single_day(
        self, analytics_manager, mock_redis
    ):
        """Test getting analytics for a single day range."""
        date = datetime(2024, 1, 15)
        
        mock_redis.hgetall.return_value = {}
        mock_redis.lrange.return_value = []
        
        analytics_list = await analytics_manager.get_date_range_analytics(date, date)
        
        assert len(analytics_list) == 1
        assert analytics_list[0]["date"] == "2024-01-15"


class TestEditTypeTrends:
    """Tests for edit type trends analysis."""
    
    @pytest.mark.asyncio
    async def test_get_edit_type_trends(self, analytics_manager, mock_redis):
        """Test getting edit type trends over multiple days."""
        # Mock different data for each day
        call_count = [0]
        
        def mock_hgetall(key):
            call_count[0] += 1
            if call_count[0] % 2 == 0:
                return {
                    "edit_type:modify": "5",
                    "edit_type:add": "3"
                }
            return {
                "edit_type:modify": "7",
                "edit_type:style": "2"
            }
        
        mock_redis.hgetall.side_effect = mock_hgetall
        mock_redis.lrange.return_value = ["1000"]
        
        trends = await analytics_manager.get_edit_type_trends(days=3)
        
        assert "modify" in trends
        assert "add" in trends
        assert "style" in trends
        assert len(trends["modify"]) == 3  # 3 days of data
    
    @pytest.mark.asyncio
    async def test_get_edit_type_trends_default_days(
        self, analytics_manager, mock_redis
    ):
        """Test getting edit type trends with default 7 days."""
        mock_redis.hgetall.return_value = {"edit_type:modify": "5"}
        mock_redis.lrange.return_value = ["1000"]
        
        trends = await analytics_manager.get_edit_type_trends()
        
        # Should have 7 days of data for each edit type
        for edit_type in EditType:
            assert edit_type.value in trends
            assert len(trends[edit_type.value]) == 7


class TestUserEngagementMetrics:
    """Tests for user engagement metrics."""
    
    @pytest.mark.asyncio
    async def test_get_user_engagement_metrics(
        self, analytics_manager, mock_state_store
    ):
        """Test getting user engagement metrics."""
        user_id = "user-123"
        
        # Mock user sessions
        mock_state_store.get_user_sessions.return_value = [
            "session-1", "session-2", "session-3"
        ]
        
        # Mock session metadata for each session
        async def mock_get_metadata(session_id):
            return SessionMetadata(
                session_id=session_id,
                user_id=user_id,
                initial_prompt="Test",
                current_version=5,
                created_at=datetime.utcnow() - timedelta(hours=1),
                last_activity=datetime.utcnow(),
                status=SessionStatus.ACTIVE,
                total_edits=10
            )
        
        mock_state_store.get_session_metadata.side_effect = mock_get_metadata
        
        metrics = await analytics_manager.get_user_engagement_metrics(user_id)
        
        assert metrics["user_id"] == user_id
        assert metrics["total_sessions"] == 3
        assert metrics["total_edits"] == 30  # 10 edits per session * 3
        assert metrics["average_edits_per_session"] == 10.0
        assert metrics["total_session_duration_minutes"] == 180.0  # 60 min * 3
    
    @pytest.mark.asyncio
    async def test_get_user_engagement_no_sessions(
        self, analytics_manager, mock_state_store
    ):
        """Test getting user engagement metrics with no sessions."""
        user_id = "user-123"
        mock_state_store.get_user_sessions.return_value = []
        
        metrics = await analytics_manager.get_user_engagement_metrics(user_id)
        
        assert metrics["user_id"] == user_id
        assert metrics["total_sessions"] == 0
        assert metrics["total_edits"] == 0
        assert metrics["average_edits_per_session"] == 0.0


class TestMostCommonEditTypes:
    """Tests for most common edit types analysis."""
    
    @pytest.mark.asyncio
    async def test_get_most_common_edit_types(
        self, analytics_manager, mock_redis
    ):
        """Test getting most common edit types."""
        mock_redis.hgetall.return_value = {
            "edit_type:modify": "50",
            "edit_type:add": "30",
            "edit_type:style": "20",
            "edit_type:remove": "10",
            "edit_type:layout": "5"
        }
        mock_redis.lrange.return_value = ["1000"]
        
        common_types = await analytics_manager.get_most_common_edit_types(limit=3)
        
        assert len(common_types) == 3
        assert common_types[0]["edit_type"] == "modify"
        assert common_types[0]["count"] == 50
        assert common_types[1]["edit_type"] == "add"
        assert common_types[1]["count"] == 30
        assert common_types[2]["edit_type"] == "style"
        assert common_types[2]["count"] == 20
    
    @pytest.mark.asyncio
    async def test_get_most_common_edit_types_no_data(
        self, analytics_manager, mock_redis
    ):
        """Test getting most common edit types with no data."""
        mock_redis.hgetall.return_value = {}
        mock_redis.lrange.return_value = []
        
        common_types = await analytics_manager.get_most_common_edit_types()
        
        assert len(common_types) == 0


class TestPerformanceTrends:
    """Tests for performance trends analysis."""
    
    @pytest.mark.asyncio
    async def test_get_performance_trends(self, analytics_manager, mock_redis):
        """Test getting performance trends over multiple days."""
        # Mock varying data for each day
        call_count = [0]
        
        def mock_hgetall(key):
            call_count[0] += 1
            return {
                "edit_type:modify": str(call_count[0] * 5),
                "status:success": str(call_count[0] * 4),
                "status:failure": "1"
            }
        
        def mock_lrange(key, start, end):
            return [str(1000 + call_count[0] * 100)]
        
        mock_redis.hgetall.side_effect = mock_hgetall
        mock_redis.lrange.side_effect = mock_lrange
        
        trends = await analytics_manager.get_performance_trends(days=3)
        
        assert "period" in trends
        assert trends["period"]["days"] == 3
        assert "trends" in trends
        assert len(trends["trends"]["dates"]) == 3
        assert len(trends["trends"]["average_processing_times_ms"]) == 3
        assert len(trends["trends"]["success_rates"]) == 3
        assert "overall" in trends
        assert "average_processing_time_ms" in trends["overall"]
        assert "average_success_rate" in trends["overall"]
    
    @pytest.mark.asyncio
    async def test_get_performance_trends_default_days(
        self, analytics_manager, mock_redis
    ):
        """Test getting performance trends with default 7 days."""
        mock_redis.hgetall.return_value = {"edit_type:modify": "5"}
        mock_redis.lrange.return_value = ["1000"]
        
        trends = await analytics_manager.get_performance_trends()
        
        assert trends["period"]["days"] == 7
        assert len(trends["trends"]["dates"]) == 7


class TestAnalyticsIntegration:
    """Integration tests for analytics functionality."""
    
    @pytest.mark.asyncio
    async def test_full_analytics_workflow(
        self, analytics_manager, mock_state_store, mock_redis
    ):
        """Test complete analytics workflow from tracking to retrieval."""
        session_id = "test-session-123"
        
        # Track multiple edits
        await analytics_manager.track_edit(
            session_id, EditType.MODIFY, 1500, success=True
        )
        await analytics_manager.track_edit(
            session_id, EditType.ADD, 1200, success=True
        )
        await analytics_manager.track_edit(
            session_id, EditType.STYLE, 1800, success=False
        )
        
        # Mock session metadata for metrics calculation
        mock_state_store.get_session_metadata.return_value = SessionMetadata(
            session_id=session_id,
            user_id="user-123",
            initial_prompt="Test",
            current_version=3,
            created_at=datetime.utcnow() - timedelta(hours=1),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
            total_edits=3
        )
        
        mock_redis.hgetall.return_value = {
            "edit_type:modify": "1",
            "edit_type:add": "1",
            "edit_type:style": "1"
        }
        mock_redis.lrange.return_value = ["1500", "1200", "1800"]
        
        # Calculate metrics
        metrics = await analytics_manager.calculate_session_metrics(session_id)
        
        assert metrics is not None
        assert metrics.total_edits == 3
        assert metrics.average_processing_time_ms == 1500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
