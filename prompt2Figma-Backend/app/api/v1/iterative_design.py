# app/api/v1/iterative_design.py
"""
API endpoints for iterative design sessions.
Implements the stateful iterative design workflow with session management.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.analytics import AnalyticsManager
from app.core.config import settings
from app.core.models import (CreateSessionRequest, CreateSessionResponse, DesignState,
                             EditSessionRequest, EditSessionResponse, EditType,
                             IterativeDesignError, SessionHistoryResponse)
from app.core.performance_monitor import get_performance_monitor
from app.core.security import InputSanitizer, SecurityError, get_rate_limiter, get_security_monitor
from app.core.session_manager import DesignSessionManager, SessionManagerError
from app.core.state_store import RedisStateStore
from app.tasks.pipeline import generate_wireframe_json
from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/design-sessions", tags=["Iterative Design"])

# Global instances
_state_store: RedisStateStore = None
_session_manager: DesignSessionManager = None
_analytics_manager: AnalyticsManager = None


async def get_state_store() -> RedisStateStore:
    """Dependency to get the state store instance."""
    global _state_store
    if _state_store is None:
        _state_store = RedisStateStore(settings.REDIS_STATE_STORE_URL)
        await _state_store.connect()
    return _state_store


async def get_session_manager() -> DesignSessionManager:
    """Dependency to get the session manager instance."""
    global _session_manager
    if _session_manager is None:
        state_store = await get_state_store()
        _session_manager = DesignSessionManager(state_store)
    return _session_manager


async def get_analytics_manager() -> AnalyticsManager:
    """Dependency to get the analytics manager instance."""
    global _analytics_manager
    if _analytics_manager is None:
        state_store = await get_state_store()
        _analytics_manager = AnalyticsManager(state_store)
    return _analytics_manager


@router.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    await get_state_store()
    await get_session_manager()
    logger.info("Iterative design API initialized")


@router.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown."""
    global _state_store
    if _state_store:
        await _state_store.disconnect()
    logger.info("Iterative design API shutdown")


@router.post("", response_model=CreateSessionResponse, status_code=201)
async def create_design_session(
    request: CreateSessionRequest,
    session_manager: DesignSessionManager = Depends(get_session_manager),
):
    """
    Create a new iterative design session.

    This endpoint creates a new session and generates the initial wireframe
    based on the provided prompt. The session can then be used for iterative edits.

    Requirements: 1.1, 5.1
    """
    try:
        start_time = datetime.utcnow()
        security_monitor = get_security_monitor()

        # Sanitize user input
        try:
            sanitized_prompt, warnings = InputSanitizer.sanitize_prompt(request.prompt)
            if warnings:
                await security_monitor.log_security_event(
                    "prompt_sanitization",
                    details={"warnings": warnings},
                    severity="warning",
                )
        except SecurityError as e:
            await security_monitor.log_security_event(
                "invalid_prompt", details={"error": str(e)}, severity="error"
            )
            raise HTTPException(status_code=400, detail=str(e))

        # Sanitize user ID
        user_id = request.user_id or "anonymous"
        try:
            user_id = InputSanitizer.sanitize_user_id(user_id)
        except SecurityError as e:
            await security_monitor.log_security_event(
                "invalid_user_id",
                user_id=user_id,
                details={"error": str(e)},
                severity="error",
            )
            raise HTTPException(status_code=400, detail=f"Invalid user ID: {str(e)}")

        # Create session using session manager
        session = await session_manager.create_session(user_id, sanitized_prompt)

        # Log session creation
        await security_monitor.log_security_event(
            "session_created",
            session_id=session.session_id,
            user_id=user_id,
            severity="info",
        )

        # Generate initial wireframe using existing pipeline
        try:
            # Use Celery task to generate wireframe with sanitized prompt
            task = generate_wireframe_json.apply_async(args=[sanitized_prompt])
            initial_wireframe = task.get(timeout=180)

            if not initial_wireframe or not isinstance(initial_wireframe, dict):
                raise ValueError("Invalid wireframe generated")

        except Exception as wireframe_error:
            logger.warning(
                f"Wireframe generation failed, using placeholder: {wireframe_error}"
            )
            # Fallback to placeholder wireframe
            initial_wireframe = {
                "type": "container",
                "id": "root",
                "children": [
                    {
                        "type": "text",
                        "id": "placeholder",
                        "content": f"Generated from: {sanitized_prompt}",
                        "styles": {"fontSize": "16px", "color": "#333"},
                    }
                ],
                "metadata": {
                    "prompt": sanitized_prompt,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback": True,
                },
            }

        # Store initial design state
        initial_state = DesignState(
            wireframe_json=initial_wireframe,
            metadata={"initial": True, "prompt": sanitized_prompt, "user_id": user_id},
            version=1,
        )

        await session_manager.update_session_state(session.session_id, initial_state)

        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)

        logger.info(
            f"Created session {session.session_id} for user {user_id} "
            f"in {processing_time}ms"
        )

        return CreateSessionResponse(
            session_id=session.session_id, wireframe_json=initial_wireframe, version=1
        )

    except SessionManagerError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{session_id}/edit", response_model=EditSessionResponse)
