# app/core/models.py
"""
Core data models for the Stateful Iterative Design Engine.
These models define the structure for design sessions, states, and edit contexts.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid


class EditType(str, Enum):
    """Types of edits that can be applied to a design."""
    MODIFY = "modify"
    ADD = "add"
    REMOVE = "remove"
    STYLE = "style"
    LAYOUT = "layout"


class SessionStatus(str, Enum):
    """Status of a design session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class DesignState(BaseModel):
    """Represents a versioned state of a design."""
    wireframe_json: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int


class EditContext(BaseModel):
    """Context information for a design edit."""
    prompt: str
    edit_type: EditType
    target_elements: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: int = 0


class DesignSession(BaseModel):
    """Represents a design session with metadata and current state."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    initial_prompt: str
    current_version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    status: SessionStatus = SessionStatus.ACTIVE


class SessionMetadata(BaseModel):
    """Metadata about a design session stored in Redis."""
    session_id: str
    user_id: str
    initial_prompt: str
    current_version: int
    created_at: datetime
    last_activity: datetime
    status: SessionStatus
    total_edits: int = 0


class EditResult(BaseModel):
    """Result of applying an edit to a design."""
    success: bool
    new_version: int
    updated_wireframe: Dict[str, Any]
    changes_summary: str
    processing_time_ms: int
    errors: Optional[List[str]] = None


class SessionMetrics(BaseModel):
    """Analytics and metrics for a design session."""
    total_edits: int
    session_duration_minutes: int
    edit_types_distribution: Dict[EditType, int] = Field(default_factory=dict)
    average_processing_time_ms: float
    user_satisfaction_score: Optional[float] = None


# API Request/Response Models
class CreateSessionRequest(BaseModel):
    """Request to create a new design session."""
    prompt: str
    user_id: Optional[str] = None


class CreateSessionResponse(BaseModel):
    """Response after creating a design session."""
    session_id: str
    wireframe_json: Dict[str, Any]
    version: int


class EditSessionRequest(BaseModel):
    """Request to edit an existing design session."""
    edit_prompt: str


class EditSessionResponse(BaseModel):
    """Response after editing a design session."""
    session_id: str
    wireframe_json: Dict[str, Any]
    version: int
    changes_summary: str
    processing_time_ms: int


class SessionHistoryResponse(BaseModel):
    """Response containing session version history."""
    session_id: str
    versions: List[Dict[str, Any]]
    total_versions: int


class VersionMetadata(BaseModel):
    """Metadata for a design version."""
    version: int
    created_at: datetime
    changes_summary: str
    edit_type: EditType
    target_elements: List[str] = Field(default_factory=list)
    processing_time_ms: int
    content_hash: str
    compressed: bool = False


class VersionDiff(BaseModel):
    """Represents differences between two versions."""
    from_version: int
    to_version: int
    added_elements: List[Dict[str, Any]]
    removed_elements: List[Dict[str, Any]]
    modified_elements: List[Dict[str, Any]]
    metadata_changes: Dict[str, Any]
    summary: str


class IterativeDesignError(BaseModel):
    """Error response for iterative design operations."""
    error_code: str
    message: str
    recoverable: bool
    suggested_action: Optional[str] = None
    session_state: Optional[str] = None  # "preserved", "corrupted", "recovered"