"""Reconstruction storage service.

Stores AI-server reconstruction results: which upload they were built
from, which method (smpl_fast | smpl_multi), where the GLB landed,
and the status of the (Phase D) AI inference job.

Phase B does NOT call the AI server — it only persists the metadata.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.api.schemas import ReconstructionItem
from app.services import storage

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
RECON_DIR = BACKEND_ROOT / "data" / "reconstructions"

ALLOWED_METHODS = ("smpl_fast", "smpl_multi")
ALLOWED_STATUSES = ("pending", "processing", "done", "failed")


def _ensure_dir() -> None:
    RECON_DIR.mkdir(parents=True, exist_ok=True)


def create_reconstruction(
    upload_id: str,
    method: str,
) -> ReconstructionItem:
    """Create a pending reconstruction row.

    Raises ValueError on bad method or unknown upload.
    """
    if method not in ALLOWED_METHODS:
        raise ValueError(f"unsupported method: {method!r} (allowed: {ALLOWED_METHODS})")
    # Verify upload exists (FK enforced but we want a clean 404 path)
    conn = storage.get_db()
    row = conn.execute("SELECT id FROM uploads WHERE id = ?", (upload_id,)).fetchone()
    if not row:
        raise ValueError(f"upload not found: {upload_id}")

    _ensure_dir()
    recon_id = f"rec-{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO reconstructions (id, upload_id, method, status, created_at) "
        "VALUES (?, ?, ?, 'pending', ?)",
        (recon_id, upload_id, method, now),
    )
    conn.commit()
    return get_reconstruction(recon_id)  # type: ignore[return-value]


def update_status(
    recon_id: str,
    status: str,
    glb_path: str | None = None,
    metrics: dict | None = None,
    ai_task_id: str | None = None,
) -> ReconstructionItem | None:
    """Update the lifecycle fields of a reconstruction row.

    Any field passed as None is left unchanged. Returns the updated item,
    or None if the id doesn't exist.
    """
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"invalid status: {status!r}")

    conn = storage.get_db()
    existing = conn.execute(
        "SELECT * FROM reconstructions WHERE id = ?", (recon_id,)
    ).fetchone()
    if not existing:
        return None

    # Phase F: when a GLB path arrives (typically on status=done), register
    # it in the asset registry so /assets/glb/{id} can serve it. This makes
    # the AI server -> backend handoff explicit and uniform.
    if glb_path is not None and status == "done":
        try:
            from app.services import asset_service
            asset_service.register(
                absolute_path=glb_path,
                kind="glb",
                owner_id=recon_id,
            )
        except FileNotFoundError:
            # The AI server told us about a file that doesn't exist yet.
            # We still record the glb_path in the recon row (so the URL
            # resolution will hit 410 Gone until the file lands), but
            # the asset registry stays empty for this id.
            pass
        except Exception as e:
            import logging
            logging.warning(f"[recon_storage] asset register failed for {recon_id}: {e}")

    sets: list[str] = ["status = ?"]
    vals: list = [status]
    if glb_path is not None:
        sets.append("glb_path = ?")
        vals.append(glb_path)
    if metrics is not None:
        sets.append("metrics_json = ?")
        vals.append(json.dumps(metrics))
    if ai_task_id is not None:
        sets.append("ai_task_id = ?")
        vals.append(ai_task_id)
    vals.append(recon_id)
    conn.execute(
        f"UPDATE reconstructions SET {', '.join(sets)} WHERE id = ?",
        tuple(vals),
    )
    conn.commit()
    return get_reconstruction(recon_id)


def get_reconstruction(recon_id: str) -> ReconstructionItem | None:
    conn = storage.get_db()
    row = conn.execute(
        "SELECT * FROM reconstructions WHERE id = ?", (recon_id,)
    ).fetchone()
    if not row:
        return None
    d = dict(row)
    return ReconstructionItem(
        id=d["id"],
        upload_id=d["upload_id"],
        method=d["method"],
        glb_path=d["glb_path"],
        glb_url=_to_url(d["glb_path"], recon_id=d["id"]),
        metrics=json.loads(d["metrics_json"]) if d["metrics_json"] else None,
        status=d["status"],
        ai_task_id=d["ai_task_id"],
        created_at=datetime.fromisoformat(d["created_at"]),
        next_poll_ms=_next_poll_ms(d["status"]),
    )


def list_reconstructions(
    limit: int = 20,
    upload_id: str | None = None,
) -> list[ReconstructionItem]:
    conn = storage.get_db()
    if upload_id is not None:
        rows = conn.execute(
            "SELECT id FROM reconstructions WHERE upload_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (upload_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id FROM reconstructions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    out: list[ReconstructionItem] = []
    for r in rows:
        item = get_reconstruction(r["id"])
        if item is not None:
            out.append(item)
    return out


def _to_url(glb_path: str | None, recon_id: str | None = None) -> str | None:
    """Resolve the canonical URL for a recon's GLB.

    Phase F architecture: ALWAYS go through the asset registry. The
    /assets/glb/{id} endpoint is the single source of truth for
    frontend URLs; the absolute path on disk stays private to backend.

    recon_id is preferred (set by the caller). Falls back to inferring
    it from the GLB filename (works because AI server worker writes
    files as <recon_id>.glb).
    """
    if not glb_path:
        return None
    from app.services import asset_service  # local to avoid circular
    if recon_id is None:
        recon_id = Path(glb_path).stem
    url = asset_service.public_url_for_owner(recon_id, kind="glb")
    if url is not None:
        return url
    # No registration yet (e.g. callback arrived but file not on disk).
    # Return a placeholder so callers can show "preparing" without
    # breaking the JSON schema.
    return f"/assets/glb/_pending_{recon_id}"


def _next_poll_ms(status: str) -> int:
    """Adaptive polling hint. See ReconstructionItem.next_poll_ms docstring.

    PENDING  -> 2000ms (just created, AI server may not have picked up yet)
    PROCESSING -> 4000ms (worker is running, less urgency)
    DONE / FAILED -> 0ms (stop polling)
    """
    return {
        "pending": 2000,
        "processing": 4000,
        "done": 0,
        "failed": 0,
    }.get(status, 2000)
