"""AI Server API Gateway (Phase A skeleton).

This is the ONLY process that exposes HTTP. Workers do not.

Responsibilities:
    - Accept inference jobs (POST /infer/smpl_fast, POST /infer/smpl_multi, POST /infer/normalize).
    - Persist the job to SQLite + put it on the in-process queue.
    - Return job_id immediately (202-style 'processing').
    - Serve status/result queries (GET /status/{id}, GET /result/{id}).
    - Serve /health for the dev machine client and operator dashboards.
    - Run the HeartbeatWatchdog in a background thread (T007).

What this process does NOT do:
    - It does NOT load any ML model.
    - It does NOT touch the GPU.
    - It does NOT call the workers directly — workers pull from the queue.

Phase A has the queue pipeline working end-to-end with mock run_task.
Phase C adds normalize (PIL only, no GPU).
Phase D adds real SMPLer-X inference.

Routes added in this file:
    GET  /health
    POST /infer/smpl_fast
    POST /infer/smpl_multi
    POST /infer/normalize
    GET  /status/{task_id}
    GET  /result/{task_id}
"""
from __future__ import annotations

import logging
import os
import sys
from typing import Any

# Bootstrap path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_HERE)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ai_server.queue.inproc_queue import enqueue, queue_size
from ai_server.queue.persistence import get, list_by_status
from ai_server.queue.task import Task, TaskStatus, new_task_id
from ai_server.queue.watchdog import HeartbeatWatchdog

logger = logging.getLogger(__name__)


# ─── Schemas ────────────────────────────────────────────────────────────────

class SmplFastRequest(BaseModel):
    """Single-image SMPL reconstruction job."""
    upload_id: str = Field(..., description="Upload id from /api/uploads (dev machine)")
    image_url: str | None = Field(None, description="Optional URL/path to image (else resolved from upload_id)")


class SmplMultiRequest(BaseModel):
    """Multi-image SMPLer-X fusion job."""
    upload_id: str
    image_urls: list[str] = Field(default_factory=list, description="Multiple views of the subject")


class NormalizeRequest(BaseModel):
    """Image normalization job (Phase C).

    Reads the uploaded image and produces a fixed-format 512x512 centered
    human crop. PIL only — no GPU, no torch. The output is what Phase D's
    SMPLer-X pipeline expects.
    """
    upload_id: str = Field(..., description="Upload id from /api/uploads (dev machine)")
    image_url: str | None = Field(None, description="URL/path to source image (else resolved from upload_id)")
    backend_callback: str | None = Field(
        None,
        description="Optional URL the AI server PATCHes with the normalized result. "
                    "If unset, dev machine polls GET /status/{task_id} instead.",
    )


class EnqueueResponse(BaseModel):
    task_id: str
    status: str
    task_type: str


class StatusResponse(BaseModel):
    task_id: str
    status: str
    task_type: str
    gpu_id: int | None = None
    started_at: str | None = None
    finished_at: str | None = None
    error_msg: str | None = None


class ResultResponse(BaseModel):
    task_id: str
    status: str
    result: dict[str, Any] | None = None


# ─── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="FitScan AI Server (Gateway)",
    version="0.2.0",
    description="API Gateway only — workers pull from in-process queue. No GPU work here.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _on_startup() -> None:
    """Initialize schema and start the watchdog thread."""
    from ai_server.queue.persistence import init_schema
    init_schema()
    logger.info("[api] schema initialized")

    wd = HeartbeatWatchdog(
        timeout_sec=int(os.getenv("WATCHDOG_TIMEOUT_SEC", "600")),
        scan_interval_sec=int(os.getenv("WATCHDOG_SCAN_SEC", "30")),
    )
    wd.start()
    app.state.watchdog = wd
    logger.info("[api] watchdog started")


@app.on_event("shutdown")
def _on_shutdown() -> None:
    wd = getattr(app.state, "watchdog", None)
    if wd is not None:
        wd.stop()


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + a small snapshot of queue/worker state."""
    return {
        "status": "ok",
        "queue_depth": queue_size(),
        "pending": len(list_by_status(TaskStatus.PENDING, limit=1000)),
        "running": len(list_by_status(TaskStatus.RUNNING, limit=1000)),
        "done_recent": len(list_by_status(TaskStatus.DONE, limit=100)),
        "failed_recent": len(list_by_status(TaskStatus.FAILED, limit=100)),
    }


@app.post("/infer/smpl_fast", response_model=EnqueueResponse, status_code=202)
def enqueue_smpl_fast(req: SmplFastRequest) -> EnqueueResponse:
    """Enqueue a single-image SMPL reconstruction job.

    Returns immediately with task_id. Worker on GPU 0 (role='fast') will
    pick it up and run inference asynchronously.
    """
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_fast",
        payload={
            "upload_id": req.upload_id,
            "image_url": req.image_url,
        },
    )
    enqueue(task)
    return EnqueueResponse(task_id=task.id, status="PENDING", task_type=task.task_type)


@app.post("/infer/smpl_multi", response_model=EnqueueResponse, status_code=202)
def enqueue_smpl_multi(req: SmplMultiRequest) -> EnqueueResponse:
    """Enqueue a multi-image SMPLer-X fusion job (slower, multi-view)."""
    if not req.image_urls:
        raise HTTPException(status_code=400, detail="image_urls must not be empty")
    task = Task(
        id=new_task_id("rec"),
        task_type="smpl_multi",
        payload={
            "upload_id": req.upload_id,
            "image_urls": req.image_urls,
        },
    )
    enqueue(task)
    return EnqueueResponse(task_id=task.id, status="PENDING", task_type=task.task_type)


@app.post("/infer/normalize", response_model=EnqueueResponse, status_code=202)
def enqueue_normalize(req: NormalizeRequest) -> EnqueueResponse:
    """Enqueue an image normalization job (Phase C).

    The worker (PIL only, no GPU) will:
        1. Load the source image from image_url (or dev-machine uploads dir).
        2. Otsu-threshold to find the subject bounding box.
        3. Center-crop a square (1.1x padding) and resize to 512x512 JPEG.
        4. Save to ai_server/data/normalized/<upload_id>.jpg.
        5. If backend_callback is set, PATCH that URL with the result.

    Returns immediately with task_id. The dev machine's normalize_service
    updates the uploads row when the worker reports completion.
    """
    task = Task(
        id=new_task_id("norm"),
        task_type="normalize",
        payload={
            "upload_id": req.upload_id,
            "image_url": req.image_url,
            "backend_callback": req.backend_callback,
        },
    )
    enqueue(task)
    return EnqueueResponse(task_id=task.id, status="PENDING", task_type=task.task_type)


@app.get("/status/{task_id}", response_model=StatusResponse)
def get_status(task_id: str) -> StatusResponse:
    """Poll task status. Cheap read from SQLite."""
    t = get(task_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return StatusResponse(
        task_id=t.id,
        status=t.status.value,
        task_type=t.task_type,
        gpu_id=t.gpu_id,
        started_at=t.started_at,
        finished_at=t.finished_at,
        error_msg=t.error_msg,
    )


@app.get("/result/{task_id}", response_model=ResultResponse)
def get_result(task_id: str) -> ResultResponse:
    """Fetch the task's result. Only meaningful when status == DONE."""
    t = get(task_id)
    if t is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    if t.status is not TaskStatus.DONE:
        return ResultResponse(task_id=t.id, status=t.status.value, result=None)
    return ResultResponse(task_id=t.id, status=t.status.value, result=t.result)


# ─── main (for `python -m ai_server.api`) ────────────────────────────────────

def main() -> None:
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
