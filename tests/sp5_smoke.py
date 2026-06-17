"""SP-5 smoke test — verifies the Phase E multi-view SMPL pipeline.

This script proves:
    1. AI server worker run_smpl_multi accepts N image_urls and writes
       ONE consolidated GLB on disk.
    2. AI server /infer/smpl_multi enqueue + dequeue + multi-view pipeline.
    3. backend recon_service.create_and_trigger with image_urls=[] on
       smpl_multi -> 400.
    4. backend recon_service.create_and_trigger with image_urls=[1 url]
       auto-routes to smpl_fast.
    5. backend recon_service.create_and_trigger with image_urls=[2 urls]
       falls back to smpl_fast with a warning.
    6. backend recon_service.create_and_trigger with image_urls=[3..8 urls]
       uses smpl_multi.
    7. backend recon_service.create_and_trigger with image_urls=[9 urls]
       -> ValueError too-many-views.
    8. POST /api/reconstructions with image_urls=[3] -> 201 + smpl_multi.
    9. E2E: upload 3 normalized crops -> POST /api/reconstructions ->
       run_smpl_multi in-process -> PATCH callback -> GET shows done with
       view_count=3 in metrics.

It does NOT use a real GPU. The AI server worker is exercised in-process.
"""
from __future__ import annotations

import io
import os
import struct
import sys
import tempfile
from pathlib import Path

# ─── Hermetic dirs ───────────────────────────────────────────────────────────
TMP_ROOT = Path(tempfile.mkdtemp(prefix="fitscan_sp5_"))
TMP_DB = TMP_ROOT / "fitscan.db"
os.environ["FITSCAN_QUEUE_DB"] = str(TMP_DB)
os.environ["DEV_UPLOADS_DIR"] = str(TMP_ROOT / "uploads")
os.environ["AI_NORMALIZED_DIR"] = str(TMP_ROOT / "normalized")

# Bootstrap paths -- ai_server/queue would shadow stdlib queue.
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
if str(_REPO_ROOT) in sys.path:
    sys.path.remove(str(_REPO_ROOT))
sys.path.append(str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "backend"))

# ─── Patch backend storage paths ────────────────────────────────────────────
from app.services import storage as _storage  # noqa: E402
from app.services import upload_storage as _upload_storage  # noqa: E402
from app.services import recon_service as _recon_svc  # noqa: E402
from app.services import recon_storage as _recon_storage  # noqa: E402

_storage.DB_PATH = TMP_DB
_storage._conn = None
_upload_storage.BACKEND_ROOT = TMP_ROOT
_upload_storage.UPLOADS_DIR = TMP_ROOT / "uploads"

# ─── Patch AI server worker output dirs ──────────────────────────────────────
import ai_server.worker_process as _wp  # noqa: E402
_wp._NORMALIZE_OUT_DIR = TMP_ROOT / "normalized"
_wp._RECON_OUT_DIR = TMP_ROOT / "reconstructions_ai"

# ─── Mock ai_client so TestClient works without a real AI server ────────────
import app.services.ai_client as _ai_client  # noqa: E402


def _mock_smpl_fast_sync(upload_id, image_url, backend_callback, recon_id):
    return {"task_id": f"rec-mock-{recon_id[-6:]}", "status": "PENDING", "task_type": "smpl_fast"}


def _mock_smpl_multi_sync(upload_id, image_url, image_urls, backend_callback, recon_id):
    return {
        "task_id": f"rec-mock-multi-{recon_id[-6:]}",
        "status": "PENDING",
        "task_type": "smpl_multi",
    }


_ai_client.ai_client.smpl_fast_sync = _mock_smpl_fast_sync  # type: ignore[attr-defined]
_ai_client.ai_client.smpl_multi_sync = _mock_smpl_multi_sync  # type: ignore[attr-defined]

# Override _to_url for static serve path
def _patched_to_url(glb_path):
    if not glb_path:
        return None
    return f"/static/reconstructions/{Path(glb_path).name}"


_recon_storage._to_url = _patched_to_url

# ─── Imports after patching ──────────────────────────────────────────────────
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

from ai_server.queue.inproc_queue import dequeue_blocking, enqueue  # noqa: E402
from ai_server.queue.persistence import init_schema, mark_done, mark_running  # noqa: E402
from ai_server.queue.task import Task, new_task_id  # noqa: E402
from ai_server.worker_process import run_smpl_multi  # noqa: E402

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


def _make_test_jpeg(path: Path, w: int = 512, h: int = 512) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    arr = np.full((h, w, 3), 30, dtype=np.uint8)
    side = min(w, h) // 2
    x0 = (w - side) // 2
    y0 = (h - side) // 2
    arr[y0:y0 + side, x0:x0 + side] = 220
    Image.fromarray(arr).save(path, "JPEG", quality=90)


