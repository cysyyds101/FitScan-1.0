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
from pathlib import Path
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


# ─── Task dispatch ──────────────────────────────────────────────────────────

# Where normalized crops land. AI server-side, NOT dev machine.
# Phase D's SMPLer-X worker reads from here.
_NORMALIZE_OUT_DIR = Path(__file__).resolve().parent / "data" / "normalized"
_NORMALIZE_SIZE = 512
_NORMALIZE_PADDING = 1.1  # crop square side = max(w, h) * padding

# Where reconstructed GLBs land. AI server-side; dev machine mounts via
# /static/reconstructions in prod (shared volume) or via callback in tests.
_RECON_OUT_DIR = Path(__file__).resolve().parent / "data" / "reconstructions"
_GLTF_FIXTURE = Path(__file__).resolve().parent / "data" / "fixtures" / "sample.glb"


def _resolve_source_path(image_url: str | None, upload_id: str) -> Path:
    """Map image_url or upload_id to a readable file on disk.

    Supports:
        - file:// URLs and absolute paths
        - http(s):// URLs (downloads to a temp cache)
        - plain upload_id 'up-xxx' (resolves under dev machine uploads dir)
    """
    if image_url:
        if image_url.startswith("file://"):
            return Path(image_url[len("file://"):])
        if image_url.startswith(("http://", "https://")):
            raise ValueError(
                f"http(s) image_url not supported in this build: {image_url}"
            )
        p = Path(image_url)
        if p.is_absolute() and p.exists():
            return p

    # Fallback: dev machine uploads dir (shared via NFS / volume in prod)
    # We respect $DEV_UPLOADS_DIR override so tests can isolate.
    dev_dir = Path(os.environ.get("DEV_UPLOADS_DIR", "")).resolve()
    if upload_id and dev_dir:
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            cand = dev_dir / f"{upload_id}{ext}"
            if cand.exists():
                return cand
    raise FileNotFoundError(f"cannot resolve source for upload_id={upload_id} image_url={image_url}")


def run_normalize(task: Task) -> dict[str, Any]:
    """Phase C handler: PIL-only 512x512 centered human crop.

    Pipeline (no torch / no CUDA / no SMPL):
        1. Open image with PIL.
        2. Convert to grayscale + Otsu threshold (PIL ImageOps).
        3. Find non-zero bbox of subject.
        4. Center-crop a square = max(w, h) * 1.1 around bbox center.
        5. Resize to 512x512, save as JPEG.
        6. If backend_callback set, PATCH it with the result.
    """
    from PIL import Image, ImageOps  # local import keeps startup fast
    import io
    import json
    try:
        import httpx
    except ImportError:
        httpx = None

    upload_id = task.payload.get("upload_id", "")
    image_url = task.payload.get("image_url")
    backend_callback = task.payload.get("backend_callback")

    src = _resolve_source_path(image_url, upload_id)
    img = Image.open(src).convert("RGB")

    # Otsu threshold on grayscale to find subject bbox
    gray = img.convert("L")
    thresholded = ImageOps.autocontrast(gray)  # improve contrast first
    thresh = thresholded.point(lambda p: 255 if p > 110 else 0)  # crude binarization
    bbox = thresh.getbbox()

    if bbox is None:
        # No clear subject found — fall back to center-crop whole image
        bbox = (0, 0, img.width, img.height)
        padding = 1.0
    else:
        padding = _NORMALIZE_PADDING

    # Square crop centered on bbox
    x0, y0, x1, y1 = bbox
    bw, bh = x1 - x0, y1 - y0
    cx, cy = x0 + bw // 2, y0 + bh // 2
    side = int(max(bw, bh) * padding)
    # Clamp to image bounds
    half = side // 2
    crop_box = (
        max(0, cx - half),
        max(0, cy - half),
        min(img.width, cx - half + side),
        min(img.height, cy - half + side),
    )
    cropped = img.crop(crop_box)
    # Make sure final is exactly 512x512
    cropped = cropped.resize((_NORMALIZE_SIZE, _NORMALIZE_SIZE), Image.LANCZOS)

    _NORMALIZE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _NORMALIZE_OUT_DIR / f"{upload_id}.jpg"
    cropped.save(out_path, format="JPEG", quality=92)

    result = {
        "upload_id": upload_id,
        "normalized_path": str(out_path),
        "width": _NORMALIZE_SIZE,
        "height": _NORMALIZE_SIZE,
        "source": str(src),
        "bbox": list(bbox),
    }

    # Optional: PATCH backend to update the uploads row
    if backend_callback and httpx is not None:
        try:
            httpx.patch(
                backend_callback,
                json={
                    "status": "NORMALIZED",
                    "normalized_path": str(out_path),
                    "task_id": task.id,
                },
                timeout=10.0,
            )
        except Exception as e:
            logger.warning(f"[worker normalize] backend_callback PATCH failed: {e}")
    elif backend_callback and httpx is None:
        logger.warning("[worker normalize] httpx missing; skipping backend_callback PATCH")

    return result


