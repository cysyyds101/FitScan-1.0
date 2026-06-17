"""Reconstructions API.

- POST /api/reconstructions              create a pending reconstruction
- GET  /api/reconstructions/{id}         get one
- GET  /api/reconstructions              list (filter by ?upload_id=, ?limit=)
- PATCH /api/reconstructions/{id}        update status / glb_path / metrics
                                          (used by Phase D AI server callbacks)

Phase B only persists metadata. The AI server call happens in Phase D.
"""
from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    ReconstructionCreate,
    ReconstructionItem,
    ReconstructionUpdate,
)
from app.services import recon_storage

router = APIRouter()


@router.post("/reconstructions", response_model=ReconstructionItem, status_code=201)
def create_reconstruction(data: ReconstructionCreate):
    try:
        return recon_storage.create_reconstruction(
            upload_id=data.upload_id,
            method=data.method,
        )
    except ValueError as e:
        # Distinguish 404 (upload not found) from 400 (bad method)
        msg = str(e)
        if "upload not found" in msg:
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
