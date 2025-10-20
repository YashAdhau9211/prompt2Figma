# app/core/error_recovery.py
"""
Error recovery mechanisms for the Stateful Iterative Design Engine.
Handles session state validation, recovery, and graceful degradation.
"""

import json
import logging
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core.models import DesignState

logger = logging.getLogger(__name__)


class SessionRecoveryManager:
    """
    Manages recovery of corrupted or invalid session states.

    Responsibilities:
    - Validate session state integrity
    - Recover from corrupted states using previous versions
    - Detect and repair common data corruption patterns
    """

    def __init__(self):
        self.validation_rules = self._build_validation_rules()

    def _build_validation_rules(self) -> Dict[str, callable]:
        """Build validation rules for session state data."""
        return {
            "has_wireframe": lambda data: "wireframe_json" in data,
            "has_metadata": lambda data: "metadata" in data,
            "has_created_at": lambda data: "created_at" in data,
            "has_version": lambda data: "version" in data,
            "wireframe_is_json": lambda data: self._is_valid_json(
                data.get("wireframe_json", "")
            ),
            "metadata_is_json": lambda data: self._is_valid_json(
                data.get("metadata", "")
            ),
            "version_is_numeric": lambda data: str(data.get("version", "")).isdigit(),
        }

    def _is_valid_json(self, json_str: str) -> bool:
        """Check if a string is valid JSON."""
        if not json_str:
            return False
        try:
            json.loads(json_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    async def validate_session_state(
        self, session_id: str, state_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate the integrity of a session state.

        Args:
            session_id: Session identifier
            state_data: Raw state data from Redis

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not state_data:
            return False, "State data is empty"

        # Run all validation rules
        for rule_name, rule_func in self.validation_rules.items():
            try:
                if not rule_func(state_data):
                    error_msg = f"Validation failed: {rule_name}"
                    logger.warning(f"Session {session_id} - {error_msg}")
                    return False, error_msg
            except Exception as e:
                error_msg = f"Validation error in {rule_name}: {str(e)}"
                logger.error(f"Session {session_id} - {error_msg}")
                return False, error_msg

        return True, None

    async def validate_design_state_model(
        self, design_state: DesignState
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a DesignState model instance.

        Args:
            design_state: DesignState instance to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check wireframe_json is a dict
            if not isinstance(design_state.wireframe_json, dict):
                return False, "wireframe_json must be a dictionary"

            # Check metadata is a dict
            if not isinstance(design_state.metadata, dict):
                return False, "metadata must be a dictionary"

            # Check version is positive
            if design_state.version < 1:
                return False, "version must be positive"

            # Check created_at is valid
            if not isinstance(design_state.created_at, datetime):
                return False, "created_at must be a datetime"

            return True, None

        except Exception as e:
            return False, f"Model validation error: {str(e)}"

    async def recover_session_state(
        self,
        session_id: str,
        corrupted_data: Dict[str, Any],
        previous_states: List[Dict[str, Any]],
    ) -> Optional[DesignState]:
        """
        Attempt to recover a corrupted session state.

        Recovery strategies:
        1. Try to repair the corrupted data
        2. Rollback to the most recent valid previous state
        3. Reconstruct from partial data

        Args:
            session_id: Session identifier
            corrupted_data: The corrupted state data
            previous_states: List of previous state data (newest first)

        Returns:
            Recovered DesignState or None if recovery failed
        """
        logger.info(f"Attempting to recover session {session_id}")

        # Strategy 1: Try to repair corrupted data
        repaired_state = await self._attempt_repair(corrupted_data)
        if repaired_state:
            logger.info(
                f"Successfully repaired corrupted state for session {session_id}"
            )
            return repaired_state

        # Strategy 2: Rollback to most recent valid previous state
        if previous_states:
            for prev_data in previous_states:
                is_valid, _ = await self.validate_session_state(session_id, prev_data)
                if is_valid:
                    try:
                        recovered_state = DesignState(
                            wireframe_json=json.loads(prev_data["wireframe_json"]),
                            metadata=json.loads(prev_data["metadata"]),
                            created_at=datetime.fromisoformat(prev_data["created_at"]),
                            version=int(prev_data["version"]),
                        )
                        logger.info(
                            f"Recovered session {session_id} by rolling back to version {recovered_state.version}"
                        )
                        return recovered_state
                    except Exception as e:
                        logger.warning(f"Failed to parse previous state: {e}")
                        continue

        # Strategy 3: Reconstruct from partial data
        reconstructed_state = await self._reconstruct_from_partial(
            session_id, corrupted_data, previous_states
        )
        if reconstructed_state:
            logger.info(f"Reconstructed session {session_id} from partial data")
            return reconstructed_state

        logger.error(f"Failed to recover session {session_id}")
        return None

    async def _attempt_repair(
        self, corrupted_data: Dict[str, Any]
    ) -> Optional[DesignState]:
        """
        Attempt to repair corrupted data.

        Common repairs:
        - Fix malformed JSON strings
        - Restore missing required fields with defaults
        - Correct data type mismatches
        """
        try:
            repaired = corrupted_data.copy()

            # Repair wireframe_json
            if "wireframe_json" in repaired:
                if isinstance(repaired["wireframe_json"], str):
                    try:
                        repaired["wireframe_json"] = json.loads(
                            repaired["wireframe_json"]
                        )
                    except json.JSONDecodeError:
                        # Try to fix common JSON issues
                        fixed_json = repaired["wireframe_json"].replace("'", '"')
                        try:
                            repaired["wireframe_json"] = json.loads(fixed_json)
                        except json.JSONDecodeError:
                            return None
            else:
                # Missing wireframe - can't repair
                return None

            # Repair metadata
            if "metadata" in repaired:
                if isinstance(repaired["metadata"], str):
                    try:
                        repaired["metadata"] = json.loads(repaired["metadata"])
                    except json.JSONDecodeError:
                        repaired["metadata"] = {}
            else:
                repaired["metadata"] = {}

            # Repair created_at
            if "created_at" not in repaired:
                repaired["created_at"] = datetime.utcnow().isoformat()

            # Repair version
            if "version" not in repaired:
                repaired["version"] = 1
            elif not str(repaired["version"]).isdigit():
                repaired["version"] = 1

            # Try to create DesignState
            design_state = DesignState(
                wireframe_json=(
                    repaired["wireframe_json"]
                    if isinstance(repaired["wireframe_json"], dict)
                    else json.loads(repaired["wireframe_json"])
                ),
                metadata=(
                    repaired["metadata"]
                    if isinstance(repaired["metadata"], dict)
                    else json.loads(repaired["metadata"])
                ),
                created_at=(
                    datetime.fromisoformat(repaired["created_at"])
                    if isinstance(repaired["created_at"], str)
                    else repaired["created_at"]
                ),
                version=int(repaired["version"]),
            )

            return design_state

        except Exception as e:
            logger.warning(f"Repair attempt failed: {e}")
            return None

    async def _reconstruct_from_partial(
        self,
        session_id: str,
        corrupted_data: Dict[str, Any],
        previous_states: List[Dict[str, Any]],
    ) -> Optional[DesignState]:
        """
        Reconstruct state from partial data using previous states as reference.
        """
        try:
            # Start with a base from the most recent valid previous state
            if not previous_states:
                return None

            base_state = None
            for prev_data in previous_states:
                is_valid, _ = await self.validate_session_state(session_id, prev_data)
                if is_valid:
                    base_state = prev_data
                    break

            if not base_state:
                return None

            # Try to merge any valid parts from corrupted data
            reconstructed = base_state.copy()

            # If corrupted data has a valid wireframe, use it
            if "wireframe_json" in corrupted_data:
                try:
                    if isinstance(corrupted_data["wireframe_json"], str):
                        wireframe = json.loads(corrupted_data["wireframe_json"])
                    else:
                        wireframe = corrupted_data["wireframe_json"]

                    if isinstance(wireframe, dict):
                        reconstructed["wireframe_json"] = json.dumps(wireframe)
                except Exception:
                    pass  # Keep base state wireframe

            # Create DesignState from reconstructed data
            design_state = DesignState(
                wireframe_json=json.loads(reconstructed["wireframe_json"]),
                metadata=json.loads(reconstructed["metadata"]),
                created_at=datetime.fromisoformat(reconstructed["created_at"]),
                version=int(reconstructed["version"]),
            )

            return design_state

        except Exception as e:
            logger.warning(f"Reconstruction failed: {e}")
            return None


class GracefulDegradationManager:
    """
    Manages graceful degradation when Redis or other services are unavailable.

    Provides:
    - In-memory fallback for critical operations
    - Limited functionality mode
    - Status tracking and recovery
    """

    def __init__(self, cache_size: int = 100):
        self._degraded_mode = False
        self._degradation_start_time: Optional[datetime] = None
        self._in_memory_cache: OrderedDict = OrderedDict()
        self._cache_size = cache_size
        self._degradation_reason: Optional[str] = None

    def enable_degraded_mode(self, reason: str = "Service unavailable"):
        """Enable degraded mode with in-memory fallback."""
        if not self._degraded_mode:
            self._degraded_mode = True
            self._degradation_start_time = datetime.utcnow()
            self._degradation_reason = reason
            logger.warning(f"Entering degraded mode: {reason}")

    def disable_degraded_mode(self):
        """Disable degraded mode and clear cache."""
        if self._degraded_mode:
            duration = (
                datetime.utcnow() - self._degradation_start_time
            ).total_seconds()
            logger.info(f"Exiting degraded mode after {duration:.1f}s")
            self._degraded_mode = False
            self._degradation_start_time = None
            self._degradation_reason = None
            self._in_memory_cache.clear()

    def is_degraded(self) -> bool:
        """Check if currently in degraded mode."""
        return self._degraded_mode

    async def cache_session(self, session_id: str, data: Dict[str, Any]):
        """Cache session data in memory during degraded mode."""
        if len(self._in_memory_cache) >= self._cache_size:
            # Remove oldest entry
            self._in_memory_cache.popitem(last=False)

        self._in_memory_cache[session_id] = {
            "data": data,
            "cached_at": datetime.utcnow(),
        }
        logger.debug(f"Cached session {session_id} in memory")

    async def get_cached_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached session data."""
        if session_id in self._in_memory_cache:
            cache_entry = self._in_memory_cache[session_id]
            # Move to end (most recently used)
            self._in_memory_cache.move_to_end(session_id)
            return cache_entry["data"]
        return None

    def get_degradation_status(self) -> Dict[str, Any]:
        """
        Get current degradation status and metrics.

        Returns:
            Dictionary with degradation information
        """
        status = {
            "degraded_mode": self._degraded_mode,
            "reason": self._degradation_reason,
            "cached_sessions": len(self._in_memory_cache),
            "cache_capacity": self._cache_size,
        }

        if self._degradation_start_time:
            duration = (
                datetime.utcnow() - self._degradation_start_time
            ).total_seconds()
            status["degraded_duration_seconds"] = duration
            status["degraded_since"] = self._degradation_start_time.isoformat()

        return status

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the in-memory cache."""
        return {
            "size": len(self._in_memory_cache),
            "capacity": self._cache_size,
            "utilization": (
                len(self._in_memory_cache) / self._cache_size
                if self._cache_size > 0
                else 0
            ),
            "sessions": list(self._in_memory_cache.keys()),
        }
