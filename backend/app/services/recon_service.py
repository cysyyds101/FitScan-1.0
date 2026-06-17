"""Reconstruction orchestration (Phase D).

Workflow:
    1. create_and_trigger(upload_id, method):
        - verify upload exists + has a normalized crop (or raw image)
        - INSERT reconstructions row, status=pending
        - call ai_client.smpl_fast_sync(...) (or smpl_multi) -> task_id
        - update row with ai_task_id
        - return the row

    2. apply_ai_callback(recon_id, status, glb_path, metrics):
        - called by the AI server via PATCH /api/reconstructions/{id}/callback
        - update row: glb_path, metrics_json, status

    Phase D NOTE: no actual GPU. ai_client.smpl_fast_sync is sync shim
    around the async httpx call. The dev machine can be started without
    the AI server up; the route returns 502 (caller can poll later).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.api.schemas import ReconstructionItem
from app.services import recon_storage, storage, upload_storage
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)


def _resolve_normalized_path(upload_id: str) -> Optional[Path]:
    """Locate the normalized crop for this upload.

    Search order:
        1. uploads.normalized_path (set by normalize callback)
        2. ai_server/data/normalized/<upload_id>.jpg (in shared prod volume)
    """
    row = storage.get_db().execute(
        "SELECT normalized_path FROM uploads WHERE id = ?", (upload_id,)
    ).fetchone()
    if row and row["normalized_path"]:
        p = Path(row["normalized_path"])
        if p.exists():
            return p

    # Standard prod location (dev machine and AI server share via $AI_NORMALIZED_DIR)
    ai_dir = Path(__import__("os").environ.get("AI_NORMALIZED_DIR", ""))
    if ai_dir:
        cand = ai_dir / f"{upload_id}.jpg"
        if cand.exists():
            return cand
    return None


def create_and_trigger(
    upload_id: str,
    method: str = "smpl_fast",
    backend_callback_url: Optional[str] = None,
    image_urls: Optional[list] = None,
) -> dict:
    """Create a recon row AND immediately enqueue the SMPL job on the AI server.

    Returns the AI server's enqueue response (dict with task_id) plus the
    created recon_id under key 'recon_id' for the caller's convenience.

    If backend_callback_url is provided, we substitute the placeholder
    ``{recon_id}`` with the freshly-created recon id. This lets the caller
    pass something like ``http://dev/api/reconstructions/{recon_id}/callback``
    without knowing the id in advance.

    Hybrid routing (Phase E):
        0 views  -> ValueError ("at least one image is required")
        1 view   -> auto-route to smpl_fast
        2 views  -> warn, route to smpl_fast (multi-view needs >=3)
        >=3 views -> smpl_multi (capped at 8)
    """
    image_urls = list(image_urls or [])
    if upload_storage.get_upload(upload_id) is None:
        raise ValueError(f"upload not found: {upload_id}")
    if method not in ("smpl_fast", "smpl_multi"):
        raise ValueError(f"unsupported method: {method!r}")

    # Hybrid routing
    n = len(image_urls)
    if method == "smpl_multi":
        if n == 0:
            raise ValueError("at least one image is required for smpl_multi")
        if n == 1:
            logger.info(f"[recon_service] {n} view -> auto-route to smpl_fast")
            method = "smpl_fast"
        elif n == 2:
            logger.warning(
                f"[recon_service] {n} views -> smpl_multi needs >=3; "
                f"falling back to smpl_fast"
            )
            method = "smpl_fast"
        elif n > 8:
            raise ValueError(f"too many views: {n} (max 8)")
    # smpl_fast with n==0 is fine — we resolve from upload's normalized crop

    # Insert row at status=pending
    recon = recon_storage.create_reconstruction(upload_id=upload_id, method=method)
    recon_id = recon.id

    # Substitute placeholder if any
    if backend_callback_url and "{recon_id}" in backend_callback_url:
        callback = backend_callback_url.replace("{recon_id}", recon_id)
    else:
        callback = backend_callback_url

    # Resolve a single source path for the smpl_fast path
    single_src: Optional[str] = None
    if method == "smpl_fast":
        if n == 0:
            # Caller didn't provide image_urls; use the upload's normalized
            # crop or the raw upload path as a fallback.
            src = _resolve_normalized_path(upload_id)
            if src is None:
                up_row = storage.get_db().execute(
                    "SELECT path FROM uploads WHERE id = ?", (upload_id,)
                ).fetchone()
                if up_row:
                    cand = upload_storage.BACKEND_ROOT / up_row["path"]
                    if cand.exists():
                        src = cand
            single_src = str(src) if src else None
        else:
            single_src = image_urls[0]

    # Pick the right sync shim
    if method == "smpl_fast":
        ai_resp = ai_client.smpl_fast_sync(
            upload_id=upload_id,
            image_url=single_src,
            backend_callback=callback,
            recon_id=recon_id,
        )
    else:
        ai_resp = ai_client.smpl_multi_sync(
            upload_id=upload_id,
            image_url=None,
            image_urls=image_urls,
            backend_callback=callback,
            recon_id=recon_id,
        )

    if ai_resp and ai_resp.get("task_id"):
        # Persist ai_task_id
        storage.get_db().execute(
            "UPDATE reconstructions SET ai_task_id = ? WHERE id = ?",
            (ai_resp["task_id"], recon_id),
        )
        storage.get_db().commit()
    return ai_resp  # raw AI server response


def apply_ai_callback(
    recon_id: str,
    status: str,
    glb_path: Optional[str] = None,
    metrics: Optional[dict] = None,
    ai_task_id: Optional[str] = None,
) -> ReconstructionItem:
    """Update the recon row from an AI server PATCH."""
    updated = recon_storage.update_status(
        recon_id=recon_id,
        status=status,
        glb_path=glb_path,
        metrics=metrics,
        ai_task_id=ai_task_id,
    )
    if updated is None:
        raise ValueError(f"reconstruction not found: {recon_id}")
    return updated


# ─── Sync shim helper (parallel to normalize_service) ───────────────────────

def _ensure_ai_client_sync():
    """Attach sync shims to the ai_client singleton.

    We do this once at import time so routes can just call
    `ai_client.smpl_fast_sync(...)`.
    """
    import asyncio

    if not hasattr(ai_client, "smpl_fast_sync"):
        def _sync(upload_id, image_url, backend_callback, recon_id):
            return asyncio.run(
                ai_client.smpl_fast(
                    upload_id=upload_id,
                    image_url=image_url,
                    backend_callback=backend_callback,
                    recon_id=recon_id,
                )
            )
        ai_client.smpl_fast_sync = _sync  # type: ignore[attr-defined]

    if not hasattr(ai_client, "smpl_multi_sync"):
        def _sync(upload_id, image_url, backend_callback, recon_id, image_urls=None):
            return asyncio.run(
                ai_client.smpl_multi(
                    upload_id=upload_id,
                    image_url=image_url,
                    image_urls=image_urls,
                    backend_callback=backend_callback,
                    recon_id=recon_id,
                )
            )
        ai_client.smpl_multi_sync = _sync  # type: ignore[attr-defined]


_ensure_ai_client_sync()
