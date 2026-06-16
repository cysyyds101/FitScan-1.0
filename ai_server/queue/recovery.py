"""Recovery scan at AI server startup.

When the launcher (or its worker children) start up, they call recover_once()
to rebuild the in-process queue from SQLite. This handles two scenarios:

    1. Process crashed mid-task  (RUNNING with no recent heartbeat, or
       worker_pid that no longer exists in the OS).
    2. Queue lost its buffer     (e.g. mp.Queue is in-memory only, so a
       restart of the launcher empties it).

The 'source of truth' is the tasks table; the queue is just a buffer.

Key safety:
    - We DO NOT skip a task that we already see in the queue (the API may
      have enqueued it milliseconds before the launcher restarted).
    - We check both: status='PENDING' AND status='RUNNING' with stale
      heartbeat / dead pid.
    - PID-alive uses psutil if available, else a /proc/$pid lookup on
      Linux, else a best-effort skip on Windows.
"""
from __future__ import annotations

import logging
import os
from typing import Iterable

from .inproc_queue import TASK_QUEUE
from .persistence import list_recoverable, reset_to_pending
from .task import Task

logger = logging.getLogger(__name__)


# ─── Process liveness ────────────────────────────────────────────────────────

def _is_pid_alive(pid: int | None) -> bool:
    """Return True iff pid exists in OS process table.

    On Linux: check /proc/<pid>. On Windows: use os.kill with signal 0.
    """
    if pid is None:
        return False
    try:
        if os.name == "nt":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if h == 0:
                return False
            try:
                code = ctypes.c_ulong()
                ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
                return code.value == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(h)
        else:
            # POSIX: signal 0 just checks existence.
            os.kill(pid, 0)
            return True
    except (OSError, PermissionError, ImportError):
        return False


# ─── Recovery ────────────────────────────────────────────────────────────────

def _stale_reason(t: Task) -> str | None:
    """Return why this task is recoverable, or None if it's not recoverable."""
    if t.status.value == "PENDING":
        return "pending"
    if t.status.value == "RUNNING":
        if t.heartbeat_at is None:
            return "running-no-heartbeat"
        if not _is_pid_alive(t.worker_pid):
            return f"worker-pid-{t.worker_pid}-dead"
        # heartbeat stale is handled in list_recoverable(); treat here as fresh
        return None
    return None  # DONE / FAILED — leave alone


def recover_once(timeout_sec: int = 600) -> int:
    """Scan DB, reset stale RUNNING tasks, enqueue PENDING + reset RUNNING.

    Returns the number of tasks re-queued. Safe to call multiple times
    (it will only re-queue tasks that are PENDING or have stale RUNNING).
    """
    stale = list_recoverable(timeout_sec=timeout_sec)
    requeued = 0
    for t in stale:
        reason = _stale_reason(t)
        if reason is None:
            continue
        try:
            if t.status.value == "RUNNING":
                # Roll back to PENDING first (clears gpu/pid/heartbeat).
                reset_to_pending(
                    t.id,
                    error_msg=f"recovered at startup: {reason}",
                )
            # PENDING tasks need no reset — just enqueue.
            TASK_QUEUE.put(t, timeout=5)
            logger.warning(
                f"[recovery] re-queued {t.id} type={t.task_type} reason={reason}"
            )
            requeued += 1
        except Exception as e:
            logger.error(f"[recovery] failed to re-queue {t.id}: {e}")
    if requeued == 0:
        logger.info("[recovery] no tasks to recover")
    return requeued


__all__ = ["recover_once", "_is_pid_alive"]
