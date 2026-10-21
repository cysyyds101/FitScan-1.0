"""AI Inference API routes.

Proxies requests to the remote AI server (4×3090).
The AI server is a stateless inference endpoint.

- POST /api/ai/measure       Request precise body measurement
- POST /api/ai/generate       Request 3D model generation
- GET  /api/ai/status/{tid}   Poll task status
- GET  /api/ai/health         Check AI server availability
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.services.ai_client import ai_client

router = APIRouter()


class AIMeasureRequest(BaseModel):
    depth_blob: str | None = None  # base64 encoded
    coarse_data: dict | None = None


class AIGenerateRequest(BaseModel):
    image_blob: str | None = None  # base64 encoded
    prompt: str = ""


# ─── Measurement ──────────────────────────────────────────────────────────────

@router.post("/measure")
async def request_measure(req: AIMeasureRequest):
    """
    Request precise measurement from AI server.

    If AI server is unavailable, returns mock result (deterministic fake data).
    The result is also stored in the measurement session via POST /api/measurements.
    """
    result = await ai_client.measure(coarse_data=req.coarse_data)
    return result


@router.post("/generate")
async def request_generate(req: AIGenerateRequest):
    """
    Request 3D model generation from AI server.

    Returns a task_id that can be polled via GET /api/ai/status/{task_id}.
    """
    result = await ai_client.generate_model(prompt=req.prompt)
    return result


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Poll AI server for task status."""
    result = await ai_client.get_status(task_id)
    return result


@router.get("/health")
def ai_health():
    """Check if AI server is reachable."""
    return {
        "ai_server_url": ai_client.base_url,
        "available": ai_client.available,
        "note": "Mock responses used when AI server unreachable" if not ai_client.available else "AI server online",
    }
