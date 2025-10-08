# app/api/v1/endpoints.py
from fastapi import APIRouter, HTTPException
from celery.result import AsyncResult

from app.core.services.orchestrator import start_generation_pipeline  # keeps old flow working
from app.api.v1.schemas import (
    GenerationRequest, GenerationResponse, TaskStatusResponse,
    WireframeResponse, GenerateCodeRequest, GenerateCodeResponse
)

# import the Celery tasks directly
from app.tasks.pipeline import (
    generate_wireframe_json,
    generate_react_code,
    validate_code_ast
)

# Import iterative design router
from app.api.v1.iterative_design import router as iterative_router

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
        task = generate_wireframe_json.apply_async(args=[request.prompt], task_id=task_id)
        
        # Shorter timeout to prevent long waits
        json_output = task.get(timeout=180)  # Reduced from 300 to 180 seconds
        return {"layout_json": json_output}
    except Exception as e:
        # Revoke the task if it fails to prevent redelivery
        if 'task' in locals():
            task.revoke(terminate=True)
        raise HTTPException(status_code=500, detail=f"wireframe generation failed: {e}")


@router.post("/generate-code", response_model=GenerateCodeResponse)
def generate_code_from_json(request: GenerateCodeRequest):
    """
    Stage 2: Given the wireframe JSON, generate React code and validate it.
    Runs on Celery worker(s); we block until finished for a single response.
    """
    try:
        # Task 2 — generate React code
        code_task = generate_react_code.apply_async(args=[request.layout_json])
        react_code: str = code_task.get(timeout=300)

        # Task 3 — validate AST
        val_task = validate_code_ast.apply_async(args=[react_code])
        validation_result = val_task.get(timeout=120) or {}

        status = validation_result.get("validation_status", "UNKNOWN")
        errors = validation_result.get("errors", [])

        return {
            "react_code": react_code,
            "validation_status": status,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"code generation failed: {e}")
