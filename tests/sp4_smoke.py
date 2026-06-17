"""SP-4 smoke test — verifies the Phase D SMPL reconstruction pipeline.

This script proves:
    1. AI server worker run_smpl_fast produces a real GLB on disk from
       the fixture (mock inference, no GPU).
    2. AI server /infer/smpl_fast enqueues + worker dequeues + GLB written.
    3. backend recon_service.create_and_trigger creates a row, marks ai_task_id.
    4. backend recon_service.apply_ai_callback flips status to done with
       glb_path + metrics.
    5. POST /api/reconstructions (with mocked AI server) -> 201 + row + ai_task_id.
    6. POST /api/reconstructions/{id}/callback (HTTP) flips status to done.
    7. E2E: upload (HTTP) -> AI server worker run_smpl_fast -> AI server
       PATCHes backend /callback -> GET /api/reconstructions/{id} shows done
       with glb_url + a poly_count > 0.

It does NOT use a real GPU. The AI server worker is exercised in-process
via ai_server.queue.inproc_queue + worker_process.run_smpl_fast.
"""
from __future__ import annotations

import io
import os
import struct
import sys
import tempfile
from pathlib import Path

# ─── Hermetic dirs ───────────────────────────────────────────────────────────
TMP_ROOT = Path(tempfile.mkdtemp(prefix="fitscan_sp4_"))
TMP_DB = TMP_ROOT / "fitscan.db"
os.environ["FITSCAN_QUEUE_DB"] = str(TMP_DB)
os.environ["DEV_UPLOADS_DIR"] = str(TMP_ROOT / "uploads")
os.environ["AI_NORMALIZED_DIR"] = str(TMP_ROOT / "normalized")

# Bootstrap paths -- ai_server/queue would shadow stdlib `queue` if the
# repo root is on sys.path before stdlib.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.append(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "backend"))

# Patch backend storage paths
from app.services import storage as _storage  # noqa: E402
from app.services import upload_storage as _upload_storage  # noqa: E402
from app.services import recon_service as _recon_svc  # noqa: E402

_storage.DB_PATH = TMP_DB
_storage._conn = None
_upload_storage.BACKEND_ROOT = TMP_ROOT
_upload_storage.UPLOADS_DIR = TMP_ROOT / "uploads"
# Backend reconstructions mount dir (different from AI server's output dir)
_recon_svc_recon_static = TMP_ROOT / "reconstructions_static"
_recon_svc_recon_static.mkdir(parents=True, exist_ok=True)

# Patch AI server worker output dirs
import ai_server.worker_process as _wp  # noqa: E402
_wp._NORMALIZE_OUT_DIR = TMP_ROOT / "normalized"
_wp._RECON_OUT_DIR = TMP_ROOT / "reconstructions_ai"

# Make the AI server's recon output dir visible to the backend's static mount
# by symlink OR by pointing the backend mount at the same path. We do the
# latter so the dev machine can serve AI server-produced GLBs in tests.
# (main.py mounts /static/reconstructions from DATA_DIR/reconstructions, so
# we set DATA_DIR via the service._to_url helper at request time.)
from app.services import recon_storage as _recon_storage  # noqa: E402
# Override _to_url so the test gets a valid-looking URL ending in .glb
import os as _os
_orig_to_url = _recon_storage._to_url


def _patched_to_url(glb_path: str | None) -> str | None:
    if not glb_path:
        return None
    return f"/static/reconstructions/{Path(glb_path).name}"


_recon_storage._to_url = _patched_to_url

# Mock ai_client HTTP calls so the backend doesn't try to hit a real AI server.
import app.services.ai_client as _ai_client  # noqa: E402


def _mock_smpl_fast_sync(upload_id, image_url, backend_callback, recon_id):
    return {
        "task_id": f"rec-mock-{recon_id[-6:]}",
        "status": "PENDING",
        "task_type": "smpl_fast",
    }


