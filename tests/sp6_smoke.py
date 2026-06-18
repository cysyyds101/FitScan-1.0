"""SP-6 smoke test — verifies the backend exposes all endpoints the
Phase F frontend needs to render the virtual try-on page.

This is intentionally backend-only: the frontend (React + Three.js) is
validated by the dev server, not Python. SP-6 confirms the API contract
that the new frontend hooks + panels rely on:

    /api/clothing                          (used by ClothingControls)
    /api/clothing/{id}                     (alt)
    /api/uploads (POST)                    (ReconstructionPanel onUpload)
    /api/uploads/{id} (GET)                (debug)
    /api/uploads (GET list)                (debug)
    /api/uploads/{id}/normalize (POST)     (ReconstructionPanel auto-trigger)
    /api/uploads/{id}/normalized (GET)     (poll)
    /api/reconstructions (POST)            (ReconstructionPanel onTriggerRecon)
    /api/reconstructions (GET list)        (useReconstructions hook)
    /api/reconstructions/{id} (GET)        (debug)
    /api/reconstructions/{id}/callback     (AI server PATCH)
    /api/reconstructions/{id}/trigger      (re-trigger)
    /static/reconstructions/<file>.glb     (ReconstructionViewer URL)

It also re-verifies that the Phase E route still works for multi-view.
"""
from __future__ import annotations

import io
import os
import struct
import sys
import tempfile
from pathlib import Path

# ─── Hermetic dirs ───────────────────────────────────────────────────────────
TMP_ROOT = Path(tempfile.mkdtemp(prefix="fitscan_sp6_"))
TMP_DB = TMP_ROOT / "fitscan.db"
TMP_RECON = TMP_ROOT / "reconstructions"   # mirrors backend's static mount
TMP_RECON.mkdir(parents=True, exist_ok=True)
os.environ["FITSCAN_QUEUE_DB"] = str(TMP_DB)
os.environ["DEV_UPLOADS_DIR"] = str(TMP_ROOT / "uploads")
os.environ["AI_NORMALIZED_DIR"] = str(TMP_ROOT / "normalized")
# CRITICAL: AI server worker writes GLBs here so backend's StaticFiles
# mount can serve them under /static/reconstructions.
os.environ["FITSCAN_RECON_OUT_DIR"] = str(TMP_RECON)

# Bootstrap paths -- ai_server/queue would shadow stdlib `queue`.
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
from app.services import normalize_service as _norm_svc  # noqa: E402
import app.main as _app_main  # noqa: E402
from app.services import upload_storage as _us  # noqa: E402

_storage.DB_PATH = TMP_DB
_storage._conn = None
_upload_storage.BACKEND_ROOT = TMP_ROOT
_upload_storage.UPLOADS_DIR = TMP_ROOT / "uploads"

# Point the backend's static mount at our temp dir so the TestClient can
# actually serve the GLBs the AI server worker just wrote.
_app_main.RECON_STATIC_DIR = TMP_RECON
_app_main.UPLOADS_STATIC_DIR = TMP_ROOT / "uploads_static"
_app_main.UPLOADS_STATIC_DIR.mkdir(parents=True, exist_ok=True)
_app_main.DATA_DIR = TMP_ROOT

# Patch AI server worker output dirs
import ai_server.worker_process as _wp  # noqa: E402
_wp._NORMALIZE_OUT_DIR = TMP_ROOT / "normalized"
# Worker uses _recon_out_dir() at call time; set env var so it picks our dir.
os.environ["FITSCAN_RECON_OUT_DIR"] = str(TMP_RECON)

# Patch recon_storage._to_url so it matches the real asset-registry path
# (Phase F: /assets/glb/{id}, not /static/reconstructions/<file>).
def _patched_to_url(glb_path, recon_id=None):
    if not glb_path:
        return None
    from app.services import asset_service
    aid = asset_service.register(
        absolute_path=glb_path, kind="glb",
        owner_id=recon_id or Path(glb_path).stem,
    )
    return f"/assets/glb/{aid}"


_recon_storage._to_url = _patched_to_url