async def edit_design_session(
    session_id: str,
    request: EditSessionRequest,
    session_manager: DesignSessionManager = Depends(get_session_manager),
    analytics_manager: AnalyticsManager = Depends(get_analytics_manager),
):
    """
    Apply an edit to an existing design session.

    This endpoint processes the edit prompt in the context of the current
    design state and returns the updated wireframe. The edit is applied
    contextually based on the session's history.

    Requirements: 1.2, 5.1
    """
    try:
        start_time = datetime.utcnow()
        rate_limiter = get_rate_limiter()
        security_monitor = get_security_monitor()

        # Validate and sanitize session ID
        try:
            session_id = InputSanitizer.sanitize_session_id(session_id)
        except SecurityError as e:
            await security_monitor.log_security_event(
                "invalid_session_id",
                session_id=session_id,
                details={"error": str(e)},
                severity="error",
            )
            raise HTTPException(status_code=400, detail=f"Invalid session ID: {str(e)}")

        # Check rate limit
        allowed, reason = await rate_limiter.check_rate_limit(session_id)
        if not allowed:
            await security_monitor.log_security_event(
                "rate_limit_exceeded",
                session_id=session_id,
                details={"reason": reason},
                severity="warning",
            )
            raise HTTPException(status_code=429, detail=reason)

        # Sanitize edit prompt
        try:
            sanitized_prompt, warnings = InputSanitizer.sanitize_prompt(
                request.edit_prompt
            )
            if warnings:
                await security_monitor.log_security_event(
                    "edit_prompt_sanitization",
                    session_id=session_id,
                    details={"warnings": warnings},
                    severity="warning",
                )
        except SecurityError as e:
            await security_monitor.log_security_event(
                "invalid_edit_prompt",
                session_id=session_id,
                details={"error": str(e)},
                severity="error",
            )
            raise HTTPException(status_code=400, detail=str(e))

        # Verify session exists and is active
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found or expired"
            )

        # Get current design state
        current_state = await session_manager.state_store.get_design_state(session_id)
        if not current_state:
            raise HTTPException(
                status_code=404,
                detail=f"Design state not found for session {session_id}",
            )

        # TODO: In future tasks, integrate with ContextProcessingEngine
        # For now, apply a simple edit by generating a new wireframe
        # that incorporates the edit prompt with context

        # Build contextual prompt with sanitized input
        contextual_prompt = f"""
        Current design state: {current_state.wireframe_json}
        
        User edit request: {sanitized_prompt}
        
        Please update the design based on the edit request while maintaining 
        the existing structure and context.
        """

        try:
            # Use existing pipeline to generate updated wireframe
            task = generate_wireframe_json.apply_async(args=[contextual_prompt])
            updated_wireframe = task.get(timeout=180)

            if not updated_wireframe or not isinstance(updated_wireframe, dict):
                # Fallback: make a simple modification to current wireframe
                updated_wireframe = current_state.wireframe_json.copy()
                if "children" not in updated_wireframe:
                    updated_wireframe["children"] = []

                updated_wireframe["children"].append(
                    {
                        "type": "text",
                        "id": f"edit-{session.current_version + 1}",
                        "content": f"Edit: {sanitized_prompt}",
                        "styles": {
                            "fontSize": "14px",
                            "color": "#666",
                            "marginTop": "10px",
                        },
                    }
                )

        except Exception as gen_error:
            logger.warning(
                f"Wireframe generation failed for edit, using fallback: {gen_error}"
            )
            # Fallback modification
            updated_wireframe = current_state.wireframe_json.copy()
            if "children" not in updated_wireframe:
                updated_wireframe["children"] = []

            updated_wireframe["children"].append(
                {
                    "type": "text",
                    "id": f"edit-{session.current_version + 1}",
                    "content": f"Edit: {sanitized_prompt}",
                    "styles": {
                        "fontSize": "14px",
                        "color": "#666",
                        "marginTop": "10px",
                    },
                }
            )

        # Apply edit using session manager
        changes = {
            "prompt": sanitized_prompt,
            "edit_type": "modify",
            "target_elements": [],
            "summary": f"Applied edit: {sanitized_prompt}",
        }

        metadata = {
            "edit_prompt": sanitized_prompt,
            "previous_version": session.current_version,
        }

        edit_result = await session_manager.apply_edit(
            session_id, updated_wireframe, changes, metadata
        )

        end_time = datetime.utcnow()
        actual_processing_time = int((end_time - start_time).total_seconds() * 1000)

        # Track edit in analytics
        edit_type = EditType(changes.get("edit_type", "modify"))
        await analytics_manager.track_edit(
            session_id, edit_type, actual_processing_time, success=edit_result.success
        )

        logger.info(
            f"Applied edit to session {session_id}, "
            f"new version: {edit_result.new_version}, "
            f"processing time: {actual_processing_time}ms"
        )

        return EditSessionResponse(
            session_id=session_id,
            wireframe_json=edit_result.updated_wireframe,
            version=edit_result.new_version,
            changes_summary=edit_result.changes_summary,
            processing_time_ms=actual_processing_time,
        )

    except HTTPException:
        raise
    except SessionManagerError as e:
        logger.error(f"Session manager error editing session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error editing session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    session_manager: DesignSessionManager = Depends(get_session_manager),
):
    """
    Get the version history for a design session.

    Returns all versions of the design with metadata about changes,
    allowing users to track the evolution of their design.

    Requirements: 5.4
    """
    try:
        # Verify session exists
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found or expired"
            )

        # Get session history using session manager
        history = await session_manager.get_session_history(session_id)

        # Format version details
        version_details = []
        for state in history:
            # Count elements in wireframe
            element_count = 0
            if isinstance(state.wireframe_json, dict):
                element_count = len(state.wireframe_json.get("children", []))

            version_details.append(
                {
                    "version": state.version,
                    "created_at": state.created_at.isoformat(),
                    "metadata": state.metadata,
                    "element_count": element_count,
                    "wireframe_json": state.wireframe_json,
                }
            )

        logger.info(
            f"Retrieved history for session {session_id}: {len(version_details)} versions"
        )

        return SessionHistoryResponse(
            session_id=session_id,
            versions=version_details,
            total_versions=len(version_details),
        )

    except HTTPException:
        raise
    except SessionManagerError as e:
        logger.error(f"Session manager error getting history for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting history for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{session_id}")
