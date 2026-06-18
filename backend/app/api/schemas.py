"""Pydantic schemas. Minimal — no ORM."""
from typing import Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


# ─── Clothing ──────────────────────────────────────────────────────────────────

class ClothingItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    name: str
    model_url: str
    category: str = "top"
    description: str = ""


class ClothingListResponse(BaseModel):
    items: list[ClothingItem]
    total: int


# ─── Measurements ──────────────────────────────────────────────────────────────

class MeasurementSession(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    created_at: datetime
    raw_data: dict | None = None       # original request payload
    coarse_data: dict | None = None    # frontend coarse measurement
    precise_data: dict | None = None   # AI server precise measurement
    status: str = "pending"            # pending | processing | done | error
    ai_task_id: str | None = None


class MeasurementCreate(BaseModel):
    raw_data: dict | None = None
    coarse_data: dict | None = None


# ─── AI Inference ──────────────────────────────────────────────────────────────

class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending | processing | done | error
    result: dict | None = None
    error: str | None = None


# ─── Uploads (Phase B) ─────────────────────────────────────────────────────────

class UploadItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    path: str                 # relative to backend/
    url: str                  # HTTP URL for client
    mime: str
    size: int
    created_at: datetime
    user_id: Optional[str] = None
    # Phase C: image normalization state
    normalize_status: Optional[str] = "NONE"   # NONE | QUEUED | NORMALIZING | NORMALIZED | FAILED
    normalized_path: Optional[str] = None
    normalize_task_id: Optional[str] = None


class NormalizeUpdate(BaseModel):
    """Callback payload the AI server PATCHes to the backend."""

    model_config = {"protected_namespaces": ()}

    status: Literal["QUEUED", "NORMALIZING", "NORMALIZED", "FAILED"]
    normalized_path: Optional[str] = None
    task_id: Optional[str] = None
    error: Optional[str] = None


# ─── Reconstructions (Phase B) ─────────────────────────────────────────────────

ReconMethod = Literal["smpl_fast", "smpl_multi"]
ReconStatus = Literal["pending", "processing", "done", "failed"]


class ReconstructionItem(BaseModel):
    model_config = {"protected_namespaces": ()}

    id: str
    upload_id: str
    method: ReconMethod
    glb_path: Optional[str] = None
    glb_url: Optional[str] = None
    metrics: Optional[dict] = None
    status: ReconStatus = "pending"
    ai_task_id: Optional[str] = None
    created_at: datetime
    # Adaptive polling hint (Phase F upgrade): when should the frontend
    # poll next? Server-side authority so the client doesn't spam the API
    # or wake the GPU worker unnecessarily.
    #   pending    -> 2000ms
    #   processing -> 4000ms
    #   near_done  -> 1000ms  (future: when metrics shows >80% progress)
    #   done/failed -> 0     (stop polling)
    next_poll_ms: int = 2000


class ReconstructionCreate(BaseModel):
    model_config = {"protected_namespaces": ()}

    upload_id: str
    method: ReconMethod = "smpl_fast"
    # Phase E: for method=smpl_multi, caller passes the N normalized crop
    # paths here. If empty, the service resolves the single upload's
    # normalized crop (smpl_fast behavior).
    image_urls: list[str] = Field(default_factory=list)


class ReconstructionUpdate(BaseModel):
    """Optional fields for status updates from Phase D AI server callbacks."""

    model_config = {"protected_namespaces": ()}

    status: ReconStatus
    glb_path: Optional[str] = None
    metrics: Optional[dict] = None
    ai_task_id: Optional[str] = None
