"""Upload storage service.

Saves uploaded files to disk under backend/data/uploads/ and persists
metadata (path / mime / size / user_id / created_at) to the uploads table.

DB rows store the *relative* path (relative to backend/) so the tree can
be moved without breaking references.
"""
from __future__ import annotations

import shutil
import uuid
from datetime import datetime
from pathlib import Path

from app.api.schemas import UploadItem
from app.services import storage

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
UPLOADS_DIR = BACKEND_ROOT / "data" / "uploads"

ALLOWED_MIME_PREFIXES = ("image/",)
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def _ensure_dir() -> None:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _ext_from_mime(mime: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/jpg":  ".jpg",
        "image/png":  ".png",
        "image/webp": ".webp",
    }.get(mime.lower(), ".bin")


def save_file_to_disk(
    file_bytes: bytes,
    mime: str,
    original_filename: str | None = None,
) -> tuple[str, Path, int]:
    """Persist raw bytes to disk.

    Returns (upload_id, abs_path, size_bytes).
    Raises ValueError on validation failure.
    """
    if not file_bytes:
        raise ValueError("empty file")
    if len(file_bytes) > MAX_FILE_BYTES:
        raise ValueError(f"file too large: {len(file_bytes)} > {MAX_FILE_BYTES}")
    if not mime.lower().startswith(ALLOWED_MIME_PREFIXES):
        raise ValueError(f"unsupported mime type: {mime}")

    _ensure_dir()
    upload_id = f"up-{uuid.uuid4().hex[:12]}"
    ext = Path(original_filename).suffix if original_filename else _ext_from_mime(mime)
    if not ext:
        ext = _ext_from_mime(mime)

    abs_path = UPLOADS_DIR / f"{upload_id}{ext}"
    abs_path.write_bytes(file_bytes)
    return upload_id, abs_path, len(file_bytes)


def _to_relpath(abs_path: Path) -> str:
    """Store path relative to backend/ for portability."""
    return str(abs_path.relative_to(BACKEND_ROOT))


def insert_upload(
    upload_id: str,
    abs_path: Path,
    mime: str,
    size: int,
    user_id: str | None = None,
) -> UploadItem:
    rel_path = _to_relpath(abs_path)
    now = datetime.utcnow().isoformat()
    conn = storage.get_db()
    conn.execute(
        "INSERT INTO uploads (id, path, mime, size, created_at, user_id, "
        "normalize_status, normalized_path, normalize_task_id) "
        "VALUES (?, ?, ?, ?, ?, ?, 'NONE', NULL, NULL)",
        (upload_id, rel_path, mime, size, now, user_id),
    )
    conn.commit()
    return UploadItem(
        id=upload_id,
        path=rel_path,
        url=f"/static/uploads/{abs_path.name}",
        mime=mime,
        size=size,
        created_at=datetime.fromisoformat(now),
        user_id=user_id,
        normalize_status="NONE",
        normalized_path=None,
        normalize_task_id=None,
    )


def get_upload(upload_id: str) -> UploadItem | None:
    conn = storage.get_db()
    row = conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    abs_path = BACKEND_ROOT / d["path"]
    return UploadItem(
        id=d["id"],
        path=d["path"],
        url=f"/static/uploads/{abs_path.name}",
        mime=d["mime"],
        size=d["size"],
        created_at=datetime.fromisoformat(d["created_at"]),
        user_id=d["user_id"],
        normalize_status=d.get("normalize_status") or "NONE",
        normalized_path=d.get("normalized_path"),
        normalize_task_id=d.get("normalize_task_id"),
    )


def list_uploads(limit: int = 20) -> list[UploadItem]:
    conn = storage.get_db()
    rows = conn.execute(
        "SELECT id FROM uploads ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [get_upload(r["id"]) for r in rows if get_upload(r["id"]) is not None]
