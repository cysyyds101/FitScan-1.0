"""SQLite persistence for the task queue.

Holds the Source of Truth: the `tasks` table. The in-process mp.Queue is just
a transient buffer; if it loses data, recovery.py replays from here.

Design choices:
    - WAL journaling so workers can write concurrently with the API process.
    - File-based DB so it survives process restarts (recovery test).
    - Each process opens its own connection; sqlite3 with check_same_thread=False.
    - Short-lived transactions; the heartbeat update is the hottest path.

Schema columns mirror the Task dataclass (see queue/task.py). Indexes on
status and heartbeat_at support the watchdog's stale-RUNNING scan.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .task import Task, TaskStatus, assert_transition, now_iso


# ─── Location ────────────────────────────────────────────────────────────────

def _default_db_path() -> Path:
    """Default DB path: <repo>/ai_server/storage/queue.db.

    Override by setting FITSCAN_QUEUE_DB env var (used by tests).
    """
    env = os.getenv("FITSCAN_QUEUE_DB")
    if env:
        return Path(env)
    # ai_server/queue/persistence.py  ->  ai_server/storage/queue.db
    here = Path(__file__).resolve().parent.parent
    d = here / "storage"
    d.mkdir(parents=True, exist_ok=True)
    return d / "queue.db"


DB_PATH: Path = _default_db_path()


# ─── Schema ──────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    id            TEXT PRIMARY KEY,
    task_type     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'PENDING',
    payload_json  TEXT NOT NULL,
    gpu_id        INTEGER,
    worker_pid    INTEGER,
    created_at    TEXT NOT NULL,
    started_at    TEXT,
    heartbeat_at  TEXT,
    finished_at   TEXT,
    result_json   TEXT,
    error_msg     TEXT
);
CREATE INDEX IF NOT EXISTS idx_tasks_status      ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_heartbeat   ON tasks(heartbeat_at);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at  ON tasks(created_at);
"""


# ─── Per-process connection (sqlite3, single writer per process) ─────────────

_local = threading.local()


def _connect() -> sqlite3.Connection:
    """Open a connection with sensible defaults for our access pattern."""
    conn = sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
        timeout=30.0,        # wait up to 30s if DB is busy
        isolation_level=None,  # autocommit; we manage transactions explicitly
    )
    conn.row_factory = sqlite3.Row
    # WAL allows concurrent readers + one writer, ideal for many workers.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")  # safe enough with WAL
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _conn() -> sqlite3.Connection:
    """Return the per-thread connection (lazy init)."""
    c = getattr(_local, "conn", None)
    if c is None:
        c = _connect()
        _local.conn = c
    return c


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Context manager that yields a connection and commits on success.

    Use as:
        with db() as conn:
            conn.execute(...)

    On exception, rolls back. Always commits on clean exit.
    """
    conn = _conn()
    try:
        conn.execute("BEGIN")
        yield conn
        conn.execute("COMMIT")
    except Exception:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.OperationalError:
            pass
        raise


def init_schema() -> None:
    """Create tables and indexes if missing. Call once at startup."""
    conn = _conn()
    conn.executescript(SCHEMA_SQL)


# ─── CRUD ─────────────────────────────────────────────────────────────────────

def insert_pending(task: Task) -> None:
    """Insert a new task in PENDING state. Idempotent on PK conflict (REPLACE).

    Use REPLACE so retries (e.g. duplicate enqueue) don't error. Caller should
    ensure the id is unique per logical attempt.
    """
    if task.status is not TaskStatus.PENDING:
        raise ValueError(f"insert_pending requires PENDING, got {task.status.value}")
    row = task.to_row()
    with db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO tasks
                (id, task_type, status, payload_json, gpu_id, worker_pid,
                 created_at, started_at, heartbeat_at, finished_at, result_json, error_msg)
            VALUES
                (:id, :task_type, :status, :payload, :gpu_id, :worker_pid,
                 :created_at, :started_at, :heartbeat_at, :finished_at, :result, :error_msg)
            """,
            row,
        )