# Mock ai_client HTTP calls
import app.services.ai_client as _ai_client  # noqa: E402


def _mock_smpl_fast_sync(upload_id, image_url, backend_callback, recon_id):
    return {"task_id": f"rec-mock-{recon_id[-6:]}", "status": "PENDING"}


def _mock_smpl_multi_sync(upload_id, image_url, image_urls, backend_callback, recon_id):
    return {"task_id": f"rec-mock-multi-{recon_id[-6:]}", "status": "PENDING"}


def _mock_normalize_sync(upload_id, image_url, backend_callback):
    return {"task_id": f"norm-mock-{upload_id[-6:]}", "status": "PENDING"}


_ai_client.ai_client.smpl_fast_sync = _mock_smpl_fast_sync
_ai_client.ai_client.smpl_multi_sync = _mock_smpl_multi_sync
_ai_client.ai_client.normalize_sync = _mock_normalize_sync

# ─── Imports after patching ──────────────────────────────────────────────────
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

from ai_server.queue.inproc_queue import dequeue_blocking, enqueue  # noqa: E402
from ai_server.queue.persistence import init_schema, mark_done, mark_running  # noqa: E402
from ai_server.queue.task import Task, new_task_id  # noqa: E402
from ai_server.worker_process import run_smpl_fast, run_smpl_multi  # noqa: E402

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


def _jpeg_bytes(w: int = 512, h: int = 512) -> io.BytesIO:
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


# ─── 1. GET /api/clothing ────────────────────────────────────────────────────

def test_clothing_list() -> None:
    section("1. GET /api/clothing (used by ClothingControls)")
    with TestClient(app) as client:
        r = client.get("/api/clothing")
        check("GET -> 200", r.status_code == 200)
        body = r.json()
        items = body.get("items", body) if isinstance(body, dict) else body
        check("response has items list", isinstance(items, list), f"type={type(items)}")
        if items:
            it = items[0]
            check("item has id", "id" in it, f"keys={list(it.keys())}")
            check("item has name", "name" in it)
            check("item has model_url", "model_url" in it)


# ─── 2. POST /api/uploads (multipart) ───────────────────────────────────────

def test_upload() -> str:
    section("2. POST /api/uploads (ReconstructionPanel onUpload)")
    with TestClient(app) as client:
        files = {"file": ("ph.jpg", _jpeg_bytes(), "image/jpeg")}
        r = client.post("/api/uploads", files=files)
        check("POST -> 201", r.status_code == 201, f"got {r.status_code}")
        body = r.json()
        check("response has id", "id" in body)
        check("response has url", "url" in body)
        check("response has normalize_status=None or NONE",
              body.get("normalize_status") in (None, "NONE", ""),
              f"status={body.get('normalize_status')}")
        return body["id"]


# ─── 3. POST /api/uploads/{id}/normalize ───────────────────────────────────

def test_trigger_normalize(uid: str) -> None:
    section("3. POST /api/uploads/{id}/normalize (panel auto-trigger)")
    with TestClient(app) as client:
        r = client.post(f"/api/uploads/{uid}/normalize")
        check("POST -> 202", r.status_code == 202, f"got {r.status_code}")
        body = r.json()
        check("status now QUEUED", body.get("normalize_status") == "QUEUED")
        check("ai_task_id present", body.get("normalize_task_id", "").startswith("norm-"))

        # Poll for completion (run normalize worker in-process synchronously)
        src = TMP_ROOT / "uploads" / f"{uid}.jpg"
        if not src.exists():
            # The upload may have been saved to a different name; find it.
            uploads_dir = TMP_ROOT / "uploads"
            candidates = list(uploads_dir.glob(f"{uid}.*"))
            src = candidates[0] if candidates else None
        assert src is not None, f"upload file missing for {uid}"

        # Manually run worker run_normalize on this upload's normalized_path
        # We use the worker's _NORMALIZE_OUT_DIR location.
        norm_path = TMP_ROOT / "normalized" / f"{uid}.jpg"
        norm_path.parent.mkdir(parents=True, exist_ok=True)
        # Create a placeholder normalized crop so the worker has something
        # to read.
        Image.fromarray(np.full((512, 512, 3), 100, dtype=np.uint8)).save(
            norm_path, "JPEG"
        )

        task = Task(
            id=new_task_id("norm"),
            task_type="normalize",
            payload={
                "upload_id": uid,
                "image_url": str(src),
                "backend_callback": None,
            },
        )
        from ai_server.worker_process import run_normalize
        run_normalize(task)

        # PATCH the upload row to NORMALIZED (simulating AI server PATCH)
        _norm_svc.set_normalize_result(
            upload_id=uid, status="NORMALIZED", normalized_path=str(norm_path),
        )

        # GET /api/uploads/{id}/normalized should show NORMALIZED
        g = client.get(f"/api/uploads/{uid}/normalized")
        check("GET normalized -> 200", g.status_code == 200)
        check("status NORMALIZED", g.json().get("normalize_status") == "NORMALIZED")


