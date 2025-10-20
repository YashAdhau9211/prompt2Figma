# app/core/analytics.py
"""
Analytics and metrics tracking for the Stateful Iterative Design Engine.
Handles session metrics calculation, edit type tracking, and performance analytics.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.models import EditContext, EditType, SessionMetadata, SessionMetrics
from app.core.state_store import RedisStateStore

logger = logging.getLogger(__name__)


class AnalyticsManager:
    """
    Manages analytics and metrics tracking for design sessions.

    Responsibilities:
    - Session metrics calculation and storage
    - Edit type tracking and distribution analysis
    - Performance analytics and trends
    - User engagement metrics
    """

    def __init__(self, state_store: RedisStateStore):
        self.state_store = state_store

    async def track_edit(
        self,
        session_id: str,
        edit_type: EditType,
        processing_time_ms: int,
        success: bool = True,
    ) -> bool:
        """
        Track an individual edit for analytics.

        Args:
            session_id: The session identifier
            edit_type: Type of edit performed
            processing_time_ms: Time taken to process the edit
            success: Whether the edit was successful

        Returns:
            bool: True if tracking was successful
        """
        try:
            # Get current date for daily metrics
            date_key = datetime.utcnow().strftime("%Y-%m-%d")
            analytics_key = f"analytics:edits:{date_key}"

            # Increment edit count by type
            await self.state_store.redis.hincrby(
                analytics_key, f"edit_type:{edit_type.value}", 1
            )

            # Track success/failure
            status_key = "success" if success else "failure"
            await self.state_store.redis.hincrby(
                analytics_key, f"status:{status_key}", 1
            )

            # Store processing time for average calculation
            await self.state_store.redis.lpush(
                f"{analytics_key}:processing_times", processing_time_ms
            )

            # Trim processing times list to keep last 1000 entries
            await self.state_store.redis.ltrim(
                f"{analytics_key}:processing_times", 0, 999
            )

            # Set expiry for 90 days
            await self.state_store.redis.expire(analytics_key, timedelta(days=90))
            await self.state_store.redis.expire(
                f"{analytics_key}:processing_times", timedelta(days=90)
            )

            # Track session-specific edit
            session_analytics_key = f"session:{session_id}:analytics"
            await self.state_store.redis.hincrby(
                session_analytics_key, f"edit_type:{edit_type.value}", 1
            )
            await self.state_store.redis.lpush(
                f"{session_analytics_key}:processing_times", processing_time_ms
            )
            await self.state_store.redis.ltrim(
                f"{session_analytics_key}:processing_times", 0, 999
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track edit for session {session_id}: {e}")
            return False

    async def calculate_session_metrics(
        self, session_id: str
    ) -> Optional[SessionMetrics]:
        """
        Calculate comprehensive metrics for a session.

        Args:
            session_id: The session identifier

        Returns:
            SessionMetrics or None if calculation fails
        """
        try:
            # Get session metadata
            metadata = await self.state_store.get_session_metadata(session_id)
            if not metadata:
                logger.warning(f"Session metadata not found for {session_id}")
                return None

            # Calculate session duration
            duration_minutes = int(
                (metadata.last_activity - metadata.created_at).total_seconds() / 60
            )

            # Get edit type distribution from session analytics
            session_analytics_key = f"session:{session_id}:analytics"
            analytics_data = await self.state_store.redis.hgetall(session_analytics_key)

            edit_types_distribution = {}
            for key, value in analytics_data.items():
                if key.startswith("edit_type:"):
                    edit_type_str = key.replace("edit_type:", "")
                    try:
                        edit_type = EditType(edit_type_str)
                        edit_types_distribution[edit_type] = int(value)
                    except ValueError:
                        logger.warning(f"Unknown edit type: {edit_type_str}")

            # Calculate average processing time
            processing_times_key = f"{session_analytics_key}:processing_times"
            processing_times_str = await self.state_store.redis.lrange(
                processing_times_key, 0, -1
            )

            processing_times = [int(t) for t in processing_times_str if t]
            avg_processing_time = (
                sum(processing_times) / len(processing_times)
                if processing_times
                else 0.0
            )

            metrics = SessionMetrics(
                total_edits=metadata.total_edits,
                session_duration_minutes=duration_minutes,
                edit_types_distribution=edit_types_distribution,
                average_processing_time_ms=avg_processing_time,
            )

            # Store calculated metrics
            await self._store_session_metrics(session_id, metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate session metrics for {session_id}: {e}")
            return None

    async def _store_session_metrics(
        self, session_id: str, metrics: SessionMetrics
    ) -> bool:
        """Store calculated session metrics in Redis."""
        try:
            metrics_key = f"session:{session_id}:metrics"
            metrics_data = {
                "total_edits": metrics.total_edits,
                "session_duration_minutes": metrics.session_duration_minutes,
                "average_processing_time_ms": metrics.average_processing_time_ms,
                "edit_types_distribution": json.dumps(
                    {k.value: v for k, v in metrics.edit_types_distribution.items()}
                ),
                "calculated_at": datetime.utcnow().isoformat(),
            }

            if metrics.user_satisfaction_score is not None:
                metrics_data["user_satisfaction_score"] = (
                    metrics.user_satisfaction_score
                )

            await self.state_store.redis.hset(metrics_key, mapping=metrics_data)
            await self.state_store.redis.expire(metrics_key, timedelta(days=90))

            return True

        except Exception as e:
            logger.error(f"Failed to store session metrics for {session_id}: {e}")
            return False

    async def get_daily_analytics(
        self, date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a specific date.

        Args:
            date: Date to get analytics for (defaults to today)

        Returns:
            Dictionary with daily analytics data
        """
        try:
            if date is None:
                date = datetime.utcnow()

            date_key = date.strftime("%Y-%m-%d")
            analytics_key = f"analytics:edits:{date_key}"

            # Get all analytics data for the date
            analytics_data = await self.state_store.redis.hgetall(analytics_key)

            if not analytics_data:
                return {
                    "date": date_key,
                    "total_edits": 0,
                    "edit_types": {},
                    "success_rate": 0.0,
                    "average_processing_time_ms": 0.0,
                }

            # Parse edit types
            edit_types = {}
            total_edits = 0
            success_count = 0
            failure_count = 0

            for key, value in analytics_data.items():
                if key.startswith("edit_type:"):
                    edit_type = key.replace("edit_type:", "")
                    count = int(value)
                    edit_types[edit_type] = count
                    total_edits += count
                elif key == "status:success":
                    success_count = int(value)
                elif key == "status:failure":
                    failure_count = int(value)

            # Calculate success rate
            total_attempts = success_count + failure_count
            success_rate = (
                (success_count / total_attempts * 100) if total_attempts > 0 else 0.0
            )

            # Get average processing time
            processing_times_key = f"{analytics_key}:processing_times"
            processing_times_str = await self.state_store.redis.lrange(
                processing_times_key, 0, -1
            )

            processing_times = [int(t) for t in processing_times_str if t]
            avg_processing_time = (
                sum(processing_times) / len(processing_times)
                if processing_times
                else 0.0
            )

            return {
                "date": date_key,
                "total_edits": total_edits,
                "edit_types": edit_types,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": round(success_rate, 2),
                "average_processing_time_ms": round(avg_processing_time, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get daily analytics for {date}: {e}")
            return {
                "date": date.strftime("%Y-%m-%d") if date else "unknown",
                "error": str(e),
            }

    async def get_date_range_analytics(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get analytics for a date range.

        Args:
            start_date: Start of the date range
            end_date: End of the date range

        Returns:
            List of daily analytics for the date range
        """
        try:
            analytics_list = []
            current_date = start_date

            while current_date <= end_date:
                daily_analytics = await self.get_daily_analytics(current_date)
                analytics_list.append(daily_analytics)
                current_date += timedelta(days=1)

            return analytics_list

        except Exception as e:
            logger.error(f"Failed to get date range analytics: {e}")
            return []

    async def get_edit_type_trends(self, days: int = 7) -> Dict[str, List[int]]:
        """
        Get edit type trends over the specified number of days.

        Args:
            days: Number of days to analyze (default: 7)

        Returns:
            Dictionary mapping edit types to daily counts
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days - 1)

            # Get analytics for date range
            analytics_list = await self.get_date_range_analytics(start_date, end_date)

            # Aggregate edit types
            trends = defaultdict(list)

            for daily_data in analytics_list:
                edit_types = daily_data.get("edit_types", {})

                # Ensure all edit types are represented
                for edit_type in EditType:
                    count = edit_types.get(edit_type.value, 0)
                    trends[edit_type.value].append(count)

            return dict(trends)

        except Exception as e:
            logger.error(f"Failed to get edit type trends: {e}")
            return {}

    async def get_user_engagement_metrics(self, user_id: str) -> Dict[str, Any]:
        """
        Get engagement metrics for a specific user.

        Args:
            user_id: The user identifier

        Returns:
            Dictionary with user engagement metrics
        """
        try:
            # Get all user sessions
            session_ids = await self.state_store.get_user_sessions(user_id)

            if not session_ids:
                return {
                    "user_id": user_id,
                    "total_sessions": 0,
                    "total_edits": 0,
                    "average_edits_per_session": 0.0,
                    "total_session_duration_minutes": 0,
                    "average_session_duration_minutes": 0.0,
                }

            total_edits = 0
            total_duration = 0
            active_sessions = 0

            for session_id in session_ids:
                metadata = await self.state_store.get_session_metadata(session_id)
                if metadata:
                    total_edits += metadata.total_edits
                    duration = (
                        metadata.last_activity - metadata.created_at
                    ).total_seconds() / 60
                    total_duration += duration
                    active_sessions += 1

            avg_edits_per_session = (
                total_edits / active_sessions if active_sessions > 0 else 0.0
            )

            avg_duration = (
                total_duration / active_sessions if active_sessions > 0 else 0.0
            )

            return {
                "user_id": user_id,
                "total_sessions": active_sessions,
                "total_edits": total_edits,
                "average_edits_per_session": round(avg_edits_per_session, 2),
                "total_session_duration_minutes": round(total_duration, 2),
                "average_session_duration_minutes": round(avg_duration, 2),
            }

        except Exception as e:
            logger.error(f"Failed to get user engagement metrics for {user_id}: {e}")
            return {"user_id": user_id, "error": str(e)}

    async def get_most_common_edit_types(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most common edit types across all sessions.

        Args:
            limit: Maximum number of edit types to return

        Returns:
            List of edit types with their counts, sorted by frequency
        """
        try:
            # Get today's analytics
            today_analytics = await self.get_daily_analytics()
            edit_types = today_analytics.get("edit_types", {})

            # Sort by count
            sorted_types = sorted(edit_types.items(), key=lambda x: x[1], reverse=True)

            return [
                {"edit_type": edit_type, "count": count}
                for edit_type, count in sorted_types[:limit]
            ]

        except Exception as e:
            logger.error(f"Failed to get most common edit types: {e}")
            return []

    async def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get performance trends over the specified number of days.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with performance trend data
        """
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days - 1)

            analytics_list = await self.get_date_range_analytics(start_date, end_date)

            dates = []
            avg_processing_times = []
            success_rates = []
            total_edits = []

            for daily_data in analytics_list:
                dates.append(daily_data["date"])
                avg_processing_times.append(
                    daily_data.get("average_processing_time_ms", 0)
                )
                success_rates.append(daily_data.get("success_rate", 0))
                total_edits.append(daily_data.get("total_edits", 0))

            # Calculate overall statistics
            overall_avg_time = (
                sum(avg_processing_times) / len(avg_processing_times)
                if avg_processing_times
                else 0.0
            )

            overall_success_rate = (
                sum(success_rates) / len(success_rates) if success_rates else 0.0
            )

            return {
                "period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "days": days,
                },
                "trends": {
                    "dates": dates,
                    "average_processing_times_ms": avg_processing_times,
                    "success_rates": success_rates,
                    "total_edits": total_edits,
                },
                "overall": {
                    "average_processing_time_ms": round(overall_avg_time, 2),
                    "average_success_rate": round(overall_success_rate, 2),
                    "total_edits": sum(total_edits),
                },
            }

        except Exception as e:
            logger.error(f"Failed to get performance trends: {e}")
            return {"error": str(e)}
