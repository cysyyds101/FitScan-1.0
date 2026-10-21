"""
FitScan AI Server — GPU Inference Endpoint (4×3090).

Stateless inference-only FastAPI.
No business logic, no database, no business-layer imports from backend/.

Routes:
    GET  /health
    POST /infer/measure     Precise body measurement
    POST /infer/generate    3D model generation
    GET  /status/{task_id}

All models are loaded once at startup.
AI server URL configured via env: PORT=8080
"""
import os
import uuid
import asyncio
import random
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FitScan AI Server", version="1.0.0", description="GPU inference only — 4×RTX 3090")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory task store (replace with Redis in production) ───────────────────
_tasks: dict[str, dict] = {}


# ─── Schemas ─────────────────────────────────────────────────────────────────

class MeasureRequest(BaseModel):
    task_id: str
    timestamp: str
    coarse_measurement: dict | None = None


class GenerateRequest(BaseModel):
    task_id: str
    timestamp: str
    prompt: str = ""


class TaskResponse(BaseModel):
    task_id: str
    status: str  # pending | processing | done | error
    result: dict | None = None
    error: str | None = None


# ─── Mock inference (MVP — replace with real models) ────────────────────────

async def _run_measure(coarse: dict | None) -> dict:
    """
    Mock precise measurement.
    In production: load PyTorch model → run inference → return mm-precision results.
    """
    await asyncio.sleep(random.uniform(0.5, 1.5))  # simulate GPU compute time
    base = coarse or {}
    return {
        "height":          round(base.get("height", 170) + random.uniform(-1, 1), 1),
        "shoulder_width":  round(base.get("shoulder_width", 46) + random.uniform(-0.5, 0.5), 1),
        "chest":           round(base.get("chest", 92) + random.uniform(-0.8, 0.8), 1),
        "waist":           round(base.get("waist", 78) + random.uniform(-0.6, 0.6), 1),
        "hip":             round(base.get("hip", 96) + random.uniform(-0.7, 0.7), 1),
        "inseam":          round(base.get("inseam", 80) + random.uniform(-0.5, 0.5), 1),
        "arm_length":       round(base.get("arm_length", 62) + random.uniform(-0.4, 0.4), 1),
        "unit": "cm",
        "precision": "sub-cm",
        "gpu": "3090",
        "model_version": "v0.1-mock",
    }


async def _run_generate(prompt: str) -> dict:
    """
    Mock 3D model generation.
    In production: load Tripo3D/MNISTR3D → run inference → save GLB → return URL.
    """
    await asyncio.sleep(random.uniform(2, 5))  # simulate GPU compute time (longer for generation)
    return {
        "model_url": "/static/models/clothing_01.glb",  # placeholder
        "format": "glb",
        "polys": random.randint(5000, 20000),
        "prompt": prompt,
        "gpu": "3090",
        "model_version": "v0.1-mock",
    }


async def _process_task(task_id: str, fn, *args):
    """Background task runner with state updates."""
    _tasks[task_id] = {"status": "processing", "result": None, "error": None}
    try:
        result = await fn(*args)
        _tasks[task_id] = {"status": "done", "result": result, "error": None}
        logger.info(f"[ai_server] Task {task_id} done")
    except Exception as e:
        _tasks[task_id] = {"status": "error", "result": None, "error": str(e)}
        logger.error(f"[ai_server] Task {task_id} error: {e}")


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "gpu": "4×RTX 3090", "mode": "mock"}


@app.post("/infer/measure", response_model=TaskResponse)
async def infer_measure(req: MeasureRequest):
    """Request precise body measurement. Returns immediately, runs in background."""
    task_id = req.task_id or str(uuid.uuid4())
    _tasks[task_id] = {"status": "pending", "result": None, "error": None}
    asyncio.create_task(_process_task(task_id, _run_measure, req.coarse_measurement))
    return TaskResponse(task_id=task_id, status="processing")


@app.post("/infer/generate", response_model=TaskResponse)
async def infer_generate(req: GenerateRequest):
    """Request 3D model generation. Returns immediately, runs in background."""
    task_id = req.task_id or str(uuid.uuid4())
    _tasks[task_id] = {"status": "pending", "result": None, "error": None}
    asyncio.create_task(_process_task(task_id, _run_generate, req.prompt))
    return TaskResponse(task_id=task_id, status="processing")


@app.get("/status/{task_id}", response_model=TaskResponse)
def get_status(task_id: str):
    task = _tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return TaskResponse(task_id=task_id, **task)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