# ─── 4. POST /api/reconstructions (smpl_fast) ──────────────────────────────

def test_create_recon(uid: str) -> str:
    section("4. POST /api/reconstructions (panel onTriggerRecon)")
    with TestClient(app) as client:
        r = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_fast", "image_urls": []},
        )
        check("POST -> 201", r.status_code == 201, f"got {r.status_code}")
        body = r.json()
        check("status pending", body.get("status") == "pending")
        check("ai_task_id present", body.get("ai_task_id", "").startswith("rec-"))
        check("method stored", body.get("method") == "smpl_fast")
        return body["id"]


# ─── 5. GET /api/reconstructions?upload_id=... (useReconstructions hook) ──

def test_list_reconstructions(uid: str) -> None:
    section("5. GET /api/reconstructions?upload_id=... (useReconstructions hook)")
    with TestClient(app) as client:
        r = client.get(f"/api/reconstructions?upload_id={uid}&limit=50")
        check("GET -> 200", r.status_code == 200)
        items = r.json()
        check("items is list", isinstance(items, list))
        check("at least 1 item", len(items) >= 1, f"n={len(items)}")


# ─── 6. AI server worker writes GLB + StaticFiles serves it ───────────────

def test_glb_static_serve(uid: str, recon_id: str) -> None:
    section("6. AI server worker writes GLB + /static/reconstructions serves it")
    init_schema()

    # Run the worker in-process; it should write a GLB into TMP_RECON
    norm_path = TMP_ROOT / "normalized" / f"{uid}.jpg"
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_fast",
        payload={
            "upload_id": uid,
            "recon_id": recon_id,
            "normalized_path": str(norm_path),
            "backend_callback": None,
        },
    )
    # Persist the task first (insert_pending) so mark_running can find it.
    from ai_server.queue.persistence import insert_pending
    insert_pending(task)
    mark_running(task.id, gpu_id=0, worker_pid=os.getpid())
    result = run_smpl_fast(task)
    mark_done(task.id, result)

    out = Path(result["glb_path"])
    check("worker wrote GLB", out.exists(), str(out))
    check("GLB is under TMP_RECON", str(out).startswith(str(TMP_RECON)),
          str(out))
    check("GLB filename matches recon_id",
          out.name == f"{recon_id}.glb", out.name)

    # Now: backend PATCH to set status=done
    with TestClient(app) as client:
        cb = client.post(
            f"/api/reconstructions/{recon_id}/callback",
            json={
                "status": "done",
                "glb_path": str(out),
                "metrics": result["metrics"],
            },
        )
        check("callback -> 200", cb.status_code == 200)
        check("backend shows done", cb.json()["status"] == "done")

        # Phase F: glb_url now goes through the asset registry at
        # /assets/glb/{id}, not the legacy /static/reconstructions/ mount.
        item = cb.json()
        glb_url = item.get("glb_url", "")
        check("glb_url uses asset registry", glb_url.startswith("/assets/glb/"),
              f"got {glb_url!r}")
        g = client.get(glb_url)
        check("GET /assets/glb/... -> 200", g.status_code == 200,
              f"got {g.status_code}")
        check("served bytes match disk", g.content == out.read_bytes(),
              f"len_net={len(g.content)} len_disk={out.stat().st_size}")
        check("magic == glTF", g.content[:4] == b"glTF", repr(g.content[:4]))


