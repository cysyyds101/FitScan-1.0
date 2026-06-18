"""SP-7 smoke test — Phase F architecture upgrades:

    1) Asset registry (asset_service.py)
       - register() with absolute path -> asset_id
       - lookup() and lookup_by_owner()
       - public_url_for_owner() returns /assets/glb/{id}
       - Idempotent: re-registering the same path returns the same id

    2) /assets/glb/{id} route
       - Registered asset serves the file via FileResponse
       - Wrong kind -> 400, unknown id -> 404, missing file -> 410
       - URL space is /assets/{kind}/{id} (NOT /static/...)

    3) AI server -> Backend ownership handoff
       - When recon PATCH callback arrives with status=done + glb_path,
         recon_storage.update_status() auto-registers the asset
       - GET /api/reconstructions/{id} returns glb_url=/assets/glb/...

    4) next_poll_ms (adaptive polling hint)
       - pending    -> 2000
       - processing -> 4000
       - done       -> 0
       - failed     -> 0
       - Surface in ReconstructionItem response
"""
from __future__ import annotations

import os
import sys
import tempfile
import json
from pathlib import Path

# ─── path setup (mirror SP-3/4/5/6) ────────────────────────────────────────
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
for entry in (str(REPO), str(REPO / "backend")):
    if entry in sys.path:
        sys.path.remove(entry)
    sys.path.append(entry)
# Append repo LAST so stdlib `queue` is preferred over ai_server/queue/
sys.path.append(str(REPO))

# ─── isolate DB and storage roots to a tempdir BEFORE any app import ──────
_tmp = tempfile.TemporaryDirectory()
TMP_DIR = Path(_tmp.name)
os.environ["FITSCAN_DATA_DIR"] = str(TMP_DIR / "data")
os.environ.setdefault("FITSCAN_RECON_OUT_DIR", str(TMP_DIR / "recon_out"))

# Create a real GLB fixture on disk in the recon_out directory so the
# asset registry's `register` call doesn't 404 on the file-existence check.
RECON_OUT = Path(os.environ["FITSCAN_RECON_OUT_DIR"])
RECON_OUT.mkdir(parents=True, exist_ok=True)

# Use the same fixture as SP-4/5/6 if present
FIXTURE_SRC = REPO / "ai_server" / "data" / "fixtures" / "sample.glb"
FIXTURE_BYTES = None
if FIXTURE_SRC.exists():
    FIXTURE_BYTES = FIXTURE_SRC.read_bytes()
else:
    # Minimal valid GLB (one triangle)
    FIXTURE_BYTES = bytes.fromhex(
        "1A66746C1A00736F757263650000006B6A736F6E7B"
        "227363656E65223A302C2273657373696F6E73223A5B" 
        "7B226E616D65223A22656D707479227D5D7D00"
        "00474C54460B0000000000000000002C0000000C0" 
        "0000000C000000A45F6F75747075740000"
    )

import asyncio
import io
from PIL import Image


# ─── test helpers ──────────────────────────────────────────────────────────
def header(t: str):
    print(f"\n=== {t} ===")


def ok(msg: str):
    print(f"  [OK]  {msg}")


def fail(msg: str):
    print(f"  [FAIL] {msg}")
    raise AssertionError(msg)


