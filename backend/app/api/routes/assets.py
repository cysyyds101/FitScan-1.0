"""Asset serving API.

    GET /assets/{kind}/{id}    serve a registered asset (e.g. GLB)

The route resolves the asset_id via asset_service, then streams the file
from its absolute path. It does NOT depend on a fixed StaticFiles mount
because assets may live on a shared volume whose root is only known to
the backend (the AI server writes the file, the backend owns the index).

This single endpoint is the canonical URL space the frontend uses:
    /assets/glb/{id}            reconstructed body model
    /assets/normalized/{id}     normalized crop (future)
    /assets/metrics/{id}        metrics JSON (future)
    /assets/texture/{id}        texture map (future)

Frontends MUST go through this endpoint, never the underlying /static/...
mount, because the asset registry may point at a file path that's not
under any StaticFiles directory.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import asset_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/assets/{kind}/{asset_id}")
def get_asset(kind: str, asset_id: str):
    """Stream a registered asset by kind + id."""
    if kind not in asset_service.ALLOWED_KINDS:
        raise HTTPException(
            status_code=404,
            detail=f"unsupported asset kind: {kind!r} (allowed: {asset_service.ALLOWED_KINDS})",
        )

    asset = asset_service.lookup(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"asset {asset_id} not found")
    if asset["kind"] != kind:
        raise HTTPException(
            status_code=400,
            detail=f"asset {asset_id} is kind={asset['kind']!r}, not {kind!r}",
        )

    abs_path = Path(asset["absolute_path"])
    if not abs_path.exists():
        # AI server hasn't written it yet, or shared volume is unmounted.
        raise HTTPException(
            status_code=410,
            detail=f"asset {asset_id} file missing on disk: {abs_path}",
        )

    return FileResponse(
        path=str(abs_path),
        media_type=asset["mime"],
        filename=abs_path.name,
    )