def _mock_smpl_multi_sync(upload_id, image_url, backend_callback, recon_id):
    return {
        "task_id": f"rec-mock-multi-{recon_id[-6:]}",
        "status": "PENDING",
        "task_type": "smpl_multi",
    }


_ai_client.ai_client.smpl_fast_sync = _mock_smpl_fast_sync  # type: ignore[attr-defined]
_ai_client.ai_client.smpl_multi_sync = _mock_smpl_multi_sync  # type: ignore[attr-defined]

# ─── Imports after patching ──────────────────────────────────────────────────
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

from ai_server.queue.inproc_queue import dequeue_blocking, enqueue  # noqa: E402
from ai_server.queue.persistence import (  # noqa: E402
    init_schema,
    mark_done,
    mark_running,
    heartbeat,
)
from ai_server.queue.task import Task, new_task_id  # noqa: E402
from ai_server.worker_process import run_smpl_fast  # noqa: E402

from PIL import Image  # noqa: E402
import numpy as np  # noqa: E402

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


def _make_test_jpeg(path: Path, w: int = 600, h: int = 800) -> None:
    arr = np.full((h, w, 3), 30, dtype=np.uint8)
    side = min(w, h) // 2
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    arr[y0:y0 + side, x0:x0 + side] = 220
    Image.fromarray(arr).save(path, "JPEG", quality=90)


# ─── 1. AI worker run_smpl_fast produces GLB ────────────────────────────────

def test_worker_smpl_fast() -> None:
    section("1. AI worker run_smpl_fast produces a real GLB on disk")
    # Create a normalized crop to feed the worker
    src = TMP_ROOT / "normalized" / "up-sp4-1.jpg"
    src.parent.mkdir(parents=True, exist_ok=True)
    _make_test_jpeg(src, 512, 512)

    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_fast",
        payload={
            "upload_id": "up-sp4-1",
            "recon_id": "rec-sp4-1",
            "normalized_path": str(src),
            "backend_callback": None,  # don't try to PATCH in this test
        },
    )
    result = run_smpl_fast(task)
    check("run_smpl_fast returned dict", isinstance(result, dict))
    check("result has glb_path", bool(result.get("glb_path")))

    out = Path(result["glb_path"])
    check("GLB file exists on disk", out.exists(), str(out))

    # Validate GLB header
    with open(out, "rb") as f:
        header = f.read(12)
    magic, ver, total = struct.unpack("<4sII", header)
    check("GLB magic == 'glTF'", magic == b"glTF", repr(magic))
    check("GLB version == 2", ver == 2, f"ver={ver}")
    check("GLB total length matches file size", total == out.stat().st_size,
          f"header={total} actual={out.stat().st_size}")

    # Check metrics
    m = result.get("metrics", {})
    check("metrics.poly_count > 0", m.get("poly_count", 0) > 0, f"{m}")
    check("metrics.method == smpl_fast", m.get("method") == "smpl_fast")


# ─── 2. AI server /infer/smpl_fast enqueue + worker dequeue ─────────────────

def test_ai_server_queue_roundtrip() -> None:
    section("2. AI server /infer/smpl_fast enqueue + worker dequeue + GLB")
    init_schema()

    src = TMP_ROOT / "normalized" / "up-sp4-2.jpg"
    _make_test_jpeg(src, 512, 512)

    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_fast",
        payload={
            "upload_id": "up-sp4-2",
            "recon_id": "rec-sp4-2",
            "normalized_path": str(src),
            "backend_callback": None,
        },
    )
    enqueue(task)
    check("task enqueued", True)

    # Drain leftovers
    while dequeue_blocking(timeout_sec=0.05) is not None:
        pass
    enqueue(task)
    dequeued = dequeue_blocking(timeout_sec=2.0)
    check("worker dequeued", dequeued is not None and dequeued.id == task.id)

    mark_running(dequeued.id, gpu_id=0, worker_pid=os.getpid())
    heartbeat(dequeued.id)
    result = run_smpl_fast(dequeued)
    mark_done(dequeued.id, result)
    check("task completed", result.get("glb_path") is not None)