def _patch_backend(callback: str, payload: dict) -> None:
    """Best-effort PATCH to the dev machine. Skips on missing httpx."""
    try:
        import httpx
    except ImportError:
        logger.warning("[worker] httpx missing; skipping backend PATCH")
        return
    try:
        httpx.patch(callback, json=payload, timeout=10.0)
    except Exception as e:
        logger.warning(f"[worker] backend PATCH failed ({callback}): {e}")


def run_smpl_fast(task: Task) -> dict[str, Any]:
    """Phase D handler: SMPL reconstruction from a normalized crop.

    In production this would:
        1. Load the normalized crop (PIL).
        2. Run SMPLer-X / HMR2.0 / CLIFF (PyTorch) to get SMPL params.
        3. Forward-kinemat the SMPL mesh to get a posed body.
        4. Export to GLB (trimesh / pygltflib).

    In this build (dev machine has no GPU / no model weights) we substitute
    a "mock inference" that:
        1. Verifies the normalized crop exists.
        2. Copies the GLTF fixture to <RECON_OUT_DIR>/<recon_id>.glb.
        3. Reports a deterministic metrics dict so SP-4 can verify.

    The dispatcher + queue + backend callback path is fully exercised
    either way; only the GPU call is stubbed.
    """
    upload_id = task.payload.get("upload_id", "")
    recon_id = task.payload.get("recon_id", "")
    normalized_path = task.payload.get("normalized_path")
    backend_callback = task.payload.get("backend_callback")

    # 1. Verify normalized input exists
    if normalized_path:
        np_ = Path(normalized_path)
        if not np_.exists():
            # Try the standard location
            alt = _NORMALIZE_OUT_DIR / f"{upload_id}.jpg"
            if alt.exists():
                np_ = alt
            else:
                raise FileNotFoundError(
                    f"normalized crop not found: {normalized_path}"
                )
        src_size = np_.stat().st_size
    else:
        # No path provided — assume the standard one and require its existence
        np_ = _NORMALIZE_OUT_DIR / f"{upload_id}.jpg"
        if not np_.exists():
            raise FileNotFoundError(f"normalized crop missing for {upload_id}")
        src_size = np_.stat().st_size

    # 2. Output: copy GLB fixture to a stable path
    _RECON_OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _RECON_OUT_DIR / f"{recon_id or upload_id}.glb"
    if not _GLTF_FIXTURE.exists():
        raise FileNotFoundError(f"GLB fixture missing: {_GLTF_FIXTURE}")
    out_path.write_bytes(_GLTF_FIXTURE.read_bytes())

    # 3. Mock metrics
    metrics = {
        "format": "glb",
        "poly_count": 3,        # 1 triangle
        "size_bytes": out_path.stat().st_size,
        "src_normalized_bytes": src_size,
        "method": "smpl_fast",
        "mock": True,           # tells prod code this is a stub
    }

    result = {
        "upload_id": upload_id,
        "recon_id": recon_id,
        "glb_path": str(out_path),
        "metrics": metrics,
    }

    # 4. PATCH backend so reconstructions row flips to done
    if backend_callback:
        _patch_backend(
            backend_callback,
            {
                "status": "done",
                "glb_path": str(out_path),
                "metrics": metrics,
            },
        )
    return result


def run_smpl_multi(task: Task) -> dict[str, Any]:
    """Phase E stub: multi-view fusion. Reuses the single-view path with
    a marker until SMPLer-X multi-view lands."""
    return run_smpl_fast(task)  # stub for now


def run_task(task: Task) -> dict[str, Any]:
    """Dispatch by task_type. Phase A has no real GPU work yet — return mock.

    Phase D (FAST PATH) and Phase E (SLOW PATH) will add real implementations.
    Phase C adds real (but GPU-free) normalize handling.
    """
    if task.task_type == "normalize":
        return run_normalize(task)
    if task.task_type == "smpl_fast":
        return run_smpl_fast(task)
    if task.task_type == "smpl_multi":
        return run_smpl_multi(task)

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
