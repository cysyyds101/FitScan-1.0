"""Heartbeat watchdog — runs inside the API Gateway process.

Periodically scans the tasks table for RUNNING tasks whose heartbeat is older
than the timeout. Such tasks are rolled back to PENDING and re-queued.

Why the API Gateway runs the watchdog (not a worker):
    - Watchdog is bookkeeping, not GPU work.
    - The API process is the only one that's always alive while the system runs.
    - Workers may crash and restart; we still need a single source of 'triage'.

Rollback strategy:
    - Set status = PENDING, clear gpu_id / worker_pid / started_at / heartbeat_at.
    - Re-enqueue the task so the next available worker picks it up.
    - Stamp error_msg = 'watchdog: heartbeat timeout' for observability.

Timing:
    - Default timeout = 10 minutes (configurable via env or constructor).
    - Default scan interval = 30 seconds.
    - Both should be > heartbeat writer interval (default 30s) to avoid
      false positives under load.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from .inproc_queue import SHUTDOWN_EVENT, TASK_QUEUE
from .persistence import list_recoverable, reset_to_pending
from .task import Task, now_iso

logger = logging.getLogger(__name__)


class HeartbeatWatchdog:
    """Background thread that reaps stale RUNNING tasks."""

    def __init__(
        self,
        timeout_sec: int = 600,
        scan_interval_sec: int = 30,
    ):
        self.timeout_sec = timeout_sec
        self.scan_interval_sec = scan_interval_sec
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run, name="heartbeat-watchdog", daemon=True
        )
        self._thread.start()
        logger.info(
            f"[watchdog] started (timeout={self.timeout_sec}s, "
            f"scan={self.scan_interval_sec}s)"
        )

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=join_timeout)
            logger.info("[watchdog] stopped")

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.scan_once()
            except Exception as e:
                logger.exception(f"[watchdog] scan error: {e}")
            # Sleep in small slices so stop() returns quickly
            for _ in range(self.scan_interval_sec):
                if self._stop.is_set():
                    return
                time.sleep(1)

    def scan_once(self) -> int:
        """Find stale RUNNING tasks, rollback, re-enqueue. Returns count."""
        stale = list_recoverable(timeout_sec=self.timeout_sec)
        reaped = 0
        for t in stale:
            if t.status.value != "RUNNING":
                # PENDING — leave to normal enqueue path
                continue
            try:
                reset_to_pending(
                    t.id,
                    error_msg=f"watchdog rollback at {now_iso()}",
                )
                TASK_QUEUE.put(t, timeout=5)
                logger.warning(
                    f"[watchdog] rolled back {t.id} type={t.task_type} "
                    f"(no heartbeat for {self.timeout_sec}s)"
                )
                reaped += 1
            except Exception as e:
                logger.error(f"[watchdog] reap {t.id} failed: {e}")
        return reaped


__all__ = ["HeartbeatWatchdog"]