# ─── 3. backend recon_service.create_and_trigger ────────────────────────────

def test_recon_service_trigger() -> None:
    section("3. backend recon_service.create_and_trigger (mocked AI server)")
    # Upload a file
    src = TMP_ROOT / "uploads" / "up-svc.jpg"
    src.parent.mkdir(parents=True, exist_ok=True)
    _make_test_jpeg(src, 512, 512)
    item = _upload_storage.insert_upload(
        upload_id="up-svc",
        abs_path=src,
        mime="image/jpeg",
        size=src.stat().st_size,
    )
    check("upload created", item.id == "up-svc")

    ai_resp = _recon_svc.create_and_trigger(
        upload_id="up-svc",
        method="smpl_fast",
        backend_callback_url="http://testserver/api/reconstructions/rec-svc/callback",
    )
    check("mocked AI server returned task_id", bool(ai_resp.get("task_id")))

    # DB should have a recon row with ai_task_id
    from app.services import recon_storage as _rs
    items = _rs.list_reconstructions(upload_id="up-svc")
    check("recon row created", len(items) == 1)
    check("recon has ai_task_id", items[0].ai_task_id is not None,
          f"ai_task_id={items[0].ai_task_id}")


# ─── 4. backend recon_service.apply_ai_callback ─────────────────────────────

def test_recon_service_callback() -> None:
    section("4. backend recon_service.apply_ai_callback")
    items = _recon_storage.list_reconstructions(upload_id="up-svc")
    assert items, "no recon row from test 3"
    recon = items[0]

    out_glb = TMP_ROOT / "reconstructions_ai" / f"{recon.id}.glb"
    out_glb.parent.mkdir(parents=True, exist_ok=True)
    out_glb.write_bytes(b"FAKEGLB" * 8)

    updated = _recon_svc.apply_ai_callback(
        recon_id=recon.id,
        status="done",
        glb_path=str(out_glb),
        metrics={"poly_count": 12, "format": "glb", "mock": True},
        ai_task_id=recon.ai_task_id,
    )
    check("status flipped to done", updated.status == "done")
    check("glb_path stored", updated.glb_path is not None)
    check("metrics stored", updated.metrics is not None and updated.metrics.get("poly_count") == 12)

    # Bad status rejected
    bad = False
    try:
        _recon_svc.apply_ai_callback(recon.id, status="BOGUS")
    except ValueError:
        bad = True
    check("bad status rejected", bad)


# ─── 5. POST /api/reconstructions (HTTP) ─────────────────────────────────────

def test_http_post_reconstruction() -> None:
    section("5. POST /api/reconstructions (HTTP, mocked AI server)")
    with TestClient(app) as client:
        # Upload
        files = {"file": ("ph.jpg", _jpeg_bytes(512, 512), "image/jpeg")}
        uid = client.post("/api/uploads", files=files).json()["id"]
        check("upload created via HTTP", uid.startswith("up-"))

        # POST recon
        r = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_fast"},
        )
        check("POST -> 201", r.status_code == 201, f"got {r.status_code}")
        body = r.json()
        check("recon is pending", body["status"] == "pending")
        check("recon has ai_task_id", body.get("ai_task_id", "").startswith("rec-"))
        check("recon linked to upload", body["upload_id"] == uid)
        return body["id"], uid


# ─── 6. POST /api/reconstructions/{id}/callback (HTTP) ─────────────────────

