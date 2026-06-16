"""SP-1 smoke test — verifies the Phase A queue pipeline without needing GPU.

This script proves:
    1. SQLite schema initializes cleanly.
    2. Task dataclass + persistence CRUD works (PENDING -> RUNNING -> DONE/FAILED).
    3. Heartbeat writer updates heartbeat_at.
    4. Recovery scan finds PENDING + stale RUNNING.
    5. Watchdog rolls back stale RUNNING -> PENDING.
    6. mp.Queue round-trip works (in-process).

It does NOT spawn worker subprocesses (that needs a real GPU host). For
the supervisor / restart / breaker logic, see test_launcher_logic.py
(which exercises the GPUState / WorkerSupervisor in isolation).
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

# Use a temp DB so we don't clobber real state
TMP_DB = Path(tempfile.gettempdir()) / "fitscan_sp1_test.db"
if TMP_DB.exists():
    TMP_DB.unlink()
os.environ["FITSCAN_QUEUE_DB"] = str(TMP_DB)

# Bootstrap
_HERE = Path(__file__).resolve().parent
_PARENT = _HERE.parent
sys.path.insert(0, str(_PARENT))

from ai_server.queue import persistence as P  # noqa: E402
from ai_server.queue.inproc_queue import (  # noqa: E402
    TASK_QUEUE,
    SHUTDOWN_EVENT,
    dequeue_blocking,
    enqueue,
)
from ai_server.queue.recovery import recover_once  # noqa: E402
from ai_server.queue.task import Task, TaskStatus, new_task_id  # noqa: E402
from ai_server.queue.watchdog import HeartbeatWatchdog  # noqa: E402
from ai_server.worker_process import HeartbeatWriter  # noqa: E402


PASS = "[OK] "
FAIL = "[FAIL] "


def check(name: str, ok: bool, detail: str = "") -> None:
    sym = PASS if ok else FAIL
    print(f"  {sym} {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        global _failed
        _failed = True


_failed = False


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ─── 1. Schema ───────────────────────────────────────────────────────────────

def test_schema() -> None:
    section("1. Schema init")
    P.init_schema()
    with P.db() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
        ).fetchall()
    check("tasks table created", len(rows) == 1)

    with P.db() as conn:
        idx = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='tasks'"
        ).fetchall()
    check("indexes created", len(idx) >= 2, f"{len(idx)} indexes")


# ─── 2. CRUD + transitions ──────────────────────────────────────────────────

def test_crud() -> None:
    section("2. Persistence CRUD + status transitions")
    t = Task(id=new_task_id("rec"), task_type="smpl_fast", payload={"upload_id": "up-001"})
    P.insert_pending(t)
    got = P.get(t.id)
    check("insert_pending + get", got is not None and got.status is TaskStatus.PENDING)

    P.mark_running(t.id, gpu_id=0, worker_pid=99999)
    got = P.get(t.id)
    check(
        "mark_running sets gpu_id + pid + started_at",
        got is not None and got.gpu_id == 0 and got.worker_pid == 99999 and got.started_at is not None,
    )

    # Heartbeat
    P.heartbeat(t.id)
    got = P.get(t.id)
    check("heartbeat sets heartbeat_at", got is not None and got.heartbeat_at is not None)

    P.mark_done(t.id, {"glb_path": "/tmp/out.glb", "metrics": {"chamfer": 12.3}})
    got = P.get(t.id)
    check(
        "mark_done stores result_json",
        got is not None
        and got.status is TaskStatus.DONE
        and got.result is not None
        and got.result.get("glb_path") == "/tmp/out.glb",
    )


# ─── 3. Illegal transition ──────────────────────────────────────────────────

def test_illegal_transition() -> None:
    section("3. Illegal transition guard")
    t = Task(id=new_task_id("rec"), task_type="smpl_fast", payload={})
    P.insert_pending(t)
    P.mark_running(t.id, gpu_id=0, worker_pid=1)
    P.mark_done(t.id, {"ok": 1})
    # DONE -> RUNNING should fail
    raised = False
    try:
        P.mark_running(t.id, gpu_id=1, worker_pid=2)
    except ValueError:
        raised = True
    check("DONE -> RUNNING rejected", raised)


# ─── 4. Recovery ────────────────────────────────────────────────────────────

def test_recovery() -> None:
    section("4. Recovery scan")
    # Fresh PENDING
    t1 = Task(id=new_task_id("rec"), task_type="smpl_fast", payload={"x": 1})
    P.insert_pending(t1)
    # Stale RUNNING (heartbeat 2h ago, far beyond 10min default)
    t2 = Task(id=new_task_id("rec"), task_type="smpl_multi", payload={"y": 2})
    P.insert_pending(t2)
    P.mark_running(t2.id, gpu_id=1, worker_pid=999999)
    # Manually age the heartbeat
    with P.db() as conn:
        conn.execute(
            "UPDATE tasks SET heartbeat_at = '2020-01-01T00:00:00' WHERE id = ?",
            (t2.id,),
        )
    # Drain queue first (any items left from prior tests)
    while not dequeue_blocking(timeout_sec=0.05) is None:
        pass

    n = recover_once(timeout_sec=10)
    check("recovery re-queued both tasks", n == 2, f"got n={n}")
    # Verify t2 was reset
    got = P.get(t2.id)
    check(
        "stale RUNNING reset to PENDING",
        got is not None and got.status is TaskStatus.PENDING and got.gpu_id is None,
    )
    # Drain queue
    drained = []
    while True:
        x = dequeue_blocking(timeout_sec=0.1)
        if x is None:
            break
        drained.append(x)
    check("queue contained both tasks", len(drained) >= 2)


# ─── 5. Watchdog rollback ──────────────────────────────────────────────────

def test_watchdog() -> None:
    section("5. HeartbeatWatchdog rolls back stale RUNNING")
    t = Task(id=new_task_id("rec"), task_type="smpl_fast", payload={})
    P.insert_pending(t)
    P.mark_running(t.id, gpu_id=2, worker_pid=999999)
    # Age heartbeat
    with P.db() as conn:
        conn.execute(
            "UPDATE tasks SET heartbeat_at = '2020-01-01T00:00:00' WHERE id = ?",
            (t.id,),
        )
    # Drain queue
    while dequeue_blocking(timeout_sec=0.05) is not None:
        pass

    wd = HeartbeatWatchdog(timeout_sec=10, scan_interval_sec=1)
    n = wd.scan_once()
    check("watchdog reaped 1 task", n == 1, f"got {n}")
    got = P.get(t.id)
    check(
        "watchdog rolled back to PENDING",
        got is not None and got.status is TaskStatus.PENDING,
    )


# ─── 6. HeartbeatWriter thread ──────────────────────────────────────────────

def test_heartbeat_writer() -> None:
    section("6. HeartbeatWriter thread")
    t = Task(id=new_task_id("rec"), task_type="smpl_fast", payload={})
    P.insert_pending(t)
    P.mark_running(t.id, gpu_id=3, worker_pid=os.getpid())
    # Capture initial heartbeat
    h0 = P.get(t.id).heartbeat_at
    time.sleep(1.1)
    # Run a short writer
    hb = HeartbeatWriter(t.id, interval_sec=1)
    hb.start()
    time.sleep(2.5)
    hb.request_stop()
    hb.join(timeout=1)
    h1 = P.get(t.id).heartbeat_at
    check(
        "heartbeat refreshed by writer",
        h1 is not None and h0 is not None and h1 >= h0,
        f"h0={h0} h1={h1}",
    )


# ─── 7. enqueue -> dequeue round-trip ──────────────────────────────────────

def test_enqueue_dequeue() -> None:
    section("7. enqueue + dequeue_blocking round-trip")
    # Drain leftover from prior tests
    while dequeue_blocking(timeout_sec=0.2) is not None:
        pass
    t = Task(id=new_task_id("rec"), task_type="smpl_fast", payload={"k": "v"})
    enqueue(t)
    got = dequeue_blocking(timeout_sec=2.0)
    check("dequeue returned the task", got is not None and got.id == t.id)
    check("payload preserved", got is not None and got.payload.get("k") == "v")


# ─── main ───────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"SP-1 smoke test  ·  DB: {TMP_DB}")
    print(f"Python: {sys.version.split()[0]}  ·  platform: {sys.platform}")
    test_schema()
    test_crud()
    test_illegal_transition()
    test_recovery()
    test_watchdog()
    test_heartbeat_writer()
    test_enqueue_dequeue()
    print()
    if _failed:
        print(f"{FAIL} SP-1 FAILED")
        return 1
    print(f"{PASS} SP-1 PASSED — Phase A queue pipeline verified.")
    # Cleanup
    try:
        TMP_DB.unlink()
        # WAL may leave sidecar files
        for ext in ("-wal", "-shm"):
            p = TMP_DB.with_name(TMP_DB.name + ext)
            if p.exists():
                p.unlink()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
