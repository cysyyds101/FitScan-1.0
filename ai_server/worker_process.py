"""GPU worker process.

Each worker:
    - Owns one GPU (CUDA_VISIBLE_DEVICES pinned by the launcher).
    - Owns one task role: 'fast' | 'multi' | 'idle'.
    - Loops: dequeue from mp.Queue → mark RUNNING → run → mark DONE/FAILED.
    - Refreshes heartbeat in a background thread every 30s.
    - If the task is not the worker's role, skip and put it back on the queue
      (with a small delay so we don't spin).

Lifecycle within a task:
    1. dequeue_blocking()  -> Task
    2. if task_type matches role: proceed
       else: requeue via TASK_QUEUE.put (someone else may handle it) and continue
    3. persistence.mark_running(task.id, gpu_id, pid)
    4. start heartbeat writer thread
    5. run task via dispatch
    6. persistence.mark_done or mark_failed
    7. stop heartbeat writer
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
import traceback
from typing import Any

# Bootstrap path so 'ai_server.queue.*' imports work regardless of CWD
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from ai_server.queue.inproc_queue import (  # noqa: E402
    SHUTDOWN_EVENT,
    TASK_QUEUE,
    dequeue_blocking,
)
from ai_server.queue.persistence import (  # noqa: E402
    heartbeat,
    mark_done,
    mark_failed,
    mark_running,
)
from ai_server.queue.task import Task  # noqa: E402

logger = logging.getLogger(__name__)


# ─── Heartbeat writer thread (T011) ─────────────────────────────────────────

class HeartbeatWriter(threading.Thread):
    """Refreshes heartbeat_at in SQLite every interval_sec.

    Stops when the stop event is set. daemon=True so it doesn't block
    process exit.

    NOTE: do NOT name the stop method `stop` — that conflicts with
    threading.Thread's deprecated internal `_stop` and breaks Thread.join().
    """

    def __init__(self, task_id: str, interval_sec: int = 30):
        super().__init__(name=f"hb-{task_id}", daemon=True)
        self.task_id = task_id
        self.interval_sec = interval_sec
        self._shutdown = threading.Event()

    def request_stop(self) -> None:
        self._shutdown.set()

    def run(self) -> None:
        while not self._shutdown.is_set():
            try:
                heartbeat(self.task_id)
            except Exception as e:
                logger.warning(f"[hb] heartbeat update failed for {self.task_id}: {e}")
            for _ in range(self.interval_sec):
                if self._shutdown.is_set():
                    return
                time.sleep(1)


# ─── Task dispatch (stub for Phase A) ────────────────────────────────────────

def run_task(task: Task) -> dict[str, Any]:
    """Dispatch by task_type. Phase A has no real GPU work yet — return mock.

    Phase D (FAST PATH) and Phase E (SLOW PATH) will add real implementations.
    For now, return a stub result so the lifecycle (PENDING→RUNNING→DONE) can
    be verified end-to-end via SP-1 and SP-2.
    """
    gpu = os.environ.get("FITSCAN_GPU_ID", "?")
    role = os.environ.get("FITSCAN_ROLE", "?")
    logger.info(f"[worker gpu={gpu} role={role}] running {task.id} type={task.task_type}")
    # Simulate work
    time.sleep(0.5)
    return {
        "gpu_id": int(gpu) if gpu.isdigit() else None,
        "role": role,
        "task_type": task.task_type,
        "echo_payload": task.payload,
    }


# ─── Main loop (T010) ────────────────────────────────────────────────────────

# Roles a worker can handle. The dispatcher table lets us add/remove types
# without touching the loop.
ROLE_HANDLERS: dict[str, set[str]] = {
    # worker role  -> task types it will accept
    "fast":  {"smpl_fast", "normalize", "eval"},
    "multi": {"smpl_multi", "normalize", "eval"},
    "idle":  {"normalize", "eval"},
}


def _accepts(role: str, task_type: str) -> bool:
    return task_type in ROLE_HANDLERS.get(role, set())


def _requeue(task: Task, reason: str) -> None:
    """Put task back on queue (best effort). Used when worker can't handle it."""
    logger.warning(f"[worker] re-queue {task.id}: {reason}")
    try:
        TASK_QUEUE.put(task, timeout=2)
    except Exception as e:
        logger.error(f"[worker] re-queue {task.id} failed: {e}")
        # If we can't re-queue, mark failed so it doesn't stay PENDING forever
        try:
            mark_failed(task.id, f"re-queue failed: {reason}")
        except Exception:
            pass
    time.sleep(0.2)


def main() -> int:
    parser = argparse.ArgumentParser(description="FitScan AI worker process")
    parser.add_argument("--gpu", type=int, required=True, help="GPU id (pinned)")
    parser.add_argument(
        "--role",
        choices=["fast", "multi", "idle"],
        required=True,
        help="Task role this worker handles",
    )
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format=f"%(asctime)s [worker gpu={args.gpu} role={args.role}] %(levelname)s: %(message)s",
    )
    logger.info(f"worker starting pid={os.getpid()} gpu={args.gpu} role={args.role}")

    while not SHUTDOWN_EVENT.is_set():
        task = dequeue_blocking(timeout_sec=1.0)
        if task is None:
            continue

        if not _accepts(args.role, task.task_type):
            _requeue(task, f"role={args.role} cannot handle type={task.task_type}")
            continue

        # ── Double-write #1: PENDING -> RUNNING ──────────────────────────────
        try:
            mark_running(task.id, gpu_id=args.gpu, worker_pid=os.getpid())
        except Exception as e:
            logger.error(f"[worker] mark_running failed for {task.id}: {e}")
            _requeue(task, f"mark_running failed: {e}")
            continue

        # ── Start heartbeat writer ──────────────────────────────────────────
        hb = HeartbeatWriter(task_id=task.id, interval_sec=30)
        hb.start()

        # ── Run task ────────────────────────────────────────────────────────
        try:
            result = run_task(task)
            # Double-write #2a: RUNNING -> DONE
            mark_done(task.id, result)
            logger.info(f"[worker] DONE {task.id}")
        except Exception as e:
            tb = traceback.format_exc(limit=4)
            logger.error(f"[worker] FAILED {task.id}: {e}\n{tb}")
            # Double-write #2b: RUNNING -> FAILED
            try:
                mark_failed(task.id, f"{type(e).__name__}: {e}\n{tb[-300:]}")
            except Exception as ee:
                logger.critical(f"[worker] mark_failed for {task.id} also failed: {ee}")
        finally:
            hb.request_stop()
            # Don't join indefinitely — daemon thread will die with process.
            hb.join(timeout=1.0)

    logger.info(f"worker gpu={args.gpu} role={args.role} exiting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