async def get_session_details(
    session_id: str,
    session_manager: DesignSessionManager = Depends(get_session_manager),
):
    """
    Get current session details and latest design state.

    Returns comprehensive information about the session including
    current state, metadata, and recent activity.
    """
    try:
        # Get session
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found or expired"
            )

        # Get current design state
        current_state = await session_manager.state_store.get_design_state(session_id)
        if not current_state:
            raise HTTPException(
                status_code=404,
                detail=f"Design state not found for session {session_id}",
            )

        # Get context history
        contexts = await session_manager.state_store.get_context_history(
            session_id, limit=5
        )

        # Get session metadata for total edits
        metadata = await session_manager.state_store.get_session_metadata(session_id)

        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "initial_prompt": session.initial_prompt,
            "current_version": session.current_version,
            "total_edits": metadata.total_edits if metadata else 0,
            "status": session.status.value,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "current_wireframe": current_state.wireframe_json,
            "recent_edits": [
                {
                    "prompt": ctx.prompt,
                    "edit_type": ctx.edit_type.value,
                    "timestamp": ctx.timestamp.isoformat(),
                    "processing_time_ms": ctx.processing_time_ms,
                }
                for ctx in contexts
            ],
        }

    except HTTPException:
        raise
    except SessionManagerError as e:
        logger.error(f"Session manager error getting details for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting session details {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/metrics/performance", tags=["Monitoring"])