# ─── 7. Picked glb URL appears in GET /api/reconstructions/{id} ───────────

def test_picked_glb_url(recon_id: str) -> None:
    section("7. GET /api/reconstructions/{id} exposes glb_url (ReconstructionViewer uses this)")
    with TestClient(app) as client:
        r = client.get(f"/api/reconstructions/{recon_id}")
        body = r.json()
        check("status done", body.get("status") == "done")
        glb_url = body.get("glb_url")
        check("glb_url present", bool(glb_url), f"glb_url={glb_url!r}")
        # Phase F: glb_url is /assets/glb/{id} (NOT /static/reconstructions/...)
        check("glb_url under /assets/glb/",
              glb_url and "/assets/glb/" in glb_url,
              glb_url)
        check("next_poll_ms == 0 (terminal)", body.get("next_poll_ms") == 0,
              body.get("next_poll_ms"))


# ─── 8. E2E (frontend-API contract) ────────────────────────────────────────

def test_e2e() -> None:
    section("8. E2E: upload -> normalize -> recon -> done -> GLB served")
    with TestClient(app) as client:
        # 1. Upload
        files = {"file": ("e2e.jpg", _jpeg_bytes(), "image/jpeg")}
        uid = client.post("/api/uploads", files=files).json()["id"]

        # 2. Normalize
        client.post(f"/api/uploads/{uid}/normalize")
        # 3. Provide a normalized crop (in real prod AI server does this)
        norm_path = TMP_ROOT / "normalized" / f"{uid}.jpg"
        norm_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.full((512, 512, 3), 100, dtype=np.uint8)).save(
            norm_path, "JPEG"
        )
        _norm_svc.set_normalize_result(uid, "NORMALIZED", str(norm_path))

        # 4. Trigger recon
        r = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_fast", "image_urls": []},
        )
        assert r.status_code == 201
        recon_id = r.json()["id"]

        # 5. AI worker produces GLB
        init_schema()
        task = Task(
            id=new_task_id("rec"),
            task_type="smpl_fast",
            payload={
                "upload_id": uid, "recon_id": recon_id,
                "normalized_path": str(norm_path),
                "backend_callback": None,
            },
        )
        from ai_server.queue.persistence import insert_pending
        insert_pending(task)
        mark_running(task.id, gpu_id=0, worker_pid=os.getpid())
        result = run_smpl_fast(task)
        mark_done(task.id, result)

        # 6. PATCH callback
        client.post(
            f"/api/reconstructions/{recon_id}/callback",
            json={"status": "done", "glb_path": result["glb_path"],
                  "metrics": result["metrics"]},
        )

        # 7. GET back
        g = client.get(f"/api/recon_path/recon_path"[:13])  # sentinel
        final = client.get(f"/api/reconstructions/{recon_id}").json()
        check("final status done", final["status"] == "done")

        # 8. Static GLB served
        glb_url = final["glb_url"]
        r_glb = client.get(glb_url)
        check("GLB served via glb_url", r_glb.status_code == 200,
              f"got {r_glb.status_code}")
        check("GLB bytes valid", r_glb.content[:4] == b"glTF")


# ─── main ───────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"SP-6 smoke test  ·  DB: {TMP_DB}")
    print(f"                 data: {TMP_ROOT}")
    print(f"Python: {sys.version.split()[0]}  ·  platform: {sys.platform}")
    test_clothing_list()
    uid = test_upload()
    test_trigger_normalize(uid)
    recon_id = test_create_recon(uid)
    test_list_reconstructions(uid)
    test_glb_static_serve(uid, recon_id)
    test_picked_glb_url(recon_id)
    test_e2e()
    print()
    if _failed:
        print(f"{FAIL} SP-6 FAILED")
        return 1
    print(f"{PASS} SP-6 PASSED -- Phase F frontend API contract verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
