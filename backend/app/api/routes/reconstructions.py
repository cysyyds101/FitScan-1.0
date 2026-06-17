"""Reconstructions API.

- POST /api/reconstructions              create + immediately trigger AI server
- POST /api/reconstructions/{id}/trigger  explicit re-trigger (e.g. after AI server came back)
- POST /api/reconstructions/{id}/callback AI server PATCH with the result
- GET  /api/reconstructions/{id}         get one
- GET  /api/reconstructions              list (filter by ?upload_id=, ?limit=)
- PATCH /api/reconstructions/{id}        manual status update (admin)

Phase D adds the live AI server hookup via recon_service.create_and_trigger.
"""
from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import (
    ReconstructionCreate,
    ReconstructionItem,
    ReconstructionUpdate,
)
from app.services import recon_service, recon_storage

router = APIRouter()


@router.post("/reconstructions", response_model=ReconstructionItem, status_code=201)
def create_reconstruction(data: ReconstructionCreate, request: Request):
    """Create a reconstruction row AND trigger the AI server (Phase D).

    On success returns 201 with status=pending and (if AI server reachable)
    ai_task_id set. If AI server is down, the row is still created so the
    caller can retry trigger later via /trigger.
    """
    base = str(request.base_url).rstrip("/")
    # Placeholder {recon_id} is substituted by recon_service once it mints the id.
    callback = f"{base}/api/reconstructions/{{recon_id}}/callback"

    try:
        recon_service.create_and_trigger(
            upload_id=data.upload_id,
            method=data.method,
            backend_callback_url=callback,
            image_urls=data.image_urls or None,
        )
    except ValueError as e:
        msg = str(e)
        if "upload not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=409, detail=msg)

    # Refetch the freshly-created row (there should be exactly one)
    items = recon_storage.list_reconstructions(upload_id=data.upload_id, limit=1)
    if not items:
        raise HTTPException(status_code=500, detail="recon row missing after create_and_trigger")
    return items[0]


@router.post("/reconstructions/{recon_id}/trigger", response_model=ReconstructionItem)
def trigger_reconstruction(recon_id: str, request: Request):
    """Explicit re-trigger. Resets status to pending and re-enqueues."""
    recon = recon_storage.get_reconstruction(recon_id)
    if recon is None:
        raise HTTPException(status_code=404, detail=f"reconstruction '{recon_id}' not found")
    if recon.status == "processing":
        raise HTTPException(status_code=409, detail="already processing")

    base = str(request.base_url).rstrip("/")
    callback = f"{base}/api/reconstructions/{recon_id}/callback"
    try:
        recon_service.create_and_trigger(
            upload_id=recon.upload_id,
            method=recon.method,
            backend_callback_url=callback,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return recon_storage.get_reconstruction(recon_id)  # type: ignore[return-value]


@router.post("/reconstructions/{recon_id}/callback", response_model=ReconstructionItem)
def ai_callback(recon_id: str, data: ReconstructionUpdate):
    """AI server PATCHes this with the result of the SMPL worker."""
    try:
        return recon_service.apply_ai_callback(
            recon_id=recon_id,
            status=data.status,
            glb_path=data.glb_path,
            metrics=data.metrics,
            ai_task_id=data.ai_task_id,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)


@router.get("/reconstructions/{recon_id}", response_model=ReconstructionItem)
def get_reconstruction(recon_id: str):
    item = recon_storage.get_reconstruction(recon_id)
    if item is None:
        raise HTTPException(status_code=404, detail=f"reconstruction '{recon_id}' not found")
    return item


@router.get("/reconstructions", response_model=list[ReconstructionItem])
def list_reconstructions(limit: int = 20, upload_id: str | None = None):
    return recon_storage.list_reconstructions(limit=limit, upload_id=upload_id)


@router.patch("/reconstructions/{recon_id}", response_model=ReconstructionItem)
def update_reconstruction(recon_id: str, data: ReconstructionUpdate):
    """Manual admin override. AI server should use /callback instead."""
    try:
        item = recon_storage.update_status(
            recon_id=recon_id,
            status=data.status,
            glb_path=data.glb_path,
            metrics=data.metrics,
            ai_task_id=data.ai_task_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if item is None:
        raise HTTPException(status_code=404, detail=f"reconstruction '{recon_id}' not found")
    return item
