"""In-memory storage (SQLite via sqlite3 for production, dict for dev MVP).

Implements ClothingItem and MeasurementSession persistence.
No ORM, no SQLAlchemy — sqlite3 directly.
"""
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from app.api.schemas import ClothingItem, MeasurementSession


# ─── Database setup ────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).resolve().parent.parent.parent / "fitscan.db"
_conn = None


def _get_db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _init_db(_conn)
    return _conn


def _init_db(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS measurements (
            id           TEXT PRIMARY KEY,
            created_at   TEXT NOT NULL,
            raw_data     TEXT,
            coarse_data  TEXT,
            precise_data TEXT,
            status       TEXT DEFAULT 'pending',
            ai_task_id   TEXT
        );

        CREATE TABLE IF NOT EXISTS clothing (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            model_url   TEXT NOT NULL,
            category    TEXT DEFAULT 'top',
            description TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS uploads (
            id                 TEXT PRIMARY KEY,
            path               TEXT NOT NULL,
            mime               TEXT NOT NULL,
            size               INTEGER NOT NULL,
            created_at         TEXT NOT NULL,
            user_id            TEXT,
            normalize_status   TEXT DEFAULT 'NONE',
            normalized_path    TEXT,
            normalize_task_id  TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_uploads_created_at        ON uploads(created_at);
        CREATE INDEX IF NOT EXISTS idx_uploads_user_id           ON uploads(user_id);
        CREATE INDEX IF NOT EXISTS idx_uploads_normalize_status  ON uploads(normalize_status);

        -- Idempotent column add for upgrades (CREATE TABLE IF NOT EXISTS won't add columns
        -- to an existing table). We probe and ALTER if missing.
        -- SQLite doesn't support IF NOT EXISTS on ALTER, so we check pragma_table_info.

        CREATE TABLE IF NOT EXISTS reconstructions (
            id            TEXT PRIMARY KEY,
            upload_id     TEXT NOT NULL,
            method        TEXT NOT NULL,
            glb_path      TEXT,
            metrics_json  TEXT,
            status        TEXT NOT NULL DEFAULT 'pending',
            ai_task_id    TEXT,
            created_at    TEXT NOT NULL,
            FOREIGN KEY (upload_id) REFERENCES uploads(id)
        );
        CREATE INDEX IF NOT EXISTS idx_recon_created_at ON reconstructions(created_at);
        CREATE INDEX IF NOT EXISTS idx_recon_upload_id  ON reconstructions(upload_id);
        CREATE INDEX IF NOT EXISTS idx_recon_status     ON reconstructions(status);
    """)

    # Idempotent column add for upgrades (CREATE TABLE IF NOT EXISTS won't add columns
    # to an existing table). SQLite doesn't support IF NOT EXISTS on ALTER, so we
    # probe pragma_table_info and ALTER if missing.
    existing = {
        row[1]
        for row in conn.execute("PRAGMA table_info(uploads)").fetchall()
    }
    if "normalize_status" not in existing:
        conn.execute("ALTER TABLE uploads ADD COLUMN normalize_status TEXT DEFAULT 'NONE'")
    if "normalized_path" not in existing:
        conn.execute("ALTER TABLE uploads ADD COLUMN normalized_path TEXT")
    if "normalize_task_id" not in existing:
        conn.execute("ALTER TABLE uploads ADD COLUMN normalize_task_id TEXT")

    # Seed clothing data if empty
    cur = conn.execute("SELECT COUNT(*) FROM clothing")
    if cur.fetchone()[0] == 0:
        seed = [
            ("c01", "T恤 (T-Shirt)", "/static/models/clothing_01.glb", "top", "基础款短袖上衣"),
            ("c02", "背心 (Vest)",    "/static/models/clothing_02.glb", "top", "简约无袖款式"),
            ("c03", "连帽衫 (Hoodie)", "/static/models/clothing_01.glb", "outer", "带帽外套"),
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO clothing VALUES (?, ?, ?, ?, ?)",
            seed,
        )
        conn.commit()


# ─── Clothing ──────────────────────────────────────────────────────────────────

def list_clothing() -> list[ClothingItem]:
    conn = _get_db()
    rows = conn.execute("SELECT * FROM clothing").fetchall()
    return [ClothingItem(**dict(r)) for r in rows]


def get_clothing(item_id: str) -> ClothingItem | None:
    conn = _get_db()
    row = conn.execute("SELECT * FROM clothing WHERE id = ?", (item_id,)).fetchone()
    return ClothingItem(**dict(row)) if row else None


# ─── Measurements ──────────────────────────────────────────────────────────────

def create_measurement_session(
    raw_data: dict | None = None,
    coarse_data: dict | None = None,
) -> MeasurementSession:
    sid = f"msr-{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    conn = _get_db()
    conn.execute(
        "INSERT INTO measurements (id, created_at, raw_data, coarse_data, status) VALUES (?, ?, ?, ?, ?)",
        (sid, now, json.dumps(raw_data), json.dumps(coarse_data), "pending"),
    )
    conn.commit()
    return MeasurementSession(
        id=sid,
        created_at=datetime.fromisoformat(now),
        raw_data=raw_data,
        coarse_data=coarse_data,
        status="pending",
    )


def get_measurement(session_id: str) -> MeasurementSession | None:
    conn = _get_db()
    row = conn.execute("SELECT * FROM measurements WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return None
    d = dict(row)
    return MeasurementSession(
        id=d["id"],
        created_at=datetime.fromisoformat(d["created_at"]),
        raw_data=json.loads(d["raw_data"]) if d["raw_data"] else None,
        coarse_data=json.loads(d["coarse_data"]) if d["coarse_data"] else None,
        precise_data=json.loads(d["precise_data"]) if d["precise_data"] else None,
        status=d["status"],
        ai_task_id=d["ai_task_id"],
    )


def update_measurement(session_id: str, precise_data: dict, status: str = "done", ai_task_id: str | None = None):
    conn = _get_db()
    conn.execute(
        "UPDATE measurements SET precise_data = ?, status = ?, ai_task_id = ? WHERE id = ?",
        (json.dumps(precise_data), status, ai_task_id, session_id),
    )
    conn.commit()


def get_db() -> sqlite3.Connection:
    """Public accessor — for sibling service modules (upload/recon storage)."""
    return _get_db()


def list_measurements(limit: int = 20) -> list[MeasurementSession]:
    conn = _get_db()
    rows = conn.execute(
        "SELECT * FROM measurements ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [get_measurement(r["id"]) for r in rows]