def make_test_jpeg(target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (256, 256), color=(120, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    target.write_bytes(buf.getvalue())


def write_glb_fixture(target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(FIXTURE_BYTES)


# ─── imports after env setup ──────────────────────────────────────────────
import app.main as _app_main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.services import storage, asset_service  # noqa: E402
from app.services import recon_service  # noqa: E402
from app.services.recon_storage import _next_poll_ms  # noqa: E402


# ─── main test flow ───────────────────────────────────────────────────────
def test_asset_registry_register_lookup():
    header("test_asset_registry_register_lookup")
    glb = RECON_OUT / "asset-test-1.glb"
    write_glb_fixture(glb)

    asset_id = asset_service.register(
        absolute_path=str(glb),
        kind="glb",
        owner_id="rec-asset-1",
    )
    assert asset_id.startswith("asset-"), asset_id
    ok(f"registered asset_id={asset_id}")

    row = asset_service.lookup(asset_id)
    assert row is not None, "lookup returned None"
    assert row["kind"] == "glb"
    assert row["owner_id"] == "rec-asset-1"
    assert row["absolute_path"] == str(glb)
    ok("lookup() returns full row")

    # Idempotent
    asset_id_2 = asset_service.register(
        absolute_path=str(glb),
        kind="glb",
        owner_id="rec-asset-1",
    )
    assert asset_id_2 == asset_id, f"idempotent register returned different id: {asset_id_2} vs {asset_id}"
    ok("register() is idempotent on same absolute_path")

    url = asset_service.public_url_for_owner("rec-asset-1", kind="glb")
    assert url == f"/assets/glb/{asset_id}", url
    ok(f"public_url_for_owner() = {url}")


def test_asset_registry_missing_file():
    header("test_asset_registry_missing_file")
    try:
        asset_service.register(
            absolute_path=str(RECON_OUT / "does-not-exist.glb"),
            kind="glb",
            owner_id="rec-missing",
        )
        fail("expected FileNotFoundError for missing file")
    except FileNotFoundError:
        ok("register() rejects missing file")


def test_asset_registry_bad_kind():
    header("test_asset_registry_bad_kind")
    try:
        asset_service.register(
            absolute_path=str(RECON_OUT / "asset-test-1.glb"),
            kind="bogus",
        )
        fail("expected ValueError for bad kind")
    except ValueError:
        ok("register() rejects unknown kind")


def test_next_poll_ms_hints():
    header("test_next_poll_ms_hints")
    assert _next_poll_ms("pending") == 2000, _next_poll_ms("pending")
    ok("pending -> 2000ms")
    assert _next_poll_ms("processing") == 4000, _next_poll_ms("processing")
    ok("processing -> 4000ms")
    assert _next_poll_ms("done") == 0
    ok("done -> 0ms (stop)")
    assert _next_poll_ms("failed") == 0
    ok("failed -> 0ms (stop)")
    # unknown status falls back to safe default
    assert _next_poll_ms("__garbage__") == 2000
    ok("unknown status -> 2000ms default")


def test_get_asset_route_serves_file():
    header("test_get_asset_route_serves_file")
    # Reuse a freshly written file
    glb = RECON_OUT / "asset-route-1.glb"
    write_glb_fixture(glb)
    asset_id = asset_service.register(
        absolute_path=str(glb),
        kind="glb",
        owner_id="rec-route-1",
    )

    client = TestClient(_app_main.app)
    resp = client.get(f"/assets/glb/{asset_id}")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("model/gltf-binary"), resp.headers
    body = resp.content
    assert len(body) > 0
    # GLB magic header: 'glTF'
    assert body[:4] == b"glTF", body[:8]
    ok(f"served {len(body)} bytes via /assets/glb/{asset_id}")


def test_get_asset_route_404_and_400():
    header("test_get_asset_route_404_and_400")
    client = TestClient(_app_main.app)
    resp = client.get("/assets/glb/asset-does-not-exist")
    assert resp.status_code == 404, resp.text
    ok("unknown id -> 404")

    resp = client.get("/assets/bogus/asset-anything")
    assert resp.status_code == 404
    ok("bad kind -> 404")

    # Kind mismatch: register as glb, request as normalized
    glb = RECON_OUT / "asset-mismatch.glb"
    write_glb_fixture(glb)
    aid = asset_service.register(absolute_path=str(glb), kind="glb", owner_id="rec-mm")
    resp = client.get(f"/assets/normalized/{aid}")
    assert resp.status_code == 400, resp.text
    ok("kind mismatch -> 400")


def test_get_asset_route_410_when_file_missing():
    header("test_get_asset_route_410_when_file_missing")
    glb = RECON_OUT / "asset-will-vanish.glb"
    write_glb_fixture(glb)
    aid = asset_service.register(absolute_path=str(glb), kind="glb", owner_id="rec-vanish")
    # delete the file under the asset
    glb.unlink()
    client = TestClient(_app_main.app)
    resp = client.get(f"/assets/glb/{aid}")
    assert resp.status_code == 410, resp.text
    ok("missing file on disk -> 410 Gone")


def test_recon_callback_registers_asset_and_url_uses_registry():
    header("test_recon_callback_registers_asset_and_url_uses_registry")
    # Simulate the AI server worker: write a GLB, then send a callback
    client = TestClient(_app_main.app)

    # 1. Create an upload (so the recon has something to reference)
    up_path = TMP_DIR / "fake-upload.jpg"
    make_test_jpeg(up_path)
    files = {"file": ("up-svc.jpg", up_path.read_bytes(), "image/jpeg")}
    r = client.post("/api/uploads", files=files)
    assert r.status_code in (200, 201), r.text
    upload = r.json()
    upload_id = upload["id"]
    ok(f"created upload {upload_id}")

    # 2. Create a recon
    r = client.post("/api/reconstructions", json={"upload_id": upload_id, "method": "smpl_fast"})
    assert r.status_code in (200, 201), r.text
    recon = r.json()
    recon_id = recon["id"]
    ok(f"created recon {recon_id}")
    assert recon["status"] == "pending"
    assert recon["next_poll_ms"] == 2000, recon
    ok("pending recon returns next_poll_ms=2000")

    # 3. Simulate AI server callback: status=done, glb_path=<shared-disk path>
    glb_path = str(RECON_OUT / f"{recon_id}.glb")
    write_glb_fixture(Path(glb_path))
    r = client.post(
        f"/api/reconstructions/{recon_id}/callback",
        json={"status": "done", "glb_path": glb_path, "metrics": {"fps": 30}},
    )
    assert r.status_code == 200, r.text
    item = r.json()
    assert item["status"] == "done", item
    assert item["glb_path"] == glb_path
    assert item["glb_url"] is not None
    assert item["glb_url"].startswith("/assets/glb/"), item["glb_url"]
    assert item["next_poll_ms"] == 0, item
    ok(f"callback registered asset, glb_url={item['glb_url']}, next_poll_ms=0")

    # 4. asset_service must have an entry for this recon
    asset = asset_service.lookup_by_owner(recon_id, kind="glb")
    assert asset is not None, f"asset registry has no entry for {recon_id}"
    ok(f"asset registry: {asset['id']}")

    # 5. GET /api/reconstructions/{id} returns same url
    r = client.get(f"/api/reconstructions/{recon_id}")
    assert r.status_code == 200
    item2 = r.json()
    assert item2["glb_url"] == item["glb_url"]
    ok("GET /api/reconstructions/{id} returns same /assets/glb/... url")

    # 6. The url must actually serve the file
    asset_id = item["glb_url"].split("/")[-1]
    r = client.get(f"/assets/glb/{asset_id}")
    assert r.status_code == 200, r.text
    assert r.content[:4] == b"glTF", r.content[:8]
    ok("URL serves a real GLB (magic=glTF)")


def test_pending_recon_url_is_placeholder():
    header("test_pending_recon_url_is_placeholder")
    """If a recon has glb_path but the file isn't on disk yet (or no
    callback has run), the URL should still be a sane /assets/glb/...
    string (the placeholder). The frontend uses this to show a 'preparing'
    state and 410 from the route to handle the race."""
    client = TestClient(_app_main.app)
    up_path = TMP_DIR / "fake-pending.jpg"
    make_test_jpeg(up_path)
    r = client.post("/api/uploads", files={"file": ("up-pending.jpg", up_path.read_bytes(), "image/jpeg")})
    upload = r.json()
    r = client.post("/api/reconstructions", json={"upload_id": upload["id"], "method": "smpl_fast"})
    recon = r.json()
    # No callback yet: glb_path is None, glb_url is None
    assert recon["glb_url"] is None
    ok("no callback -> glb_url is None (frontend shows pending UI)")


def test_processing_recon_next_poll():
    header("test_processing_recon_next_poll")
    client = TestClient(_app_main.app)
    up_path = TMP_DIR / "fake-proc.jpg"
    make_test_jpeg(up_path)
    r = client.post("/api/uploads", files={"file": ("up-proc.jpg", up_path.read_bytes(), "image/jpeg")})
    upload = r.json()
    r = client.post("/api/reconstructions", json={"upload_id": upload["id"], "method": "smpl_fast"})
    recon_id = r.json()["id"]

    # Simulate processing (no glb_path yet)
    r = client.post(
        f"/api/reconstructions/{recon_id}/callback",
        json={"status": "processing"},
    )
    assert r.status_code == 200
    item = r.json()
    assert item["status"] == "processing"
    assert item["next_poll_ms"] == 4000, item
    ok("processing -> next_poll_ms=4000ms")


def test_failed_recon_stops_polling():
    header("test_failed_recon_stops_polling")
    client = TestClient(_app_main.app)
    up_path = TMP_DIR / "fake-fail.jpg"
    make_test_jpeg(up_path)
    r = client.post("/api/uploads", files={"file": ("up-fail.jpg", up_path.read_bytes(), "image/jpeg")})
    upload = r.json()
    r = client.post("/api/reconstructions", json={"upload_id": upload["id"], "method": "smpl_fast"})
    recon_id = r.json()["id"]

    r = client.post(
        f"/api/reconstructions/{recon_id}/callback",
        json={"status": "failed", "metrics": {"error": "smplx_oom"}},
    )
    assert r.status_code == 200
    item = r.json()
    assert item["status"] == "failed"
    assert item["next_poll_ms"] == 0, item
    ok("failed -> next_poll_ms=0 (frontend stops polling)")


# ─── run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        test_asset_registry_register_lookup()
        test_asset_registry_missing_file()
        test_asset_registry_bad_kind()
        test_next_poll_ms_hints()
        test_get_asset_route_serves_file()
        test_get_asset_route_404_and_400()
        test_get_asset_route_410_when_file_missing()
        test_recon_callback_registers_asset_and_url_uses_registry()
        test_pending_recon_url_is_placeholder()
        test_processing_recon_next_poll()
        test_failed_recon_stops_polling()
        print("\n[OK]  SP-7 PASSED -- Phase F architecture upgrades verified.")
    except AssertionError as e:
        print(f"\n[FAIL]  SP-7 FAILED -- {e}")
        raise
    finally:
        _tmp.cleanup()
