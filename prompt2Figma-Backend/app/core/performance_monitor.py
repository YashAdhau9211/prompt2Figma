# app/core/performance_monitor.py
"""
Performance monitoring and metrics collection for the Stateful Iterative Design Engine.
Tracks processing times, resource usage, and system health metrics.
"""

import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics that can be collected."""
    EDIT_PROCESSING_TIME = "edit_processing_time"
    STATE_RETRIEVAL_TIME = "state_retrieval_time"
    STATE_STORAGE_TIME = "state_storage_time"
    CONTEXT_PROCESSING_TIME = "context_processing_time"
    AI_MODEL_TIME = "ai_model_time"
    SESSION_CREATION_TIME = "session_creation_time"
    VERSION_CREATION_TIME = "version_creation_time"


@dataclass
class PerformanceMetric:
    """Individual performance metric data point."""
    metric_type: MetricType
    value_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    metric_type: MetricType
    count: int
    avg_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    total_ms: float


class PerformanceMonitor:
    """
    Monitors and collects performance metrics for the iterative design system.
    
    Features:
    - Real-time metric collection
    - Statistical aggregation
    - Performance degradation detection
    - Memory-efficient rolling window storage
    """
    
    def __init__(self, window_size: int = 1000, alert_threshold_ms: float = 5000):
        """
        Initialize performance monitor.
        
        Args:
            window_size: Number of recent metrics to keep in memory
            alert_threshold_ms: Threshold for performance alerts (in milliseconds)
        """
        self.window_size = window_size
        self.alert_threshold_ms = alert_threshold_ms
        
        # Rolling window storage for each metric type
        self._metrics: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=window_size)
            for metric_type in MetricType
        }
        
        # Session-specific metrics
        self._session_metrics: Dict[str, List[PerformanceMetric]] = {}
        
        # Performance alerts
        self._alerts: deque = deque(maxlen=100)
        
        # System start time
        self._start_time = datetime.utcnow()
    
    def record_metric(
        self,
        metric_type: MetricType,
        value_ms: float,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric.
        
        Args:
            metric_type: Type of metric being recorded
            value_ms: Metric value in milliseconds
            session_id: Optional session identifier
            metadata: Optional additional metadata
        """
        metric = PerformanceMetric(
            metric_type=metric_type,
            value_ms=value_ms,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # Add to rolling window
        self._metrics[metric_type].append(metric)
        
        # Add to session-specific metrics if session_id provided
        if session_id:
            if session_id not in self._session_metrics:
                self._session_metrics[session_id] = []
            self._session_metrics[session_id].append(metric)
        
        # Check for performance alerts
        if value_ms > self.alert_threshold_ms:
            self._create_alert(metric)
        
        # Log slow operations
        if value_ms > self.alert_threshold_ms:
            logger.warning(
                f"Slow operation detected: {metric_type.value} took {value_ms:.2f}ms "
                f"(threshold: {self.alert_threshold_ms}ms)"
            )
    
    def get_stats(self, metric_type: MetricType) -> Optional[PerformanceStats]:
        """
        Get aggregated statistics for a metric type.
        
        Args:
            metric_type: Type of metric to get stats for
            
        Returns:
            PerformanceStats or None if no data available
        """
        metrics = list(self._metrics[metric_type])
        if not metrics:
            return None
        
        values = [m.value_ms for m in metrics]
        values_sorted = sorted(values)
        count = len(values)
        
        return PerformanceStats(
            metric_type=metric_type,
            count=count,
            avg_ms=sum(values) / count,
            min_ms=min(values),
            max_ms=max(values),
            p50_ms=self._percentile(values_sorted, 50),
            p95_ms=self._percentile(values_sorted, 95),
            p99_ms=self._percentile(values_sorted, 99),
            total_ms=sum(values)
        )
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Get statistics for all metric types."""
        stats = {}
        for metric_type in MetricType:
            metric_stats = self.get_stats(metric_type)
            if metric_stats:
                stats[metric_type.value] = metric_stats
        return stats
    
    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get performance statistics for a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with session performance metrics
        """
        if session_id not in self._session_metrics:
            return {}
        
        metrics = self._session_metrics[session_id]
        if not metrics:
            return {}
        
        # Group by metric type
        by_type: Dict[MetricType, List[float]] = {}
        for metric in metrics:
            if metric.metric_type not in by_type:
                by_type[metric.metric_type] = []
            by_type[metric.metric_type].append(metric.value_ms)
        
        # Calculate stats for each type
        stats = {
            "session_id": session_id,
            "total_operations": len(metrics),
            "metrics_by_type": {}
        }
        
        for metric_type, values in by_type.items():
            stats["metrics_by_type"][metric_type.value] = {
                "count": len(values),
                "avg_ms": sum(values) / len(values),
                "min_ms": min(values),
                "max_ms": max(values),
                "total_ms": sum(values)
            }
        
        return stats
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall system health status based on performance metrics.
        
        Returns:
            Dictionary with health indicators
        """
        all_stats = self.get_all_stats()
        
        # Check if any metrics exceed thresholds
        degraded = False
        warnings = []
        
        for metric_name, stats in all_stats.items():
            if stats.p95_ms > self.alert_threshold_ms:
                degraded = True
                warnings.append(
                    f"{metric_name} p95 ({stats.p95_ms:.2f}ms) exceeds threshold ({self.alert_threshold_ms}ms)"
                )
        
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        return {
            "healthy": not degraded,
            "uptime_seconds": uptime,
            "total_metrics_collected": sum(len(m) for m in self._metrics.values()),
            "active_sessions": len(self._session_metrics),
            "recent_alerts": len(self._alerts),
            "warnings": warnings,
            "performance_stats": {
                name: {
                    "avg_ms": stats.avg_ms,
                    "p95_ms": stats.p95_ms,
                    "count": stats.count
                }
                for name, stats in all_stats.items()
            }
        }
    
    def clear_session_metrics(self, session_id: str):
        """Clear metrics for a specific session to free memory."""
        if session_id in self._session_metrics:
            del self._session_metrics[session_id]
            logger.debug(f"Cleared metrics for session {session_id}")
    
    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0
        
        index = (percentile / 100) * (len(sorted_values) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = index - lower
        
        return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight
    
    def _create_alert(self, metric: PerformanceMetric):
        """Create a performance alert."""
        alert = {
            "timestamp": metric.timestamp,
            "metric_type": metric.metric_type.value,
            "value_ms": metric.value_ms,
            "threshold_ms": self.alert_threshold_ms,
            "session_id": metric.session_id,
            "metadata": metric.metadata
        }
        self._alerts.append(alert)
        logger.warning(f"Performance alert: {alert}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance alerts."""
        return list(self._alerts)[-limit:]


class PerformanceTimer:
    """Context manager for timing operations and recording metrics."""
    
    def __init__(
        self,
        monitor: PerformanceMonitor,
        metric_type: MetricType,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.monitor = monitor
        self.metric_type = metric_type
        self.session_id = session_id
        self.metadata = metadata or {}
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        # Record the metric
        self.monitor.record_metric(
            self.metric_type,
            duration_ms,
            self.session_id,
            self.metadata
        )
        
        return False  # Don't suppress exceptions
    
    async def __aenter__(self):
        self.start_time = time.perf_counter()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        duration_ms = (self.end_time - self.start_time) * 1000
        
        # Record the metric
        self.monitor.record_metric(
            self.metric_type,
            duration_ms,
            self.session_id,
            self.metadata
        )
        
        return False  # Don't suppress exceptions


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def reset_performance_monitor():
    """Reset the global performance monitor (useful for testing)."""
    global _global_monitor
    _global_monitor = PerformanceMonitor()
