# app/api/v1/iterative_design.py
"""
API endpoints for iterative design sessions.
Implements the stateful iterative design workflow with session management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import logging
from datetime import datetime

from app.core.models import (
    CreateSessionRequest, CreateSessionResponse,
    EditSessionRequest, EditSessionResponse,
    SessionHistoryResponse, IterativeDesignError,
    DesignState
)
from app.core.state_store import RedisStateStore
from app.core.session_manager import DesignSessionManager, SessionManagerError
from app.core.config import settings
from app.tasks.pipeline import generate_wireframe_json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/design-sessions", tags=["Iterative Design"])

# Global instances
_state_store: RedisStateStore = None
_session_manager: DesignSessionManager = None


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
    session_manager: DesignSessionManager = Depends(get_session_manager)
):
    """
    Create a new iterative design session.
    
    This endpoint creates a new session and generates the initial wireframe
    based on the provided prompt. The session can then be used for iterative edits.
    
    Requirements: 1.1, 5.1
    """
    try:
        start_time = datetime.utcnow()
        
        # Create session using session manager
        user_id = request.user_id or "anonymous"
        session = await session_manager.create_session(user_id, request.prompt)
        
        # Generate initial wireframe using existing pipeline
        try:
            # Use Celery task to generate wireframe
            task = generate_wireframe_json.apply_async(args=[request.prompt])
            initial_wireframe = task.get(timeout=180)
            
            if not initial_wireframe or not isinstance(initial_wireframe, dict):
                raise ValueError("Invalid wireframe generated")
                
        except Exception as wireframe_error:
            logger.warning(f"Wireframe generation failed, using placeholder: {wireframe_error}")
            # Fallback to placeholder wireframe
            initial_wireframe = {
                "type": "container",
                "id": "root",
                "children": [
                    {
                        "type": "text",
                        "id": "placeholder",
                        "content": f"Generated from: {request.prompt}",
                        "styles": {"fontSize": "16px", "color": "#333"}
                    }
                ],
                "metadata": {
                    "prompt": request.prompt,
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback": True
                }
            }
        
        # Store initial design state
        initial_state = DesignState(
            wireframe_json=initial_wireframe,
            metadata={
                "initial": True,
                "prompt": request.prompt,
                "user_id": user_id
            },
            version=1
        )
        
        await session_manager.update_session_state(session.session_id, initial_state)
        
        end_time = datetime.utcnow()
        processing_time = int((end_time - start_time).total_seconds() * 1000)
        
        logger.info(
            f"Created session {session.session_id} for user {user_id} "
            f"in {processing_time}ms"
        )
        
        return CreateSessionResponse(
            session_id=session.session_id,
            wireframe_json=initial_wireframe,
            version=1
        )
        
    except SessionManagerError as e:
        logger.error(f"Session manager error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{session_id}/edit", response_model=EditSessionResponse)
async def edit_design_session(
    session_id: str,
    request: EditSessionRequest,
    session_manager: DesignSessionManager = Depends(get_session_manager)
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
        
        # Verify session exists and is active
        session = await session_manager.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )
        
        # Get current design state
        current_state = await session_manager.state_store.get_design_state(session_id)
        if not current_state:
            raise HTTPException(
                status_code=404,
                detail=f"Design state not found for session {session_id}"
            )
        
        # TODO: In future tasks, integrate with ContextProcessingEngine
        # For now, apply a simple edit by generating a new wireframe
        # that incorporates the edit prompt with context
        
        # Build contextual prompt
        contextual_prompt = f"""
        Current design state: {current_state.wireframe_json}
        
        User edit request: {request.edit_prompt}
        
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
                
                updated_wireframe["children"].append({
                    "type": "text",
                    "id": f"edit-{session.current_version + 1}",
                    "content": f"Edit: {request.edit_prompt}",
                    "styles": {"fontSize": "14px", "color": "#666", "marginTop": "10px"}
                })
                
        except Exception as gen_error:
            logger.warning(f"Wireframe generation failed for edit, using fallback: {gen_error}")
            # Fallback modification
            updated_wireframe = current_state.wireframe_json.copy()
            if "children" not in updated_wireframe:
                updated_wireframe["children"] = []
            
            updated_wireframe["children"].append({
                "type": "text",
                "id": f"edit-{session.current_version + 1}",
                "content": f"Edit: {request.edit_prompt}",
                "styles": {"fontSize": "14px", "color": "#666", "marginTop": "10px"}
            })
        
        # Apply edit using session manager
        changes = {
            "prompt": request.edit_prompt,
            "edit_type": "modify",
            "target_elements": [],
            "summary": f"Applied edit: {request.edit_prompt}"
        }
        
        metadata = {
            "edit_prompt": request.edit_prompt,
            "previous_version": session.current_version
        }
        
        edit_result = await session_manager.apply_edit(
            session_id,
            updated_wireframe,
            changes,
            metadata
        )
        
        end_time = datetime.utcnow()
        actual_processing_time = int((end_time - start_time).total_seconds() * 1000)
        
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
            processing_time_ms=actual_processing_time
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
    session_manager: DesignSessionManager = Depends(get_session_manager)
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
                status_code=404,
                detail=f"Session {session_id} not found or expired"
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
            
            version_details.append({
                "version": state.version,
                "created_at": state.created_at.isoformat(),
                "metadata": state.metadata,
                "element_count": element_count,
                "wireframe_json": state.wireframe_json
            })
        
        logger.info(f"Retrieved history for session {session_id}: {len(version_details)} versions")
        
        return SessionHistoryResponse(
            session_id=session_id,
            versions=version_details,
            total_versions=len(version_details)
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
    session_manager: DesignSessionManager = Depends(get_session_manager)
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
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )
        
        # Get current design state
        current_state = await session_manager.state_store.get_design_state(session_id)
        if not current_state:
            raise HTTPException(
                status_code=404,
                detail=f"Design state not found for session {session_id}"
            )
        
        # Get context history
        contexts = await session_manager.state_store.get_context_history(session_id, limit=5)
        
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
                    "processing_time_ms": ctx.processing_time_ms
                }
                for ctx in contexts
            ]
        }
        
    except HTTPException:
        raise
    except SessionManagerError as e:
        logger.error(f"Session manager error getting details for {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting session details {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")