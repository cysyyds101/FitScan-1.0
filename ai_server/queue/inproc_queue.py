"""In-process task queue.

A thin wrapper over multiprocessing.Queue. Acts as a *transient buffer* —
NOT a source of truth. If the queue loses data, recovery.py replays from
SQLite on the next process restart.

Design:
    - One TASK_QUEUE shared by API process + worker processes.
    - When the launcher starts, it instantiates this module in the parent,
      which creates a Queue handle the children inherit via spawn().
    - SHUTDOWN_EVENT lets workers wake up promptly on Ctrl-C / supervisor kill.
    - Helper enqueue() also writes the task to SQLite (insert_pending) so the
      source of truth is updated atomically with the queue insertion.

NOTE on Windows / Linux:
    On Linux, the launcher can use 'fork' (faster, shares state).
    On Windows, only 'spawn' works — children import this module fresh.
    We must keep this module side-effect free except for the queue object
    itself, so spawn-mode reimport is safe.
"""
from __future__ import annotations

import logging
import multiprocessing as mp
from typing import Any

from .persistence import insert_pending
from .task import Task

logger = logging.getLogger(__name__)


# ─── Shared objects ───────────────────────────────────────────────────────────

# maxsize=128: at 128 enqueued tasks, the API process blocks on put().
# This provides backpressure — if all 4 workers are busy, new requests wait
# in the HTTP handler rather than blowing up the workers.
TASK_QUEUE: "mp.Queue[Task]" = mp.Queue(maxsize=128)

# Set when launcher is shutting down. Workers see this and exit cleanly.
SHUTDOWN_EVENT: "mp.Event" = mp.Event()


# ─── Producer side (API Gateway uses these) ──────────────────────────────────

def enqueue(task: Task) -> None:
    """Persist task to SQLite, then put it on the queue.

    Order matters: insert_pending FIRST, then put on queue. If put() blocks
    (queue full) and we crash, the task is in SQLite and recovery will pick
    it up. If we put() first and the DB write fails, we'd have a phantom task
    in the queue with no source of truth.

    For MVP, if DB write fails we DO NOT enqueue (we raise). Caller can retry.
    """
    insert_pending(task)
    try:
        TASK_QUEUE.put(task, timeout=5)
        logger.info(f"[queue] enqueued {task.id} type={task.task_type}")
    except Exception:
        # If put() fails (e.g. queue closed during shutdown), mark failed
        # so the user sees an error instead of a stuck PENDING task.
        from .persistence import mark_failed  # local import to avoid cycle
        try:
            mark_failed(task.id, "enqueue put() failed (queue closed?)")
        except Exception:
            pass
        raise


def request_shutdown() -> None:
    """Signal all workers to exit. Idempotent."""
    if not SHUTDOWN_EVENT.is_set():
        logger.info("[queue] shutdown requested")
        SHUTDOWN_EVENT.set()


def queue_size() -> int:
    """Approximate size; mp.Queue.qsize() may raise on some platforms."""
    try:
        return TASK_QUEUE.qsize()
    except (NotImplementedError, OSError):
        return -1


# ─── Consumer side (worker_process uses these) ───────────────────────────────

def dequeue_blocking(timeout_sec: float = 1.0) -> Task | None:
    """Block up to timeout_sec for a task. Returns None on timeout.

    Workers call this in a tight loop. SHUTDOWN_EVENT check after timeout
    keeps the loop responsive without busy-polling.
    """
    try:
        return TASK_QUEUE.get(timeout=timeout_sec)
    except Exception:
        # queue.Empty is the normal timeout; other exceptions (e.g. during
        # shutdown) we treat the same way.
        return None


# ─── Test / dev helpers ─────────────────────────────────────────────────────

def drain(timeout_sec: float = 0.1) -> list[Task]:
    """Non-blocking: pull all currently-queued tasks. For tests only."""
    out: list[Task] = []
    while True:
        try:
            t = TASK_QUEUE.get(timeout=timeout_sec)
        except Exception:
            break
        out.append(t)
    return out


__all__ = [
    "TASK_QUEUE",
    "SHUTDOWN_EVENT",
    "enqueue",
    "dequeue_blocking",
    "request_shutdown",
    "queue_size",
    "drain",
]
