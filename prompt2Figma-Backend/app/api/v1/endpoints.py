# app/api/v1/endpoints.py
from typing import Optional

# Import iterative design router
from app.api.v1.iterative_design import router as iterative_router
from app.api.v1.schemas import (GenerateCodeRequest, GenerateCodeResponse, GenerationRequest,
                                GenerationResponse, TaskStatusResponse, WireframeResponse)
from app.core.services.orchestrator import start_generation_pipeline  # keeps old flow working
# import the Celery tasks directly
from app.tasks.pipeline import generate_react_code, generate_wireframe_json, validate_code_ast
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException

router = APIRouter()

# Include iterative design endpoints
router.include_router(iterative_router)


# ----- existing endpoints (unchanged) -----
@router.post("/generate", response_model=GenerationResponse, status_code=202)
def generate_code(request: GenerationRequest):
    task_result = start_generation_pipeline(prompt=request.prompt)
    return {"task_id": task_result.id}


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    task_result = AsyncResult(id=task_id)
    response_data = {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    }
    return response_data


# ====== NEW FLOW: split pipeline ======


@router.post("/generate-wireframe", response_model=WireframeResponse)
def generate_wireframe(request: GenerationRequest):
    """
    Stage 1: Only generate the wireframe JSON for a given prompt.
    Runs on Celery worker; we block until the worker finishes.
    """
    try:
        # Use a unique task ID to prevent duplicate processing
        task_id = f"wireframe_{hash(request.prompt)}_{int(__import__('time').time())}"
        task = generate_wireframe_json.apply_async(
            args=[request.prompt], task_id=task_id
        )

        # Shorter timeout to prevent long waits
        json_output = task.get(timeout=180)  # Reduced from 300 to 180 seconds
        return {"layout_json": json_output}
    except Exception as e:
        # Revoke the task if it fails to prevent redelivery
        if "task" in locals():
            task.revoke(terminate=True)
        raise HTTPException(status_code=500, detail=f"wireframe generation failed: {e}")


@router.post("/generate-code", response_model=GenerateCodeResponse)
async def generate_code_from_json(request: GenerateCodeRequest):
    """
    Stage 2: Given the wireframe JSON, generate React code and validate it.
    Runs on Celery worker(s); we block until finished for a single response.

    Supports both direct JSON input and session-based input for iterative design integration.
    If session_id is provided, the wireframe will be fetched from the session state.

    Requirements: 5.2, 5.3
    """
    try:
        layout_json = request.layout_json
        session_id = request.session_id
        version = request.version

        # If session_id is provided, fetch the wireframe from session state
        if session_id:
            from app.core.config import settings
            from app.core.state_store import RedisStateStore

            # Get state store instance
            state_store = RedisStateStore(settings.REDIS_STATE_STORE_URL)
            await state_store.connect()

            try:
                # Fetch design state from session
                design_state = await state_store.get_design_state(session_id, version)

                if not design_state:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Design state not found for session {session_id}"
                        + (f" version {version}" if version else ""),
                    )

                # Use wireframe from session state
                layout_json = design_state.wireframe_json
                version = design_state.version

                # Mark session as transitioning to code generation
                from app.core.session_manager import DesignSessionManager

                session_manager = DesignSessionManager(state_store)
                await session_manager.complete_session(session_id)

            finally:
                await state_store.disconnect()

        # Task 2 — generate React code
        code_task = generate_react_code.apply_async(args=[layout_json])
        react_code: str = code_task.get(timeout=300)

        # Task 3 — validate AST
        val_task = validate_code_ast.apply_async(args=[react_code])
        validation_result = val_task.get(timeout=120) or {}

        status = validation_result.get("validation_status", "UNKNOWN")
        errors = validation_result.get("errors", [])

        return {
            "react_code": react_code,
            "validation_status": status,
            "errors": errors,
            "session_id": session_id,
            "version": version,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"code generation failed: {e}")


@router.post(
    "/design-sessions/{session_id}/generate-code", response_model=GenerateCodeResponse
)
async def generate_code_from_session(session_id: str, version: Optional[int] = None):
    """
    Generate React code from a design session's current or specified version.

    This is a convenience endpoint that combines session state retrieval and code generation.
    It automatically uses the latest version if no version is specified.

    Requirements: 5.2, 5.3
    """
    try:
        from app.core.config import settings
        from app.core.session_manager import DesignSessionManager
        from app.core.state_store import RedisStateStore

        # Get state store and session manager
        state_store = RedisStateStore(settings.REDIS_STATE_STORE_URL)
        await state_store.connect()

        try:
            session_manager = DesignSessionManager(state_store)

            # Verify session exists
            session = await session_manager.get_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=404, detail=f"Session {session_id} not found or expired"
                )

            # Get design state (use current version if not specified)
            target_version = version if version is not None else session.current_version
            design_state = await state_store.get_design_state(
                session_id, target_version
            )

            if not design_state:
                raise HTTPException(
                    status_code=404,
                    detail=f"Design state not found for session {session_id} version {target_version}",
                )

            # Generate React code
            code_task = generate_react_code.apply_async(
                args=[design_state.wireframe_json]
            )
            react_code: str = code_task.get(timeout=300)

            # Validate AST
            val_task = validate_code_ast.apply_async(args=[react_code])
            validation_result = val_task.get(timeout=120) or {}

            status = validation_result.get("validation_status", "UNKNOWN")
            errors = validation_result.get("errors", [])

            # Mark session as completed (transitioning to code generation)
            await session_manager.complete_session(session_id)

            return {
                "react_code": react_code,
                "validation_status": status,
                "errors": errors,
                "session_id": session_id,
                "version": target_version,
            }

        finally:
            await state_store.disconnect()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"code generation from session failed: {e}"
        )
