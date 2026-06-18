"""Asset registry (Phase F architecture upgrade).

Ownership rule (per user feedback):
    AI server  = writer   (writes GLB to shared disk, no DB knowledge)
    Backend    = registry owner (this module owns the asset -> URL mapping)
    Frontend   = consumer (only ever calls /assets/glb/{id})

This module:
    - Persists `asset_id -> {absolute_path, kind, mime, size, ...}` in SQLite
    - Provides register / lookup / list / unregister
    - The /assets/glb/{id} route uses lookup() to resolve the real path and
      stream the file. The AI server does NOT need to know about this layer.

Why a separate table (not just `reconstructions.glb_path`):
    - Future asset kinds: clothing models, normalized crops, segmentation maps
    - Multiple assets per recon (e.g. 1 GLB + 1 texture + 1 metrics JSON)
    - Decoupled: recon table tracks lifecycle, asset table tracks file refs
    - Uniform URL space for the frontend: /assets/{kind}/{id}
"""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services import storage

logger = logging.getLogger(__name__)

ALLOWED_KINDS = ("glb", "normalized", "metrics", "texture")
ALLOWED_MIMES = {
    "glb": "model/gltf-binary",
    "normalized": "image/jpeg",
    "metrics": "application/json",
    "texture": "image/png",
}


def _ensure_schema() -> None:
    """Create the assets table if it doesn't exist (idempotent)."""
    conn = storage.get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS assets (
            id            TEXT PRIMARY KEY,
            kind          TEXT NOT NULL,
            owner_id      TEXT,             -- e.g. recon_id, upload_id, clothing_id
            absolute_path TEXT NOT NULL,
            mime          TEXT NOT NULL,
            size_bytes    INTEGER,
            registered_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_assets_kind_owner ON assets(kind, owner_id);
        CREATE INDEX IF NOT EXISTS idx_assets_owner      ON assets(owner_id);
    """)
    conn.commit()


def register(
    absolute_path: str,
    kind: str = "glb",
    owner_id: Optional[str] = None,
    mime: Optional[str] = None,
) -> str:
    """Register an asset written by the AI server (or any other writer).

    Returns the asset_id (caller stores this in their own table for
    cross-reference; the route resolves the URL by asset_id).

    The file at absolute_path must exist and be readable; we record its
    size for downstream bandwidth hints. Idempotent by absolute_path:
    a re-registration overwrites the row.
    """
    if kind not in ALLOWED_KINDS:
        raise ValueError(f"unsupported asset kind: {kind!r} (allowed: {ALLOWED_KINDS})")

    p = Path(absolute_path)
    if not p.exists():
        raise FileNotFoundError(f"asset path does not exist: {absolute_path}")

    mime = mime or ALLOWED_MIMES[kind]
    size = p.stat().st_size
    now = datetime.utcnow().isoformat()
    asset_id = f"asset-{uuid.uuid4().hex[:12]}"

    _ensure_schema()
    conn = storage.get_db()
    # Idempotent: if the same absolute_path is registered, reuse the id.
    existing = conn.execute(
        "SELECT id FROM assets WHERE absolute_path = ?", (str(p),)
    ).fetchone()
    if existing:
        asset_id = existing["id"]
        conn.execute(
            "UPDATE assets SET kind=?, owner_id=?, mime=?, size_bytes=?, registered_at=? "
            "WHERE id = ?",
            (kind, owner_id, mime, size, now, asset_id),
        )
    else:
        conn.execute(
            "INSERT INTO assets (id, kind, owner_id, absolute_path, mime, size_bytes, registered_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (asset_id, kind, owner_id, str(p), mime, size, now),
        )
    conn.commit()
    logger.info(f"[asset_service] registered {asset_id} kind={kind} owner={owner_id} path={p}")
    return asset_id


def lookup(asset_id: str) -> Optional[dict]:
    """Return the asset row (with absolute_path) or None."""
    _ensure_schema()
    conn = storage.get_db()
    row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    return dict(row) if row else None


def lookup_by_owner(owner_id: str, kind: str = "glb") -> Optional[dict]:
    """Resolve the most recent asset for an owner_id (e.g. recon_id)."""
    _ensure_schema()
    conn = storage.get_db()
    row = conn.execute(
        "SELECT * FROM assets WHERE owner_id = ? AND kind = ? "
        "ORDER BY registered_at DESC LIMIT 1",
        (owner_id, kind),
    ).fetchone()
    return dict(row) if row else None


def list_for_owner(owner_id: str) -> list[dict]:
    _ensure_schema()
    conn = storage.get_db()
    rows = conn.execute(
        "SELECT * FROM assets WHERE owner_id = ? ORDER BY registered_at DESC",
        (owner_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def public_url_for_owner(owner_id: str, kind: str = "glb") -> Optional[str]:
    """The canonical URL the frontend should use. Returns None if not registered."""
    asset = lookup_by_owner(owner_id, kind)
    if asset is None:
        return None
    return f"/assets/{kind}/{asset['id']}"


def public_url_for_recon(recon_id: str) -> Optional[str]:
    """Convenience: URL for the GLB of a given reconstruction."""
    return public_url_for_owner(recon_id, kind="glb")


def unregister(asset_id: str) -> bool:
    _ensure_schema()
    conn = storage.get_db()
    cur = conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    return cur.rowcount > 0


def get_absolute_path(asset_id: str) -> Optional[Path]:
    """Resolve an asset_id to its on-disk path. None if not found."""
    asset = lookup(asset_id)
    if asset is None:
        return None
    p = Path(asset["absolute_path"])
    return p if p.exists() else None