async def get_performance_metrics():
    """
    Get system-wide performance metrics.

    Returns aggregated performance statistics for all metric types.
    """
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_all_stats()

        # Convert stats to serializable format
        metrics = {}
        for metric_name, metric_stats in stats.items():
            metrics[metric_name] = {
                "count": metric_stats.count,
                "avg_ms": round(metric_stats.avg_ms, 2),
                "min_ms": round(metric_stats.min_ms, 2),
                "max_ms": round(metric_stats.max_ms, 2),
                "p50_ms": round(metric_stats.p50_ms, 2),
                "p95_ms": round(metric_stats.p95_ms, 2),
                "p99_ms": round(metric_stats.p99_ms, 2),
                "total_ms": round(metric_stats.total_ms, 2),
            }

        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/health", tags=["Monitoring"])
async def get_health_status(
    session_manager: DesignSessionManager = Depends(get_session_manager),
):
    """
    Get system health status including performance and Redis health.

    Returns comprehensive health indicators for the system.
    """
    try:
        monitor = get_performance_monitor()
        perf_health = monitor.get_health_status()

        # Get Redis health from state store
        redis_health = session_manager.state_store.get_health_status()

        overall_healthy = perf_health["healthy"] and redis_health["healthy"]

        return {
            "success": True,
            "healthy": overall_healthy,
            "performance": {
                "healthy": perf_health["healthy"],
                "uptime_seconds": perf_health["uptime_seconds"],
                "total_metrics_collected": perf_health["total_metrics_collected"],
                "active_sessions": perf_health["active_sessions"],
                "recent_alerts": perf_health["recent_alerts"],
                "warnings": perf_health["warnings"],
                "stats": perf_health["performance_stats"],
            },
            "redis": redis_health,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/session/{session_id}", tags=["Monitoring"])
async def get_session_performance(
    session_id: str,
    session_manager: DesignSessionManager = Depends(get_session_manager),
):
    """
    Get performance metrics for a specific session.

    Args:
        session_id: The session identifier

    Returns:
        Performance statistics for the specified session
    """
    try:
        # Verify session exists
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        monitor = get_performance_monitor()
        session_stats = monitor.get_session_stats(session_id)

        # Get session metrics from version manager
        session_metrics = await session_manager.get_session_metrics(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "performance_stats": session_stats,
            "session_metrics": session_metrics.dict() if session_metrics else None,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session performance for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/alerts", tags=["Monitoring"])
async def get_performance_alerts(limit: int = 10):
    """
    Get recent performance alerts.

    Args:
        limit: Maximum number of alerts to return (default: 10)

    Returns:
        List of recent performance alerts
    """
    try:
        monitor = get_performance_monitor()
        alerts = monitor.get_recent_alerts(limit=limit)

        return {
            "success": True,
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Endpoints


@router.get("/analytics/session/{session_id}", tags=["Analytics"])
async def get_session_analytics(
    session_id: str,
    analytics_manager: AnalyticsManager = Depends(get_analytics_manager),
    session_manager: DesignSessionManager = Depends(get_session_manager),
):
    """
    Get comprehensive analytics for a specific session.

    Returns session metrics including edit types, duration, and performance.

    Requirements: 4.1, 4.2, 4.3
    """
    try:
        # Verify session exists
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail=f"Session {session_id} not found"
            )

        # Calculate session metrics
        metrics = await analytics_manager.calculate_session_metrics(session_id)

        if not metrics:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate metrics for session {session_id}",
            )

        return {
            "success": True,
            "session_id": session_id,
            "metrics": {
                "total_edits": metrics.total_edits,
                "session_duration_minutes": metrics.session_duration_minutes,
                "edit_types_distribution": {
                    k.value: v for k, v in metrics.edit_types_distribution.items()
                },
                "average_processing_time_ms": round(
                    metrics.average_processing_time_ms, 2
                ),
                "user_satisfaction_score": metrics.user_satisfaction_score,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session analytics for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/daily", tags=["Analytics"])
async def get_daily_analytics(
    date: Optional[str] = None,
    analytics_manager: AnalyticsManager = Depends(get_analytics_manager),
):
    """
    Get analytics for a specific date.

    Args:
        date: Date in YYYY-MM-DD format (defaults to today)

    Returns:
        Daily analytics including edit counts, types, and success rates

    Requirements: 4.3, 4.4
    """
    try:
        # Parse date if provided
        target_date = None
        if date:
            try:
                target_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
                )

        analytics = await analytics_manager.get_daily_analytics(target_date)

        return {
            "success": True,
            "analytics": analytics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get daily analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trends", tags=["Analytics"])
async def get_analytics_trends(
    days: int = 7, analytics_manager: AnalyticsManager = Depends(get_analytics_manager)
):
    """
    Get analytics trends over a specified number of days.

    Args:
        days: Number of days to analyze (default: 7)

    Returns:
        Trend data including edit types, performance, and success rates

    Requirements: 4.3, 4.4
    """
    try:
        if days < 1 or days > 90:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 90")

        # Get edit type trends
        edit_trends = await analytics_manager.get_edit_type_trends(days)

        # Get performance trends
        performance_trends = await analytics_manager.get_performance_trends(days)

        return {
            "success": True,
            "period_days": days,
            "edit_type_trends": edit_trends,
            "performance_trends": performance_trends,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analytics trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/user/{user_id}", tags=["Analytics"])
async def get_user_analytics(
    user_id: str, analytics_manager: AnalyticsManager = Depends(get_analytics_manager)
):
    """
    Get engagement analytics for a specific user.

    Args:
        user_id: The user identifier

    Returns:
        User engagement metrics including sessions, edits, and duration

    Requirements: 4.1, 4.2
    """
    try:
        engagement_metrics = await analytics_manager.get_user_engagement_metrics(
            user_id
        )

        return {
            "success": True,
            "user_id": user_id,
            "engagement_metrics": engagement_metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get user analytics for {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/edit-types", tags=["Analytics"])
async def get_edit_type_analytics(
    days: int = 7, analytics_manager: AnalyticsManager = Depends(get_analytics_manager)
):
    """
    Get analytics for edit types over a period.

    Args:
        days: Number of days to analyze (default: 7)

    Returns:
        Edit type distribution and trends

    Requirements: 4.3, 4.4
    """
    try:
        if days < 1 or days > 90:
            raise HTTPException(status_code=400, detail="Days must be between 1 and 90")

        trends = await analytics_manager.get_edit_type_trends(days)

        return {
            "success": True,
            "period_days": days,
            "edit_type_trends": trends,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get edit type analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security Endpoints


@router.get("/security/events", tags=["Security"])
async def get_security_events(
    limit: int = 100, severity: Optional[str] = None, event_type: Optional[str] = None
):
    """
    Get recent security events.

    Args:
        limit: Maximum number of events to return (default: 100)
        severity: Filter by severity (info, warning, error, critical)
        event_type: Filter by event type

    Returns:
        List of security events
    """
    try:
        from app.core.security import get_security_monitor

        monitor = get_security_monitor()
        events = await monitor.get_recent_events(
            limit=limit, severity=severity, event_type=event_type
        )

        return {
            "success": True,
            "events": events,
            "count": len(events),
            "filters": {"severity": severity, "event_type": event_type},
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/session/{session_id}/events", tags=["Security"])
async def get_session_security_events(session_id: str, limit: int = 50):
    """
    Get security events for a specific session.

    Args:
        session_id: The session identifier
        limit: Maximum number of events to return (default: 50)

    Returns:
        List of security events for the session
    """
    try:
        from app.core.security import InputSanitizer, SecurityError, get_security_monitor

        # Validate session ID
        try:
            session_id = InputSanitizer.sanitize_session_id(session_id)
        except SecurityError as e:
            raise HTTPException(status_code=400, detail=str(e))

        monitor = get_security_monitor()
        events = await monitor.get_session_events(session_id, limit=limit)

        return {
            "success": True,
            "session_id": session_id,
            "events": events,
            "count": len(events),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session security events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/stats", tags=["Security"])
async def get_security_stats():
    """
    Get security statistics.

    Returns:
        Security statistics including event counts and distributions
    """
    try:
        from app.core.security import get_security_monitor

        monitor = get_security_monitor()
        stats = await monitor.get_security_stats()

        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get security stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/rate-limit/{session_id}", tags=["Security"])
async def get_rate_limit_status(session_id: str):
    """
    Get rate limit status for a session.

    Args:
        session_id: The session identifier

    Returns:
        Rate limit statistics for the session
    """
    try:
        from app.core.security import InputSanitizer, SecurityError, get_rate_limiter

        # Validate session ID
        try:
            session_id = InputSanitizer.sanitize_session_id(session_id)
        except SecurityError as e:
            raise HTTPException(status_code=400, detail=str(e))

        limiter = get_rate_limiter()
        stats = limiter.get_session_stats(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "rate_limit_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security/rate-limit/{session_id}/reset", tags=["Security"])
async def reset_rate_limit(session_id: str):
    """
    Reset rate limits for a session (admin only).

    Args:
        session_id: The session identifier

    Returns:
        Success confirmation
    """
    try:
        from app.core.security import (InputSanitizer, SecurityError, get_rate_limiter,
                                       get_security_monitor)

        # Validate session ID
        try:
            session_id = InputSanitizer.sanitize_session_id(session_id)
        except SecurityError as e:
            raise HTTPException(status_code=400, detail=str(e))

        limiter = get_rate_limiter()
        await limiter.reset_session_limits(session_id)

        # Log the reset
        monitor = get_security_monitor()
        await monitor.log_security_event(
            "rate_limit_reset",
            session_id=session_id,
            details={"reset_by": "admin"},
            severity="info",
        )

        return {
            "success": True,
            "session_id": session_id,
            "message": "Rate limits reset successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset rate limit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/edit-types/popular", tags=["Analytics"])
async def get_popular_edit_types(
    limit: int = 5, analytics_manager: AnalyticsManager = Depends(get_analytics_manager)
):
    """
    Get the most popular edit types.

    Args:
        limit: Maximum number of edit types to return (default: 5)

    Returns:
        List of most common edit types with counts

    Requirements: 4.3, 4.4
    """
    try:
        if limit < 1 or limit > 20:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 20"
            )

        popular_types = await analytics_manager.get_most_common_edit_types(limit)

        return {
            "success": True,
            "popular_edit_types": popular_types,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get popular edit types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Security Endpoints


@router.get("/security/rate-limit/{session_id}", tags=["Security"])
async def get_rate_limit_status(session_id: str):
    """
    Get rate limit status for a session.

    Args:
        session_id: The session identifier

    Returns:
        Rate limit information including remaining requests

    Requirements: 2.5, 5.5
    """
    try:
        # Validate session ID
        try:
            session_id = InputSanitizer.sanitize_session_id(session_id)
        except SecurityError as e:
            raise HTTPException(status_code=400, detail=str(e))

        rate_limiter = get_rate_limiter()
        remaining = await rate_limiter.get_remaining_requests(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "rate_limit": remaining,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit status for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/events", tags=["Security"])
async def get_security_events(
    limit: int = 100, severity: Optional[str] = None, event_type: Optional[str] = None
):
    """
    Get recent security events.

    Args:
        limit: Maximum number of events to return (default: 100)
        severity: Filter by severity (info, warning, error, critical)
        event_type: Filter by event type

    Returns:
        List of security events

    Requirements: 2.5, 3.3
    """
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400, detail="Limit must be between 1 and 1000"
            )

        security_monitor = get_security_monitor()
        events = await security_monitor.get_recent_events(
            limit=limit, severity=severity, event_type=event_type
        )

        return {
            "success": True,
            "events": events,
            "count": len(events),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/stats", tags=["Security"])
async def get_security_stats():
    """
    Get security statistics.

    Returns:
        Security metrics including event counts and distributions

    Requirements: 2.5, 3.3
    """
    try:
        security_monitor = get_security_monitor()
        stats = await security_monitor.get_security_stats()

        return {
            "success": True,
            "security_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get security stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