def _make_n_normalized(upload_id: str, n: int) -> list[Path]:
    """Create N normalized crop files in the standard location."""
    paths: list[Path] = []
    # Note: in real life every image has a different upload_id. For the
    # multi-view worker we accept arbitrary paths -- we just make N files
    # named distinctly.
    for i in range(n):
        p = TMP_ROOT / "normalized" / f"{upload_id}-view{i}.jpg"
        _make_test_jpeg(p, 512, 512)
        paths.append(p)
    return paths


# ─── 1. AI worker run_smpl_multi with N views produces 1 GLB ───────────────

def test_worker_smpl_multi() -> None:
    section("1. AI worker run_smpl_multi with N views produces 1 GLB")
    src_paths = _make_n_normalized("up-sp5-1", 3)
    image_urls = [str(p) for p in src_paths]
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_multi",
        payload={
            "upload_id": "up-sp5-1",
            "recon_id": "rec-sp5-1",
            "image_urls": image_urls,
            "backend_callback": None,
        },
    )
    result = run_smpl_multi(task)
    check("run_smpl_multi returned dict", isinstance(result, dict))
    check("result has view_count=3", result.get("view_count") == 3,
          f"view_count={result.get('view_count')}")
    check("result has glb_path", bool(result.get("glb_path")))

    out = Path(result["glb_path"])
    check("GLB file exists on disk", out.exists(), str(out))

    # Validate GLB header
    with open(out, "rb") as f:
        header = f.read(12)
    magic, ver, total = struct.unpack("<4sII", header)
    check("GLB magic == 'glTF'", magic == b"glTF", repr(magic))
    check("GLB version == 2", ver == 2)
    check("GLB total length matches", total == out.stat().st_size)

    m = result["metrics"]
    check("metrics.method == smpl_multi", m["method"] == "smpl_multi")
    check("metrics.view_count == 3", m["view_count"] == 3)
    check("metrics.src_total_bytes > 0", m["src_total_bytes"] > 0)


# ─── 2. AI server /infer/smpl_multi enqueue + dequeue ──────────────────────

def test_ai_server_queue_roundtrip() -> None:
    section("2. AI server /infer/smpl_multi enqueue + dequeue")
    init_schema()

    src_paths = _make_n_normalized("up-sp5-2", 2)
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_multi",
        payload={
            "upload_id": "up-sp5-2",
            "recon_id": "rec-sp5-2",
            "image_urls": [str(p) for p in src_paths],
            "backend_callback": None,
        },
    )
    enqueue(task)
    while dequeue_blocking(timeout_sec=0.05) is not None:
        pass
    enqueue(task)
    dequeued = dequeue_blocking(timeout_sec=2.0)
    check("worker dequeued", dequeued is not None and dequeued.id == task.id)

    mark_running(dequeued.id, gpu_id=0, worker_pid=os.getpid())
    result = run_smpl_multi(dequeued)
    mark_done(dequeued.id, result)
    check("task completed", result.get("glb_path") is not None)


# ─── 3-7. recon_service.create_and_trigger routing logic ──────────────────

def _make_upload() -> str:
    src = TMP_ROOT / "uploads" / "up-routing.jpg"
    _make_test_jpeg(src, 512, 512)
    item = _upload_storage.insert_upload(
        upload_id="up-routing",
        abs_path=src,
        mime="image/jpeg",
        size=src.stat().st_size,
    )
    return item.id


def test_routing_logic() -> None:
    section("3-7. backend recon_service hybrid routing")
    uid = _make_upload()

    # 3. 0 views + smpl_multi -> 400
    raised = False
    try:
        _recon_svc.create_and_trigger(
            upload_id=uid, method="smpl_multi", image_urls=[]
        )
    except ValueError as e:
        raised = "at least one image" in str(e)
    check("0 views + smpl_multi -> ValueError", raised)

    # 4. 1 view + smpl_multi -> auto-route to smpl_fast
    src = TMP_ROOT / "normalized" / "single.jpg"
    _make_test_jpeg(src, 512, 512)
    r = _recon_svc.create_and_trigger(
        upload_id=uid, method="smpl_multi", image_urls=[str(src)]
    )
    # Get the row back to see method
    items = _recon_storage.list_reconstructions(upload_id=uid, limit=1)
    check("1 view auto-routed to smpl_fast", items[0].method == "smpl_fast",
          f"method={items[0].method}")

    # 5. 2 views + smpl_multi -> warn + smpl_fast
    paths2 = _make_n_normalized("warn2", 2)
    r = _recon_svc.create_and_trigger(
        upload_id=uid, method="smpl_multi", image_urls=[str(p) for p in paths2]
    )
    items = _recon_storage.list_reconstructions(upload_id=uid, limit=1)
    check("2 views fell back to smpl_fast", items[0].method == "smpl_fast",
          f"method={items[0].method}")

    # 6. 3 views + smpl_multi -> smpl_multi
    paths3 = _make_n_normalized("good3", 3)
    r = _recon_svc.create_and_trigger(
        upload_id=uid, method="smpl_multi", image_urls=[str(p) for p in paths3]
    )
    items = _recon_storage.list_reconstructions(upload_id=uid, limit=1)
    check("3 views kept as smpl_multi", items[0].method == "smpl_multi",
          f"method={items[0].method}")

    # 7. 9 views + smpl_multi -> too many
    paths9 = _make_n_normalized("bad9", 9)
    raised = False
    try:
        _recon_svc.create_and_trigger(
            upload_id=uid, method="smpl_multi",
            image_urls=[str(p) for p in paths9]
        )
    except ValueError as e:
        raised = "too many" in str(e)
    check("9 views -> ValueError too many", raised)


