"""SP-2 smoke test — verifies the Phase B dev machine data pipeline.

This script proves:
    1. uploads + reconstructions tables exist in the SQLite schema.
    2. upload_storage CRUD: save_file_to_disk + insert + get + list.
    3. recon_storage CRUD: create + update_status + get + list (with upload_id filter).
    4. POST /api/uploads accepts a multipart file and persists to disk + DB.
    5. GET /api/uploads/{id} returns the upload.
    6. POST /api/reconstructions creates a pending recon row referencing the upload.
    7. E2E: upload -> reconstruction -> patch status='done' -> fetch by id round-trips.

It does NOT call the AI server (that's Phase D). The recon stays in
'pending' until PATCH flips it (we patch manually here to simulate the
Phase D callback).

It does NOT use a real GPU. Runs entirely on the dev machine.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path

# Isolate from the real fitscan.db: redirect DB + data dirs to a temp tree
TMP_ROOT = Path(tempfile.mkdtemp(prefix="fitscan_sp2_"))
TMP_DB = TMP_ROOT / "fitscan.db"
os.environ["FITSCAN_QUEUE_DB"] = str(TMP_DB)  # no-op for backend, but keeps tests hermetic

# Backend uses a module-level _conn in storage.py; we need to import
# everything BEFORE the conn is created so we can monkey-patch DB_PATH
# and data dir if needed. We do that by setting an env var the storage
# module will read.
os.environ["FITSCAN_BACKEND_ROOT"] = str(TMP_ROOT)

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT))

# Monkey-patch storage so its DB file + data dirs live in our temp tree
# (rather than the real backend/ which would pollute the repo).
from app.services import storage as _storage  # noqa: E402
from app.services import upload_storage as _upload_storage  # noqa: E402
from app.services import recon_storage as _recon_storage  # noqa: E402

_storage.DB_PATH = TMP_DB
_storage._conn = None  # force reconnect

_upload_storage.BACKEND_ROOT = TMP_ROOT
_upload_storage.UPLOADS_DIR = TMP_ROOT / "data" / "uploads"

_recon_storage.BACKEND_ROOT = TMP_ROOT
_recon_storage.RECON_DIR = TMP_ROOT / "data" / "reconstructions"

# FastAPI TestClient
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


PASS = "[OK] "
FAIL = "[FAIL] "

_failed = False


def check(name: str, ok: bool, detail: str = "") -> None:
    sym = PASS if ok else FAIL
    print(f"  {sym} {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        global _failed
        _failed = True


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# ─── 1. Schema ───────────────────────────────────────────────────────────────

def test_schema() -> None:
    section("1. uploads + reconstructions schema")
    _storage._init_db(_storage._get_db())
    conn = _storage.get_db()
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    check("uploads table created", "uploads" in tables)
    check("reconstructions table created", "reconstructions" in tables)
    indexes = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='reconstructions'"
        ).fetchall()
    }
    check("recon indexes created", len(indexes) >= 3, f"{len(indexes)} indexes")


# ─── 2. upload_storage CRUD ─────────────────────────────────────────────────

def test_upload_storage() -> None:
    section("2. upload_storage CRUD")
    payload = b"\x89PNG\r\n\x1a\n" + b"fakepngbody" * 10
    up_id, abs_path, size = _upload_storage.save_file_to_disk(
        file_bytes=payload,
        mime="image/png",
        original_filename="test.png",
    )
    check("save_file_to_disk returned id", up_id.startswith("up-"))
    check("save_file_to_disk wrote file", abs_path.exists() and abs_path.read_bytes() == payload)
    check("size matches", size == len(payload), f"{size}")

    item = _upload_storage.insert_upload(
        upload_id=up_id,
        abs_path=abs_path,
        mime="image/png",
        size=size,
        user_id="u-test-1",
    )
    check("insert_upload returns id", item.id == up_id)
    check("insert_upload url set", item.url.startswith("/static/uploads/"))
    check("insert_upload user_id set", item.user_id == "u-test-1")

    got = _upload_storage.get_upload(up_id)
    check("get_upload round-trip", got is not None and got.id == up_id and got.size == size)

    items = _upload_storage.list_uploads(limit=10)
    check("list_uploads returns rows", any(i.id == up_id for i in items))


# ─── 3. recon_storage CRUD ──────────────────────────────────────────────────

def test_recon_storage() -> None:
    section("3. recon_storage CRUD")
    # Need an upload to reference
    up_id, abs_path, size = _upload_storage.save_file_to_disk(
        file_bytes=b"jpeg-bytes",
        mime="image/jpeg",
        original_filename="x.jpg",
    )
    _upload_storage.insert_upload(
        upload_id=up_id, abs_path=abs_path, mime="image/jpeg", size=size
    )

    rec = _recon_storage.create_reconstruction(upload_id=up_id, method="smpl_fast")
    check("create_reconstruction returns pending", rec.status == "pending" and rec.method == "smpl_fast")

    # update_status to done with glb + metrics
    updated = _recon_storage.update_status(
        rec.id,
        status="done",
        glb_path="data/reconstructions/dummy.glb",
        metrics={"chamfer": 1.2, "iterations": 50},
        ai_task_id="rec-aaaa",
    )
    check("update_status -> done", updated is not None and updated.status == "done")
    check("update_status stored glb_path", updated is not None and updated.glb_path is not None)
    check("update_status stored metrics", updated is not None and updated.metrics and updated.metrics.get("chamfer") == 1.2)
    check("update_status stored ai_task_id", updated is not None and updated.ai_task_id == "rec-aaaa")

    # list + filter
    items = _recon_storage.list_reconstructions(limit=10)
    check("list_reconstructions contains new one", any(i.id == rec.id for i in items))
    items_filtered = _recon_storage.list_reconstructions(limit=10, upload_id=up_id)
    check("list_reconstructions filter by upload_id", all(i.upload_id == up_id for i in items_filtered))

    # error path
    bad = False
    try:
        _recon_storage.create_reconstruction(upload_id=up_id, method="smpl_weird")
    except ValueError:
        bad = True
    check("bad method rejected", bad)


# ─── 4. POST /api/uploads (HTTP) ────────────────────────────────────────────

def test_http_post_upload() -> None:
    section("4. POST /api/uploads multipart")
    with TestClient(app) as client:
        files = {"file": ("hello.png", io.BytesIO(b"PNGDATA"), "image/png")}
        data = {"user_id": "u-http-1"}
        r = client.post("/api/uploads", files=files, data=data)
        check("POST /api/uploads -> 201", r.status_code == 201, f"got {r.status_code}")
        body = r.json()
        check("response has id", body.get("id", "").startswith("up-"))
        check("response has url", body.get("url", "").startswith("/static/uploads/"))
        check("response has user_id", body.get("user_id") == "u-http-1")


# ─── 5. GET /api/uploads/{id} ───────────────────────────────────────────────

def test_http_get_upload() -> None:
    section("5. GET /api/uploads/{id}")
    with TestClient(app) as client:
        # Create first
        files = {"file": ("a.jpg", io.BytesIO(b"JPEGDATA"), "image/jpeg")}
        r1 = client.post("/api/uploads", files=files)
        uid = r1.json()["id"]

        r2 = client.get(f"/api/uploads/{uid}")
        check("GET /api/uploads/{id} -> 200", r2.status_code == 200)
        check("returned id matches", r2.json()["id"] == uid)

        r3 = client.get("/api/uploads/up-doesnotexist")
        check("GET unknown -> 404", r3.status_code == 404)


# ─── 6. POST /api/reconstructions ───────────────────────────────────────────

def test_http_post_reconstruction() -> None:
    section("6. POST /api/reconstructions")
    with TestClient(app) as client:
        files = {"file": ("b.png", io.BytesIO(b"PNGDATA2"), "image/png")}
        uid = client.post("/api/uploads", files=files).json()["id"]

        r = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_fast"},
        )
        check("POST /api/reconstructions -> 201", r.status_code == 201, f"got {r.status_code}")
        body = r.json()
        check("recon is pending", body["status"] == "pending")
        check("recon method stored", body["method"] == "smpl_fast")
        check("recon linked to upload", body["upload_id"] == uid)

        # Bad upload_id -> 404
        rbad = client.post(
            "/api/reconstructions",
            json={"upload_id": "up-nope", "method": "smpl_fast"},
        )
        check("POST with bad upload -> 404", rbad.status_code == 404)


# ─── 7. E2E: upload -> reconstruction -> patch done -> fetch ────────────────

def test_e2e() -> None:
    section("7. E2E: upload + reconstruction + patch + fetch")
    with TestClient(app) as client:
        # 1. Upload
        files = {"file": ("e2e.png", io.BytesIO(b"E2EBODY" * 100), "image/png")}
        up_resp = client.post("/api/uploads", files=files).json()
        uid = up_resp["id"]
        check("upload created", uid.startswith("up-"))

        # 2. Create reconstruction
        rec_resp = client.post(
            "/api/reconstructions",
            json={"upload_id": uid, "method": "smpl_fast"},
        ).json()
        rid = rec_resp["id"]
        check("reconstruction created", rid.startswith("rec-") and rec_resp["status"] == "pending")

        # 3. Patch to done (simulates Phase D callback)
        patch = client.patch(
            f"/api/reconstructions/{rid}",
            json={
                "status": "done",
                "glb_path": "data/reconstructions/e2e.glb",
                "metrics": {"chamfer": 0.5},
            },
        )
        check("PATCH -> 200", patch.status_code == 200)
        check("PATCH stored status", patch.json()["status"] == "done")
        check("PATCH stored glb_url", "/assets/glb/" in patch.json().get("glb_url", ""))

        # 4. Fetch back
        got = client.get(f"/api/reconstructions/{rid}").json()
        check("GET by id round-trips", got["id"] == rid and got["status"] == "done")

        # 5. List
        lst = client.get("/api/reconstructions?limit=5").json()
        check("recon list contains ours", any(r["id"] == rid for r in lst))

        up_list = client.get("/api/uploads?limit=5").json()
        check("upload list contains ours", any(u["id"] == uid for u in up_list))


# ─── main ───────────────────────────────────────────────────────────────────

def main() -> int:
    print(f"SP-2 smoke test  ·  DB: {TMP_DB}  ·  data: {TMP_ROOT}")
    print(f"Python: {sys.version.split()[0]}  ·  platform: {sys.platform}")
    test_schema()
    test_upload_storage()
    test_recon_storage()
    test_http_post_upload()
    test_http_get_upload()
    test_http_post_reconstruction()
    test_e2e()
    print()
    if _failed:
        print(f"{FAIL} SP-2 FAILED")
        return 1
    print(f"{PASS} SP-2 PASSED — Phase B dev machine data pipeline verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
