"""SP-3 smoke test — verifies the Phase C normalize pipeline.

This script proves:
    1. uploads table has normalize_status / normalized_path / normalize_task_id.
    2. AI server worker handler (run_normalize) produces a 512x512 JPEG
       from a synthetic source image (PIL only, no torch, no GPU).
    3. AI server /infer/normalize endpoint enqueues a task and the
       worker dequeues and processes it via the in-process queue.
    4. Backend normalize_service.trigger_normalize marks uploads row QUEUED
       and (with AI server mocked) returns the task_id.
    5. Backend normalize_service.set_normalize_result flips to NORMALIZED
       and stores the path.
    6. POST /api/uploads/{id}/normalize (with mocked AI server) returns 202.
    7. PATCH /api/uploads/{id}/normalized updates state.
    8. E2E: upload (HTTP) -> AI server normalize (worker) -> backend PATCH
       -> GET /api/uploads/{id}/normalized shows NORMALIZED + 512x512 file.

It does NOT use a real GPU. The AI server worker is exercised in-process
via ai_server.queue.inproc_queue and worker_process.run_normalize.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

# ─── Hermetic temp dirs ──────────────────────────────────────────────────────
TMP_ROOT = Path(tempfile.mkdtemp(prefix="fitscan_sp3_"))
TMP_DB = TMP_ROOT / "fitscan.db"
os.environ["FITSCAN_QUEUE_DB"] = str(TMP_DB)  # ai server queue DB
os.environ["DEV_UPLOADS_DIR"] = str(TMP_ROOT / "uploads")  # shared source dir
os.environ["AI_NORMALIZED_DIR"] = str(TMP_ROOT / "normalized")  # output dir

# Bootstrap paths -- order matters. ai_server/queue/ would shadow the
# stdlib `queue` module if C:\FitScan sits on sys.path. We solve it by
# putting C:\FitScan LAST (so `import queue` resolves to stdlib first),
# and importing ai_server.* and app.* via their full paths from subdirs.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent

# Remove repo root from sys.path if present, then re-add at the end so
# ai_server.* imports work but `import queue` still finds stdlib first.
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.append(str(_REPO_ROOT))  # last, so stdlib wins name lookups

sys.path.insert(0, str(_REPO_ROOT / "backend"))

# ─── Patch backend storage to hermetic paths ────────────────────────────────
from app.services import storage as _storage  # noqa: E402
from app.services import upload_storage as _upload_storage  # noqa: E402
from app.services import normalize_service as _norm_svc  # noqa: E402

_storage.DB_PATH = TMP_DB
_storage._conn = None
_upload_storage.BACKEND_ROOT = TMP_ROOT
_upload_storage.UPLOADS_DIR = TMP_ROOT / "uploads"

# ─── Patch AI server worker output dir ──────────────────────────────────────
import ai_server.worker_process as _wp  # noqa: E402
_wp._NORMALIZE_OUT_DIR = TMP_ROOT / "normalized"

# ─── Mock the AI server side for the backend route (we test it separately too)
import app.services.ai_client as _ai_client  # noqa: E402
_orig_normalize = _ai_client.ai_client.normalize


def _mock_normalize_sync(upload_id, image_url, backend_callback):
    """Stand-in for AI server HTTP call. Simulates a 202 enqueue response."""
    return {
        "task_id": f"norm-mock-{upload_id[-6:]}",
        "status": "PENDING",
        "task_type": "normalize",
    }


# Attach a sync shim that uses the mock (so TestClient routes work without
# the AI server actually being up).
def _patched_normalize_sync(upload_id, image_url, backend_callback):
    return _mock_normalize_sync(upload_id, image_url, backend_callback)


_ai_client.ai_client.normalize_sync = _patched_normalize_sync  # type: ignore[attr-defined]

# ─── Imports after patching ──────────────────────────────────────────────────
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

from ai_server.queue.inproc_queue import (  # noqa: E402
    TASK_QUEUE,
    dequeue_blocking,
    enqueue,
)
from ai_server.queue.persistence import (  # noqa: E402
    init_schema,
    mark_done,
    mark_failed,
    mark_running,
    heartbeat,
)
from ai_server.queue.task import Task, TaskStatus, new_task_id  # noqa: E402
from ai_server.worker_process import run_normalize  # noqa: E402

from PIL import Image  # noqa: E402

PASS = "[OK] "
FAIL = "[FAIL] "
_failed = False


def check(name: str, ok: bool, detail: str = "") -> None:
    sym = PASS if ok else FAIL
    print(f"  {sym} {name}" + (f" -- {detail}" if detail else ""))
    if not ok:
        global _failed
        _failed = True


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ─── 1. Schema migration ─────────────────────────────────────────────────────

def test_schema() -> None:
    section("1. uploads table has normalize columns")
    _storage._init_db(_storage._get_db())
    conn = _storage.get_db()
    cols = {r[1] for r in conn.execute("PRAGMA table_info(uploads)").fetchall()}
    for c in ("normalize_status", "normalized_path", "normalize_task_id"):
        check(f"uploads.{c} present", c in cols)


# ─── 2. AI worker PIL handler produces 512x512 ──────────────────────────────

def _make_test_jpeg(path: Path, w: int = 800, h: int = 1200) -> None:
    """Write a synthetic JPEG with a dark background and a centered bright square
    (so Otsu threshold finds a clean bbox)."""
    import numpy as np
    arr = np.full((h, w, 3), 30, dtype=np.uint8)  # dark bg
    # bright square in the middle (50% of image)
    side = min(w, h) // 2
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    arr[y0:y0 + side, x0:x0 + side] = 220
    Image.fromarray(arr).save(path, "JPEG", quality=90)


def test_worker_normalize() -> None:
    section("2. AI worker run_normalize produces 512x512 JPEG")
    src = TMP_ROOT / "uploads" / "src-test.jpg"
    src.parent.mkdir(parents=True, exist_ok=True)
    _make_test_jpeg(src, 800, 1200)

    task = Task(
        id=new_task_id("norm"),
        task_type="normalize",
        payload={
            "upload_id": "up-test1234",
            "image_url": str(src),
            "backend_callback": None,
        },
    )
    result = run_normalize(task)
    check("run_normalize returned dict", isinstance(result, dict))
    check("width=512", result.get("width") == 512, f"{result.get('width')}")
    check("height=512", result.get("height") == 512, f"{result.get('height')}")
    out = Path(result["normalized_path"])
    check("output file exists", out.exists(), str(out))
    check("output is on disk under our TMP_ROOT",
          str(out).startswith(str(TMP_ROOT)),
          str(out))
    # Re-open and verify pixel size
    with Image.open(out) as img:
        check("output JPEG is 512x512", img.size == (512, 512), f"{img.size}")
        check("output format JPEG", img.format == "JPEG", f"{img.format}")


# ─── 3. AI server endpoint enqueues + worker dequeues ───────────────────────

def test_ai_server_queue_roundtrip() -> None:
    section("3. AI server /infer/normalize enqueue + worker dequeue")
    # Init AI server schema
    init_schema()

    src = TMP_ROOT / "uploads" / "src-q.jpg"
    _make_test_jpeg(src, 600, 800)

    task = Task(
        id=new_task_id("norm"),
        task_type="normalize",
        payload={
            "upload_id": "up-queue1234",
            "image_url": str(src),
            "backend_callback": None,
        },
    )
    enqueue(task)
    check("task enqueued", True)

    # Drain any leftovers from prior tests
    while dequeue_blocking(timeout_sec=0.05) is not None:
        pass

    # Re-enqueue for the test
    enqueue(task)
    dequeued = dequeue_blocking(timeout_sec=2.0)
    check("worker dequeued", dequeued is not None and dequeued.id == task.id)

    # Simulate worker lifecycle
    mark_running(dequeued.id, gpu_id=0, worker_pid=os.getpid())
    heartbeat(dequeued.id)
    result = run_normalize(dequeued)
    mark_done(dequeued.id, result)
    check("task completed via run_normalize", result["width"] == 512)


# ─── 4. Backend normalize_service.trigger_normalize (no AI server) ───────────

def test_normalize_service_trigger() -> None:
    section("4. backend normalize_service.trigger_normalize (mocked AI server)")
    # Upload a file
    src = TMP_ROOT / "uploads" / "up-svctest.jpg"
    _make_test_jpeg(src, 640, 800)
    item = _upload_storage.insert_upload(
        upload_id="up-svctest",
        abs_path=src,
        mime="image/jpeg",
        size=src.stat().st_size,
    )
    check("upload row created", item.id == "up-svctest")
    check("initial normalize_status=NONE", item.normalize_status == "NONE")

    # trigger (mocked)
    ai_resp = _norm_svc.trigger_normalize(
        upload_id="up-svctest",
        backend_callback_url="http://testserver/api/uploads/up-svctest/normalized",
    )
    check("mocked AI server returned task_id", bool(ai_resp.get("task_id")))
    check("status PENDING", ai_resp.get("status") == "PENDING")

    # DB row should now be QUEUED
    row = _norm_svc.get_upload_row("up-svctest")
    check("uploads.normalize_status = QUEUED", row.get("normalize_status") == "QUEUED")


# ─── 5. Backend set_normalize_result flips to NORMALIZED ─────────────────────

def test_normalize_service_result() -> None:
    section("5. backend normalize_service.set_normalize_result")
    item = _norm_svc.set_normalize_result(
        upload_id="up-svctest",
        status="NORMALIZED",
        normalized_path=str(TMP_ROOT / "normalized" / "up-svctest.jpg"),
        task_id="norm-mock-svctest",
    )
    check("item updated", item.normalize_status == "NORMALIZED")
    check("path stored", item.normalized_path is not None)
    check("task_id stored", item.normalize_task_id == "norm-mock-svctest")

    # Bad status rejected
    bad = False
    try:
        _norm_svc.set_normalize_result("up-svctest", status="BOGUS")
    except ValueError:
        bad = True
    check("invalid status rejected", bad)

    # Missing upload rejected
    missing = False
    try:
        _norm_svc.set_normalize_result("up-nope", status="NORMALIZED")
    except ValueError:
        missing = True
    check("missing upload rejected", missing)


# ─── 6. POST /api/uploads/{id}/normalize (HTTP) ─────────────────────────────

def test_http_trigger_normalize() -> None:
    section("6. POST /api/uploads/{id}/normalize (HTTP)")
    with TestClient(app) as client:
        # Upload
        files = {"file": ("svc.jpg", _make_test_jpeg_io(640, 800), "image/jpeg")}
        r = client.post("/api/uploads", files=files)
        uid = r.json()["id"]

        # Trigger
        r2 = client.post(f"/api/uploads/{uid}/normalize")
        check("POST .../normalize -> 202", r2.status_code == 202, f"got {r2.status_code}")
        body = r2.json()
        check("response has normalize_status=QUEUED",
              body.get("normalize_status") == "QUEUED",
              f"{body.get('normalize_status')}")
        check("response has normalize_task_id",
              body.get("normalize_task_id", "").startswith("norm-"))


# ─── 7. PATCH /api/uploads/{id}/normalized (HTTP) ───────────────────────────

def test_http_patch_normalized() -> None:
    section("7. PATCH /api/uploads/{id}/normalized (HTTP)")
    with TestClient(app) as client:
        files = {"file": ("p.jpg", _make_test_jpeg_io(640, 800), "image/jpeg")}
        uid = client.post("/api/uploads", files=files).json()["id"]
        client.post(f"/api/uploads/{uid}/normalize")  # QUEUED

        # PATCH from "AI server" callback
        r = client.patch(
            f"/api/uploads/{uid}/normalized",
            json={
                "status": "NORMALIZED",
                "normalized_path": str(TMP_ROOT / "normalized" / f"{uid}.jpg"),
                "task_id": "norm-patch-1",
            },
        )
        check("PATCH -> 200", r.status_code == 200)
        check("status now NORMALIZED", r.json()["normalize_status"] == "NORMALIZED")
        check("task_id stored", r.json()["normalize_task_id"] == "norm-patch-1")

        # GET normalized polls it
        r2 = client.get(f"/api/uploads/{uid}/normalized")
        check("GET -> 200", r2.status_code == 200)
        check("GET shows NORMALIZED", r2.json()["normalize_status"] == "NORMALIZED")


# ─── 8. E2E: upload + worker run + backend PATCH round-trip ────────────────

def test_e2e() -> None:
    section("8. E2E: upload -> AI server worker -> backend PATCH")
    src = TMP_ROOT / "uploads" / "up-e2e.jpg"
    _make_test_jpeg(src, 800, 1000)
    item = _upload_storage.insert_upload(
        upload_id="up-e2e",
        abs_path=src,
        mime="image/jpeg",
        size=src.stat().st_size,
    )
    check("upload created", item.id == "up-e2e")

    # Run AI worker handler directly
    init_schema()
    task = Task(
        id=new_task_id("norm"),
        task_type="normalize",
        payload={"upload_id": "up-e2e", "image_url": str(src), "backend_callback": None},
    )
    result = run_normalize(task)
    check("AI worker produced 512x512", result["width"] == 512 and result["height"] == 512)

    # Simulate AI server PATCHing the backend
    item2 = _norm_svc.set_normalize_result(
        upload_id="up-e2e",
        status="NORMALIZED",
        normalized_path=result["normalized_path"],
        task_id=task.id,
    )
    check("backend row NORMALIZED", item2.normalize_status == "NORMALIZED")
    check("backend path matches worker output", item2.normalized_path == result["normalized_path"])

    # Verify the file is the real 512x512 JPEG
    with Image.open(item2.normalized_path) as img:
        check("on-disk file is 512x512 JPEG", img.size == (512, 512) and img.format == "JPEG",
              f"{img.size} {img.format}")


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_test_jpeg_io(w: int, h: int) -> io.BytesIO:
    """In-memory JPEG (for TestClient multipart upload)."""
    import numpy as np
    arr = np.full((h, w, 3), 30, dtype=np.uint8)
    side = min(w, h) // 2
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    arr[y0:y0 + side, x0:x0 + side] = 220
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    buf.seek(0)
    return buf


# ─── main ───────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"SP-3 smoke test  ·  DB: {TMP_DB}")
    print(f"                 data: {TMP_ROOT}")
    print(f"Python: {sys.version.split()[0]}  ·  platform: {sys.platform}")
    test_schema()
    test_worker_normalize()
    test_ai_server_queue_roundtrip()
    test_normalize_service_trigger()
    test_normalize_service_result()
    test_http_trigger_normalize()
    test_http_patch_normalized()
    test_e2e()
    print()
    if _failed:
        print(f"{FAIL} SP-3 FAILED")
        return 1
    print(f"{PASS} SP-3 PASSED -- Phase C normalize pipeline verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