def mark_running(task_id: str, gpu_id: int, worker_pid: int) -> Task:
    """Transition PENDING -> RUNNING. Sets started_at + heartbeat_at to now.

    Raises ValueError if the task is not PENDING (caller raced and lost).
    """
    now = now_iso()
    with db() as conn:
        cur = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Task {task_id} not found")
        cur_status = TaskStatus(row["status"])
        assert_transition(cur_status, TaskStatus.RUNNING)
        conn.execute(
            """
            UPDATE tasks
            SET status = 'RUNNING',
                gpu_id = ?,
                worker_pid = ?,
                started_at = ?,
                heartbeat_at = ?
            WHERE id = ? AND status = 'PENDING'
            """,
            (gpu_id, worker_pid, now, now, task_id),
        )
    return get(task_id)  # type: ignore[return-value]


def heartbeat(task_id: str) -> None:
    """Refresh heartbeat_at. Idempotent. No-op if task not in RUNNING state.

    This is the hot path: called every 30s by every running task.
    """
    now = now_iso()
    with db() as conn:
        conn.execute(
            "UPDATE tasks SET heartbeat_at = ? WHERE id = ? AND status = 'RUNNING'",
            (now, task_id),
        )


def mark_done(task_id: str, result: dict[str, Any]) -> Task:
    """Transition RUNNING -> DONE. Stores result and finished_at."""
    now = now_iso()
    with db() as conn:
        cur = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Task {task_id} not found")
        cur_status = TaskStatus(row["status"])
        assert_transition(cur_status, TaskStatus.DONE)
        conn.execute(
            """
            UPDATE tasks
            SET status = 'DONE',
                result_json = ?,
                finished_at = ?,
                heartbeat_at = NULL
            WHERE id = ? AND status = 'RUNNING'
            """,
            (json.dumps(result, ensure_ascii=False), now, task_id),
        )
    return get(task_id)  # type: ignore[return-value]


def mark_failed(task_id: str, error_msg: str) -> Task:
    """Transition RUNNING -> FAILED. Stores error_msg (truncated to 500 chars)."""
    now = now_iso()
    msg = (error_msg or "")[:500]
    with db() as conn:
        cur = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Task {task_id} not found")
        cur_status = TaskStatus(row["status"])
        assert_transition(cur_status, TaskStatus.FAILED)
        conn.execute(
            """
            UPDATE tasks
            SET status = 'FAILED',
                error_msg = ?,
                finished_at = ?,
                heartbeat_at = NULL
            WHERE id = ? AND status = 'RUNNING'
            """,
            (msg, now, task_id),
        )
    return get(task_id)  # type: ignore[return-value]


def reset_to_pending(task_id: str, error_msg: str | None = None) -> Task:
    """Transition RUNNING -> PENDING. Used by recovery and watchdog.

    Clears gpu_id, worker_pid, started_at, heartbeat_at so the next claim
    starts fresh. Optionally writes a watchdog-rolled-back note.
    """
    with db() as conn:
        cur = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Task {task_id} not found")
        cur_status = TaskStatus(row["status"])
        assert_transition(cur_status, TaskStatus.PENDING)
        if error_msg:
            conn.execute(
                "UPDATE tasks SET error_msg = ? WHERE id = ?",
                (error_msg[:500], task_id),
            )
        conn.execute(
            """
            UPDATE tasks
            SET status = 'PENDING',
                gpu_id = NULL,
                worker_pid = NULL,
                started_at = NULL,
                heartbeat_at = NULL
            WHERE id = ? AND status = 'RUNNING'
            """,
            (task_id,),
        )
    return get(task_id)  # type: ignore[return-value]


# ─── Reads ────────────────────────────────────────────────────────────────────

def get(task_id: str) -> Task | None:
    """Fetch a task by id, or None if not found."""
    with db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(row)


def list_recoverable(timeout_sec: int = 600) -> list[Task]:
    """Tasks that need re-queuing at startup.

    Includes:
        - status = PENDING  (never started, or rolled back)
        - status = RUNNING AND
              (heartbeat_at IS NULL OR
               heartbeat_at < (now - timeout_sec) OR
               worker_pid not alive)

    Note: PID-alive check is done by recovery.py using psutil/os.kill, not here.
    """
    with db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE status = 'PENDING'
               OR (status = 'RUNNING' AND
                   (heartbeat_at IS NULL OR
                    (julianday('now') - julianday(heartbeat_at)) * 86400 > ?))
            """,
            (timeout_sec,),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def list_by_status(status: TaskStatus, limit: int = 100) -> list[Task]:
    """Recent tasks in a given status (debug + /health)."""
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status.value, limit),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


# ─── Internal ────────────────────────────────────────────────────────────────

def _row_to_task(row: sqlite3.Row) -> Task:
    d = dict(row)
    return Task.from_row(d)
