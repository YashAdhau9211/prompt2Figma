# app/core/session_manager.py
"""
Design Session Manager for the Stateful Iterative Design Engine.
Central orchestrator for managing design sessions, state transitions, and coordinating between components.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.models import (
    DesignSession, DesignState, EditResult, SessionMetadata, 
    SessionStatus, EditContext, SessionMetrics, VersionDiff
)
from app.core.state_store import RedisStateStore
from app.core.version_manager import VersionManager

logger = logging.getLogger(__name__)


class SessionManagerError(Exception):
    """Custom exception for session manager operations."""
    pass


class DesignSessionManager:
    """
    Central orchestrator for managing design sessions, state transitions, 
    and coordinating between components.
    
    Responsibilities:
    - Session lifecycle management
    - Coordinating state updates
    - Managing session timeouts and cleanup
    - Integrating with existing pipeline for code generation
    """
    
    def __init__(self, state_store: RedisStateStore, session_timeout_hours: int = 24):
        self.state_store = state_store
        self.session_timeout = timedelta(hours=session_timeout_hours)
        self.version_manager = VersionManager(state_store)
    
    async def create_session(self, user_id: str, initial_prompt: str) -> DesignSession:
        """
        Create a new design session.
        
        Args:
            user_id: Identifier for the user creating the session
            initial_prompt: The initial design prompt
            
        Returns:
            DesignSession: The created session object
            
        Raises:
            SessionManagerError: If session creation fails
        """
        try:
            # Create new session object
            session = DesignSession(
                user_id=user_id,
                initial_prompt=initial_prompt,
                current_version=1,
                status=SessionStatus.ACTIVE
            )
            
            # Store session in Redis
            success = await self.state_store.create_session(session)
            if not success:
                raise SessionManagerError(f"Failed to store session {session.session_id} in Redis")
            
            logger.info(f"Created new design session {session.session_id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to create session for user {user_id}: {e}")
            raise SessionManagerError(f"Session creation failed: {str(e)}")
    
    async def get_session(self, session_id: str) -> Optional[DesignSession]:
        """
        Retrieve a design session by ID.
        
        Args:
            session_id: The session identifier
            
        Returns:
            DesignSession or None if not found
            
        Raises:
            SessionManagerError: If session retrieval fails due to system error
        """
        try:
            metadata = await self.state_store.get_session_metadata(session_id)
            if not metadata:
                logger.warning(f"Session {session_id} not found")
                return None
            
            # Check if session has expired
            if self._is_session_expired(metadata):
                logger.info(f"Session {session_id} has expired, marking as expired")
                await self._mark_session_expired(session_id)
                return None
            
            # Update last activity
            await self.state_store.update_session_activity(session_id)
            
            # Convert metadata to DesignSession
            session = DesignSession(
                session_id=metadata.session_id,
                user_id=metadata.user_id,
                initial_prompt=metadata.initial_prompt,
                current_version=metadata.current_version,
                created_at=metadata.created_at,
                last_activity=metadata.last_activity,
                status=SessionStatus(metadata.status)
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            raise SessionManagerError(f"Session retrieval failed: {str(e)}")
    
    async def get_session_history(self, session_id: str) -> List[DesignState]:
        """
        Get the version history for a design session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            List of DesignState objects representing the version history
            
        Raises:
            SessionManagerError: If history retrieval fails
        """
        try:
            # Verify session exists and is accessible
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            # Get all available versions
            versions = await self.state_store.get_all_versions(session_id)
            if not versions:
                logger.warning(f"No versions found for session {session_id}")
                return []
            
            # Retrieve all design states
            history = []
            for version in versions:
                state = await self.state_store.get_design_state(session_id, version)
                if state:
                    history.append(state)
            
            # Sort by version number
            history.sort(key=lambda x: x.version)
            
            logger.info(f"Retrieved {len(history)} versions for session {session_id}")
            return history
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to get session history for {session_id}: {e}")
            raise SessionManagerError(f"History retrieval failed: {str(e)}")
    
    async def update_session_state(self, session_id: str, new_state: DesignState) -> bool:
        """
        Update the design state for a session with a new version.
        
        Note: This method is deprecated in favor of apply_edit() which uses the version manager.
        Kept for backward compatibility.
        
        Args:
            session_id: The session identifier
            new_state: The new design state to store
            
        Returns:
            bool: True if update was successful
            
        Raises:
            SessionManagerError: If state update fails
        """
        try:
            # Verify session exists and is active
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            if session.status != SessionStatus.ACTIVE:
                raise SessionManagerError(f"Cannot update inactive session {session_id}")
            
            # Store the new state
            success = await self.state_store.store_design_state(
                session_id, new_state.version, new_state
            )
            
            if not success:
                raise SessionManagerError(f"Failed to store design state for session {session_id}")
            
            # Update session activity
            await self.state_store.update_session_activity(session_id)
            
            logger.info(f"Updated session {session_id} to version {new_state.version}")
            return True
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to update session state for {session_id}: {e}")
            raise SessionManagerError(f"State update failed: {str(e)}")
    
    async def add_edit_context(self, session_id: str, context: EditContext) -> bool:
        """
        Add edit context to a session's history.
        
        Args:
            session_id: The session identifier
            context: The edit context to add
            
        Returns:
            bool: True if context was added successfully
            
        Raises:
            SessionManagerError: If context addition fails
        """
        try:
            # Verify session exists
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            # Add context entry
            success = await self.state_store.add_context_entry(session_id, context)
            if not success:
                raise SessionManagerError(f"Failed to add context for session {session_id}")
            
            # Increment edit count
            await self.state_store.increment_edit_count(session_id)
            
            return True
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to add edit context for session {session_id}: {e}")
            raise SessionManagerError(f"Context addition failed: {str(e)}")
    
    async def complete_session(self, session_id: str) -> bool:
        """
        Mark a session as completed.
        
        Args:
            session_id: The session identifier
            
        Returns:
            bool: True if session was marked as completed
            
        Raises:
            SessionManagerError: If session completion fails
        """
        try:
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found")
            
            # Update session status to completed
            session_key = f"session:{session_id}:metadata"
            await self.state_store.redis.hset(session_key, "status", SessionStatus.COMPLETED.value)
            await self.state_store.update_session_activity(session_id)
            
            logger.info(f"Marked session {session_id} as completed")
            return True
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            raise SessionManagerError(f"Session completion failed: {str(e)}")
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions across the system.
        
        Returns:
            int: Number of sessions cleaned up
            
        Raises:
            SessionManagerError: If cleanup operation fails
        """
        try:
            # This is a basic implementation - in production you'd want more sophisticated cleanup
            # For now, we rely on Redis TTL for automatic cleanup, but we can add manual cleanup logic
            
            cleaned_count = await self.state_store.cleanup_expired_sessions()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            raise SessionManagerError(f"Session cleanup failed: {str(e)}")
    
    async def get_user_sessions(self, user_id: str) -> List[str]:
        """
        Get all active session IDs for a user.
        
        Args:
            user_id: The user identifier
            
        Returns:
            List of active session IDs for the user
            
        Raises:
            SessionManagerError: If user session retrieval fails
        """
        try:
            session_ids = await self.state_store.get_user_sessions(user_id)
            
            # Filter out expired sessions
            active_sessions = []
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session and session.status == SessionStatus.ACTIVE:
                    active_sessions.append(session_id)
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            raise SessionManagerError(f"User session retrieval failed: {str(e)}")
    
    async def apply_edit(self, session_id: str, wireframe_json: dict, changes: dict, metadata: dict) -> EditResult:
        """
        Apply an edit to a session using the version manager.
        
        Args:
            session_id: The session identifier
            wireframe_json: The updated wireframe JSON
            changes: Dictionary describing what changed
            metadata: Additional metadata for this version
            
        Returns:
            EditResult: The result of applying the edit
            
        Raises:
            SessionManagerError: If edit application fails
        """
        try:
            # Verify session exists and is active
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            if session.status != SessionStatus.ACTIVE:
                raise SessionManagerError(f"Cannot edit inactive session {session_id}")
            
            # Create new version using version manager
            start_time = datetime.utcnow()
            new_version = await self.version_manager.create_version(
                session_id, wireframe_json, changes, metadata
            )
            end_time = datetime.utcnow()
            
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Add edit context
            edit_context = EditContext(
                prompt=changes.get("prompt", ""),
                edit_type=changes.get("edit_type", "modify"),
                target_elements=changes.get("target_elements", []),
                processing_time_ms=processing_time_ms
            )
            
            await self.add_edit_context(session_id, edit_context)
            
            return EditResult(
                success=True,
                new_version=new_version,
                updated_wireframe=wireframe_json,
                changes_summary=changes.get("summary", ""),
                processing_time_ms=processing_time_ms
            )
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to apply edit to session {session_id}: {e}")
            raise SessionManagerError(f"Edit application failed: {str(e)}")
    
    async def get_version_diff(self, session_id: str, from_version: int, to_version: int) -> Optional[VersionDiff]:
        """
        Get the differences between two versions of a session.
        
        Args:
            session_id: The session identifier
            from_version: Starting version number
            to_version: Ending version number
            
        Returns:
            VersionDiff or None if versions not found
            
        Raises:
            SessionManagerError: If diff calculation fails
        """
        try:
            # Verify session exists
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            return await self.version_manager.get_version_diff(session_id, from_version, to_version)
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to get version diff for session {session_id}: {e}")
            raise SessionManagerError(f"Version diff failed: {str(e)}")
    
    async def compress_session_versions(self, session_id: str, keep_recent: int = 10) -> int:
        """
        Compress old versions for a session to save space.
        
        Args:
            session_id: The session identifier
            keep_recent: Number of recent versions to keep uncompressed
            
        Returns:
            Number of versions compressed
            
        Raises:
            SessionManagerError: If compression fails
        """
        try:
            # Verify session exists
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            compressed_count = await self.version_manager.compress_old_versions(session_id, keep_recent)
            
            if compressed_count > 0:
                logger.info(f"Compressed {compressed_count} versions for session {session_id}")
            
            return compressed_count
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to compress versions for session {session_id}: {e}")
            raise SessionManagerError(f"Version compression failed: {str(e)}")
    
    async def verify_session_integrity(self, session_id: str) -> dict:
        """
        Verify the integrity of all versions in a session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary with integrity check results
            
        Raises:
            SessionManagerError: If integrity check fails
        """
        try:
            # Verify session exists
            session = await self.get_session(session_id)
            if not session:
                raise SessionManagerError(f"Session {session_id} not found or expired")
            
            # Get all versions
            versions = await self.state_store.get_all_versions(session_id)
            
            integrity_results = {
                "session_id": session_id,
                "total_versions": len(versions),
                "valid_versions": 0,
                "invalid_versions": 0,
                "corrupted_versions": []
            }
            
            # Check each version
            for version in versions:
                is_valid = await self.version_manager.verify_version_integrity(session_id, version)
                if is_valid:
                    integrity_results["valid_versions"] += 1
                else:
                    integrity_results["invalid_versions"] += 1
                    integrity_results["corrupted_versions"].append(version)
            
            return integrity_results
            
        except SessionManagerError:
            raise
        except Exception as e:
            logger.error(f"Failed to verify integrity for session {session_id}: {e}")
            raise SessionManagerError(f"Integrity verification failed: {str(e)}")
    
    async def get_session_metrics(self, session_id: str) -> Optional[SessionMetrics]:
        """
        Calculate and return comprehensive metrics for a session using version manager.
        
        Args:
            session_id: The session identifier
            
        Returns:
            SessionMetrics or None if session not found
            
        Raises:
            SessionManagerError: If metrics calculation fails
        """
        try:
            # Use version manager for comprehensive metrics calculation
            metrics = await self.version_manager.calculate_session_metrics(session_id)
            
            if not metrics:
                # Fallback to basic metrics calculation
                metadata = await self.state_store.get_session_metadata(session_id)
                if not metadata:
                    return None
                
                # Get context history to calculate basic metrics
                context_history = await self.state_store.get_context_history(session_id, limit=100)
                
                # Calculate session duration
                duration = (metadata.last_activity - metadata.created_at).total_seconds() / 60
                
                # Calculate edit type distribution
                edit_types_dist = {}
                total_processing_time = 0
                
                for context in context_history:
                    edit_type = context.edit_type
                    edit_types_dist[edit_type] = edit_types_dist.get(edit_type, 0) + 1
                    total_processing_time += context.processing_time_ms
                
                # Calculate average processing time
                avg_processing_time = (
                    total_processing_time / len(context_history) 
                    if context_history else 0
                )
                
                metrics = SessionMetrics(
                    total_edits=metadata.total_edits,
                    session_duration_minutes=int(duration),
                    edit_types_distribution=edit_types_dist,
                    average_processing_time_ms=avg_processing_time
                )
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics for session {session_id}: {e}")
            raise SessionManagerError(f"Metrics calculation failed: {str(e)}")
    
    def _is_session_expired(self, metadata: SessionMetadata) -> bool:
        """Check if a session has expired based on last activity."""
        expiry_time = metadata.last_activity + self.session_timeout
        return datetime.utcnow() > expiry_time
    
    async def _mark_session_expired(self, session_id: str) -> bool:
        """Mark a session as expired in Redis."""
        try:
            session_key = f"session:{session_id}:metadata"
            await self.state_store.redis.hset(session_key, "status", SessionStatus.EXPIRED.value)
            return True
        except Exception as e:
            logger.error(f"Failed to mark session {session_id} as expired: {e}")
            return False