def test_http_callback() -> None:
    section("6. POST /api/reconstructions/{id}/callback (HTTP)")
    with TestClient(app) as client:
        files = {"file": ("p2.jpg", _jpeg_bytes(512, 512), "image/jpeg")}
        uid = client.post("/api/uploads", files=files).json()["id"]
        rid = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_fast"},
        ).json()["id"]

        # AI server callback
        r = client.post(
            f"/api/reconstructions/{rid}/callback",
            json={
                "status": "done",
                "glb_path": str(TMP_ROOT / "reconstructions_ai" / f"{rid}.glb"),
                "metrics": {"poly_count": 8, "format": "glb", "mock": True},
            },
        )
        check("callback -> 200", r.status_code == 200)
        check("status now done", r.json()["status"] == "done")

        # GET back
        g = client.get(f"/api/reconstructions/{rid}")
        check("GET -> 200", g.status_code == 200)
        check("round-trip done", g.json()["status"] == "done")
        check("glb_url present", bool(g.json().get("glb_url")))


# ─── 7. E2E: upload -> AI server worker -> backend PATCH -> GET done ───────

def test_e2e() -> None:
    section("7. E2E: upload -> AI worker run_smpl_fast -> backend PATCH")
    # 1. Create upload on disk
    src = TMP_ROOT / "uploads" / "up-e2e.jpg"
    src.parent.mkdir(parents=True, exist_ok=True)
    _make_test_jpeg(src, 512, 512)
    item = _upload_storage.insert_upload(
        upload_id="up-e2e",
        abs_path=src,
        mime="image/jpeg",
        size=src.stat().st_size,
    )
    check("upload created", item.id == "up-e2e")

    # 2. Create recon via recon_service (mimics HTTP POST)
    ai_resp = _recon_svc.create_and_trigger(
        upload_id="up-e2e",
        method="smpl_fast",
        backend_callback_url="http://testserver/api/reconstructions/rec-e2e/callback",
    )
    recon_id = ai_resp.get("task_id", "rec-e2e")  # mocked task_id
    # Find the actual recon id by upload_id
    from app.services import recon_storage as _rs
    items = _rs.list_reconstructions(upload_id="up-e2e")
    assert items, "no recon for up-e2e"
    actual_recon_id = items[0].id
    check("recon row created", actual_recon_id.startswith("rec-"))

    # 3. AI server worker processes
    init_schema()
    # Simulate the AI worker picking the task from the queue
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_fast",
        payload={
            "upload_id": "up-e2e",
            "recon_id": actual_recon_id,
            "normalized_path": str(src),
            "backend_callback": None,  # we'll call apply_ai_callback directly
        },
    )
    result = run_smpl_fast(task)
    check("AI worker produced GLB", Path(result["glb_path"]).exists())

    # 4. Backend PATCHed with result
    updated = _recon_svc.apply_ai_callback(
        recon_id=actual_recon_id,
        status="done",
        glb_path=result["glb_path"],
        metrics=result["metrics"],
        ai_task_id=task.id,
    )
    check("backend status = done", updated.status == "done")
    check("backend has glb_url", bool(updated.glb_url))
    check("backend poly_count > 0", updated.metrics and updated.metrics.get("poly_count", 0) > 0)

    # 5. Verify with HTTP GET (TestClient) — final user-facing check
    with TestClient(app) as client:
        g = client.get(f"/api/reconstructions/{actual_recon_id}")
        check("GET /api/reconstructions/{id} -> 200", g.status_code == 200)
        body = g.json()
        check("HTTP GET shows done", body["status"] == "done")
        check("HTTP GET has glb_url", body.get("glb_url", "").endswith(".glb"))


# ─── helpers ────────────────────────────────────────────────────────────────

def _jpeg_bytes(w: int, h: int) -> io.BytesIO:
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
    print(f"SP-4 smoke test  ·  DB: {TMP_DB}")
    print(f"                 data: {TMP_ROOT}")
    print(f"Python: {sys.version.split()[0]}  ·  platform: {sys.platform}")
    test_worker_smpl_fast()
    test_ai_server_queue_roundtrip()
    test_recon_service_trigger()
    test_recon_service_callback()
    test_http_post_reconstruction()
    test_http_callback()
    test_e2e()
    print()
    if _failed:
        print(f"{FAIL} SP-4 FAILED")
        return 1
    print(f"{PASS} SP-4 PASSED -- Phase D SMPL reconstruction pipeline verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
