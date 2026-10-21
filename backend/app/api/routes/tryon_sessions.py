"""Try-on Sessions API routes.

- POST /api/tryon_sessions  — save a try-on session
- GET  /api/tryon_sessions  — list recent sessions (limit=20)
"""
from fastapi import APIRouter, HTTPException

from app.api.schemas import TryonSessionCreate, TryonSessionItem, TryonSessionListResponse
from app.services import storage

router = APIRouter()


@router.post("/tryon_sessions", response_model=TryonSessionItem, status_code=201)
def create_tryon_session(payload: TryonSessionCreate):
    """Persist a try-on session.

    Stores the clothing_id, optional avatar GLB URL, and the full transform
    (position / rotation / scale) so the session can be restored later.
    """
    item = storage.create_tryon_session(
        clothing_id=payload.clothing_id,
        avatar_glb_url=payload.avatar_glb_url,
        transform=payload.transform.model_dump(),
    )
    return item


@router.get("/tryon_sessions", response_model=TryonSessionListResponse)
def list_tryon_sessions(limit: int = 20):
    """Return the most recent try-on sessions, newest first."""
    items = storage.list_tryon_sessions(limit=limit)
    return TryonSessionListResponse(items=items, total=len(items))