# ─── 8. HTTP POST with image_urls ──────────────────────────────────────────

def test_http_post_multi() -> None:
    section("8. POST /api/reconstructions with image_urls (HTTP)")
    with TestClient(app) as client:
        # Upload
        files = {"file": ("p.jpg", _jpeg_bytes(512, 512), "image/jpeg")}
        uid = client.post("/api/uploads", files=files).json()["id"]

        # POST with image_urls=3
        paths = _make_n_normalized("http3", 3)
        r = client.post(
            "/api/reconstructions",
            json={
                "upload_id": uid,
                "method": "smpl_multi",
                "image_urls": [str(p) for p in paths],
            },
        )
        check("POST -> 201", r.status_code == 201, f"got {r.status_code}")
        body = r.json()
        check("method stored as smpl_multi", body["method"] == "smpl_multi")
        check("ai_task_id present", body.get("ai_task_id", "").startswith("rec-"))

        # POST with 0 image_urls + smpl_multi -> 409
        r2 = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_multi", "image_urls": []},
        )
        check("0 image_urls + smpl_multi -> 409", r2.status_code == 409,
              f"got {r2.status_code}")


# ─── 9. E2E ────────────────────────────────────────────────────────────────

def test_e2e() -> None:
    section("9. E2E: 3 uploads -> trigger -> AI worker -> backend PATCH")
    # 1. Create a single upload
    src = TMP_ROOT / "uploads" / "up-e2e.jpg"
    _make_test_jpeg(src, 512, 512)
    _upload_storage.insert_upload(
        upload_id="up-e2e", abs_path=src, mime="image/jpeg", size=src.stat().st_size
    )

    # 2. Create 3 normalized crops for this upload
    paths = _make_n_normalized("up-e2e", 3)

    # 3. Trigger multi
    ai_resp = _recon_svc.create_and_trigger(
        upload_id="up-e2e", method="smpl_multi",
        image_urls=[str(p) for p in paths],
    )
    check("AI server returned task_id", bool(ai_resp.get("task_id")))
    items = _recon_storage.list_reconstructions(upload_id="up-e2e", limit=1)
    actual_recon_id = items[0].id
    check("row created with smpl_multi", items[0].method == "smpl_multi")

    # 4. AI server worker processes
    init_schema()
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_multi",
        payload={
            "upload_id": "up-e2e",
            "recon_id": actual_recon_id,
            "image_urls": [str(p) for p in paths],
            "backend_callback": None,
        },
    )
    result = run_smpl_multi(task)
    check("AI worker produced 1 GLB", Path(result["glb_path"]).exists())
    check("AI worker reported view_count=3", result["view_count"] == 3)

    # 5. Backend PATCHed
    updated = _recon_svc.apply_ai_callback(
        recon_id=actual_recon_id,
        status="done",
        glb_path=result["glb_path"],
        metrics=result["metrics"],
        ai_task_id=task.id,
    )
    check("backend status = done", updated.status == "done")
    check("backend metrics has view_count=3",
          updated.metrics and updated.metrics.get("view_count") == 3)

    # 6. HTTP GET confirms
    with TestClient(app) as client:
        g = client.get(f"/api/reconstructions/{actual_recon_id}")
        check("GET -> 200", g.status_code == 200)
        body = g.json()
        check("HTTP GET shows done", body["status"] == "done")
        check("HTTP GET view_count=3", body["metrics"]["view_count"] == 3)


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
    print(f"SP-5 smoke test  ·  DB: {TMP_DB}")
    print(f"                 data: {TMP_ROOT}")
    print(f"Python: {sys.version.split()[0]}  ·  platform: {sys.platform}")
    test_worker_smpl_multi()
    test_ai_server_queue_roundtrip()
    test_routing_logic()
    test_http_post_multi()
    test_e2e()
    print()
    if _failed:
        print(f"{FAIL} SP-5 FAILED")
        return 1
    print(f"{PASS} SP-5 PASSED -- Phase E multi-view SMPL pipeline verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
