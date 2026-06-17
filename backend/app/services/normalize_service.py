"""Normalize orchestration (Phase C).

Connects dev-machine uploads to AI-server normalize workers:
    1. Validate the upload exists + has a file we can resolve.
    2. Mark uploads row as QUEUED.
    3. POST AI server /infer/normalize with the source path + a
       backend_callback URL pointing at our PATCH endpoint.
    4. Return the AI server's task_id so the caller can poll if needed.

The completion flow is one-way: AI server PATCHes
/api/uploads/{id}/normalized with the result. That endpoint (in
routes/uploads.py) calls set_normalize_result() here.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from app.api.schemas import UploadItem
from app.services import storage, upload_storage
from app.services.ai_client import ai_client

logger = logging.getLogger(__name__)

ALLOWED_NORMALIZE_STATUSES = {"QUEUED", "NORMALIZING", "NORMALIZED", "FAILED"}


def _row_to_item(d: dict) -> UploadItem:
    abs_path = upload_storage.BACKEND_ROOT / d["path"] if d.get("path") else None
    url = f"/static/uploads/{abs_path.name}" if abs_path else ""
    return UploadItem(
        id=d["id"],
        path=d.get("path", ""),
        url=url,
        mime=d.get("mime", ""),
        size=d.get("size", 0),
        created_at=d["created_at"] if isinstance(d["created_at"], object) else d["created_at"],
        user_id=d.get("user_id"),
        normalize_status=d.get("normalize_status") or "NONE",
        normalized_path=d.get("normalized_path"),
        normalize_task_id=d.get("normalize_task_id"),
    )


def get_upload_row(upload_id: str) -> dict | None:
    conn = storage.get_db()
    row = conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
    return dict(row) if row else None


def trigger_normalize(
    upload_id: str,
    backend_callback_url: Optional[str] = None,
) -> dict:
    """Mark the upload as QUEUED and enqueue a normalize task on AI server.

    Returns the AI server's enqueue response (includes task_id).
    Raises ValueError on bad inputs.
    """
    row = get_upload_row(upload_id)
    if row is None:
        raise ValueError(f"upload not found: {upload_id}")

    current = row.get("normalize_status") or "NONE"
    if current in ("QUEUED", "NORMALIZING"):
        raise ValueError(f"normalize already in progress (status={current})")

    abs_path = upload_storage.BACKEND_ROOT / row["path"]
    if not abs_path.exists():
        raise ValueError(f"source file missing on disk: {row['path']}")

    # Mark as QUEUED BEFORE enqueueing (so a worker PATCH that arrives early
    # can correlate). We do this synchronously; if AI server is down the
    # caller will see the ERROR status and the row stays QUEUED — easy to
    # detect and reset.
    conn = storage.get_db()
    conn.execute(
        "UPDATE uploads SET normalize_status = 'QUEUED', normalize_task_id = NULL "
        "WHERE id = ?",
        (upload_id,),
    )
    conn.commit()

    # Build payload: prefer absolute path so AI server can read directly
    # (in prod, both processes share a volume at backend/data/uploads).
    return ai_client.normalize_sync(
        upload_id=upload_id,
        image_url=str(abs_path),
        backend_callback=backend_callback_url,
    )


def set_normalize_result(
    upload_id: str,
    status: str,
    normalized_path: Optional[str] = None,
    task_id: Optional[str] = None,
) -> UploadItem:
    """Called by the AI server PATCH callback. Updates uploads row."""
    if status not in ALLOWED_NORMALIZE_STATUSES:
        raise ValueError(f"invalid status: {status!r}")

    conn = storage.get_db()
    # Only set fields that are provided
    sets = ["normalize_status = ?"]
    vals: list = [status]
    if normalized_path is not None:
        sets.append("normalized_path = ?")
        vals.append(normalized_path)
    if task_id is not None:
        sets.append("normalize_task_id = ?")
        vals.append(task_id)
    vals.append(upload_id)
    conn.execute(
        f"UPDATE uploads SET {', '.join(sets)} WHERE id = ?",
        tuple(vals),
    )
    conn.commit()
    row = get_upload_row(upload_id)
    if row is None:
        raise ValueError(f"upload vanished during update: {upload_id}")
    return _row_to_item(row)


def _ensure_ai_client_has_sync():
    """AIClient was originally async; tests + this sync route need a sync
    shim. We attach one to the singleton lazily.
    """
    if not hasattr(ai_client, "normalize_sync"):
        import asyncio

        def _normalize_sync(upload_id, image_url, backend_callback):
            return asyncio.run(
                ai_client.normalize(
                    upload_id=upload_id,
                    image_url=image_url,
                    backend_callback=backend_callback,
                )
            )

        ai_client.normalize_sync = _normalize_sync  # type: ignore[attr-defined]


_ensure_ai_client_has_sync()
