"""Task dataclass + status enum — the unit of work flowing through the queue.

A Task is created by the API Gateway (enqueue) and consumed by a GPU Worker
(dequeue). Its lifecycle state lives in SQLite (Source of Truth), and the
in-process mp.Queue is a transient buffer only.

Status transitions (enforced in persistence.mark_*):
    PENDING  -> RUNNING    (worker claims)
    RUNNING  -> DONE       (worker success)
    RUNNING  -> FAILED     (worker exception)
    RUNNING  -> PENDING    (watchdog rollback for stale heartbeat)

Allowed callers:
    - ai_server.api        (insert_pending)
    - ai_server.worker_process (mark_running, mark_done, mark_failed, heartbeat)
    - ai_server.queue.recovery  (replay + reset)
    - ai_server.queue.watchdog  (stale RUNNING -> PENDING)
"""
from __future__ import annotations

import enum
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


class TaskStatus(str, enum.Enum):
    """Task lifecycle states. Stored as TEXT in SQLite."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

    @classmethod
    def values(cls) -> list[str]:
        return [s.value for s in cls]


# Allowed transitions. Any other transition raises ValueError.
_ALLOWED: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.RUNNING},
    TaskStatus.RUNNING: {TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.PENDING},
    TaskStatus.DONE: set(),
    TaskStatus.FAILED: set(),
}


def assert_transition(from_status: TaskStatus, to_status: TaskStatus) -> None:
    """Raise ValueError if transition is not in the allowed set."""
    if to_status not in _ALLOWED[from_status]:
        raise ValueError(
            f"Illegal task transition: {from_status.value} -> {to_status.value}"
        )


def now_iso() -> str:
    """ISO 8601 UTC timestamp with second precision (consistent across processes)."""
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())


def new_task_id(prefix: str = "rec") -> str:
    """Generate a task id, e.g. 'rec-7f3a9b2c4d11'."""
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class Task:
    """A unit of GPU work.

    Fields:
        id:           unique task id (also primary key in tasks table)
        task_type:    discriminator — 'smpl_fast' | 'smpl_multi' | 'normalize' | 'eval'
        payload:      dict passed to the worker (e.g. upload_id, method, params)
        status:       current lifecycle state
        gpu_id:       gpu pinned when RUNNING, None otherwise
        worker_pid:   worker process pid when RUNNING, None otherwise
        created_at:   ISO timestamp when enqueued
        started_at:   ISO timestamp when claimed by a worker
        heartbeat_at: ISO timestamp of last worker heartbeat (for watchdog)
        finished_at:  ISO timestamp when DONE/FAILED
        result:       dict result on success (e.g. {'glb_path': '...', 'metrics': {...}})
        error_msg:    short error string on FAILED
    """

    id: str
    task_type: str
    payload: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    gpu_id: int | None = None
    worker_pid: int | None = None
    created_at: str = field(default_factory=now_iso)
    started_at: str | None = None
    heartbeat_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error_msg: str | None = None

    # ── Serialization (for mp.Queue transport) ─────────────────────────────

    def to_json(self) -> str:
        """Compact JSON for transport over mp.Queue / IPC."""
        d = asdict(self)
        d["status"] = self.status.value
        return json.dumps(d, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def from_json(cls, s: str) -> "Task":
        d = json.loads(s)
        d["status"] = TaskStatus(d["status"])
        return cls(**d)

    def to_row(self) -> dict[str, Any]:
        """Flat dict matching tasks table columns (status as string)."""
        d = asdict(self)
        d["status"] = self.status.value
        d["payload"] = json.dumps(self.payload, ensure_ascii=False)
        d["result"] = json.dumps(self.result) if self.result is not None else None
        return d

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Task":
        d = dict(row)
        d["status"] = TaskStatus(d["status"])
        # SQL rows use payload_json / result_json; dataclass uses payload / result.
        # NB: pop FIRST, then decide on None vs valid JSON. `if d[k]` would
        # be wrong because None is falsy — we'd skip the pop and leak the
        # column into the dataclass constructor.
        if "payload_json" in d:
            raw = d.pop("payload_json")
            d["payload"] = json.loads(raw) if raw else {}
        if "result_json" in d:
            raw = d.pop("result_json")
            d["result"] = json.loads(raw) if raw else None
        return cls(**d)
