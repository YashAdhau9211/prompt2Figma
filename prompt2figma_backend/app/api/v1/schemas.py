# app/api/v1/schemas.py
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel

# already present in your code:
class GenerationRequest(BaseModel):
    prompt: str

class GenerationResponse(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None


# ✨ NEW: used by /generate-wireframe
class WireframeResponse(BaseModel):
    layout_json: Dict[str, Any]


# ✨ NEW: used by /generate-code
class GenerateCodeRequest(BaseModel):
    layout_json: Dict[str, Any]


class GenerateCodeResponse(BaseModel):
    react_code: str
    validation_status: Literal["SUCCESS", "FAILURE", "PENDING", "UNKNOWN"] = "UNKNOWN"
    errors: Optional[List[str]] = []
