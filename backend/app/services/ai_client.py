"""AI Server HTTP client.

All AI inference calls go through here.
The dev machine has no GPU — calls are proxied to the remote AI server (4×3090).

The AI server is a stateless inference endpoint.
It exposes REST APIs only, no WebSocket, no business logic.

Env:
    AI_SERVER_URL  — base URL of AI server, default http://localhost:8080
    AI_CLIENT_TIMEOUT — HTTP timeout in seconds, default 60
"""
import os
import uuid
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None

import logging

logger = logging.getLogger(__name__)

AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://localhost:8080")
TIMEOUT = float(os.getenv("AI_CLIENT_TIMEOUT", "60"))


class AIClient:
    """Thin HTTP client for AI server inference endpoints."""

    def __init__(self, base_url: str = AI_SERVER_URL, timeout: float = TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._available = None  # cached availability check

    @property
    def available(self) -> bool:
        """Check if AI server is reachable (cached)."""
        if self._available is None:
            self._available = self._ping()
        return self._available

    def _ping(self) -> bool:
        if httpx is None:
            logger.warning("[ai_client] httpx not installed")
            return False
        try:
            resp = httpx.get(f"{self.base_url}/health", timeout=3.0)
            return resp.status_code == 200
        except Exception:
            return False

    # ─── Body measurement ───────────────────────────────────────────────────

    async def measure(self, depth_blob: bytes | None = None, coarse_data: dict | None = None) -> dict:
        """
        Request precise body measurement from AI server.

        Args:
            depth_blob: Raw depth frame bytes (optional).
            coarse_data: Frontend coarse measurement result (optional).

        Returns:
            AI server response: {"task_id": "...", "status": "processing"}

        The AI server will POST back results asynchronously via callback
        or the client polls GET /ai/status/{task_id}.
        """
        if httpx is None:
            return self._mock_measure(coarse_data)

        payload = {
            "task_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if coarse_data:
            payload["coarse_measurement"] = coarse_data

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/infer/measure",
                    json=payload,
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[ai_client] measure failed: {e}, using mock")
            return self._mock_measure(coarse_data)

    # ─── 3D model generation ────────────────────────────────────────────────

    async def generate_model(self, image_data: bytes | None = None, prompt: str = "") -> dict:
        """
        Request 3D model generation from AI server.

        Args:
            image_data: Optional photo bytes.
            prompt: Optional text prompt (for generative models).

        Returns:
            {"task_id": "...", "status": "processing"}
        """
        if httpx is None:
            return self._mock_generate(prompt)

        payload = {
            "task_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if prompt:
            payload["prompt"] = prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout * 10) as client:
                files = {}
                if image_data:
                    files["image"] = ("photo.jpg", image_data, "image/jpeg")
                resp = await client.post(
                    f"{self.base_url}/infer/generate",
                    data=payload,
                    files=files if files else None,
                    timeout=self.timeout * 10,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[ai_client] generate failed: {e}, using mock")
            return self._mock_generate(prompt)

    # ─── Task status ────────────────────────────────────────────────────────

    async def get_status(self, task_id: str) -> dict:
        """Poll AI server for task status."""
        if httpx is None:
            return self._mock_status(task_id)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/status/{task_id}")
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[ai_client] get_status failed: {e}, using mock")
            return self._mock_status(task_id)

    # ─── Normalize (Phase C) ────────────────────────────────────────────────

    async def normalize(
        self,
        upload_id: str,
        image_url: str | None = None,
        backend_callback: str | None = None,
    ) -> dict:
        """Enqueue an image normalization job on the AI server.

        Args:
            upload_id: dev-machine upload id (resolves source on AI server side).
            image_url: optional explicit URL/path to the source image.
            backend_callback: optional URL the AI server PATCHes when done.
                              If unset, dev machine must poll via get_status().

        Returns:
            {"task_id": "norm-xxx", "status": "PENDING", "task_type": "normalize"}

        No mock fallback here: Phase C is async and we cannot fabricate
        a 512x512 PIL crop in the client. If the AI server is down, this
        returns a 502-like dict so the route layer can decide.
        """
        if httpx is None:
            return {"task_id": None, "status": "ERROR", "error": "httpx not installed"}

        payload = {
            "upload_id": upload_id,
            "image_url": image_url,
            "backend_callback": backend_callback,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/infer/normalize",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[ai_client] normalize enqueue failed: {e}")
            return {"task_id": None, "status": "ERROR", "error": str(e)}

    # ─── SMPL reconstruction (Phase D) ──────────────────────────────────────

    async def smpl_fast(
        self,
        upload_id: str,
        image_url: str | None = None,
        backend_callback: str | None = None,
        recon_id: str | None = None,
    ) -> dict:
        """Enqueue a single-image SMPL reconstruction job (Phase D)."""
        if httpx is None:
            return {"task_id": None, "status": "ERROR", "error": "httpx not installed"}

        payload = {
            "upload_id": upload_id,
            "image_url": image_url,
            "backend_callback": backend_callback,
            "recon_id": recon_id,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/infer/smpl_fast",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[ai_client] smpl_fast enqueue failed: {e}")
            return {"task_id": None, "status": "ERROR", "error": str(e)}

    async def smpl_multi(
        self,
        upload_id: str,
        image_url: str | None = None,
        image_urls: list[str] | None = None,
        backend_callback: str | None = None,
        recon_id: str | None = None,
    ) -> dict:
        """Enqueue a multi-view SMPLer-X fusion job (Phase E).

        Accepts EITHER:
            - image_url (single)        -> POSTed as image_url
            - image_urls (list, >=1)    -> POSTed as image_urls
        The AI server prefers image_urls; if only image_url is given we
        wrap it in a single-element list to keep the wire format uniform.
        """
        if httpx is None:
            return {"task_id": None, "status": "ERROR", "error": "httpx not installed"}

        # Normalize: if both empty, error. If only image_url, wrap.
        urls = list(image_urls) if image_urls else []
        if not urls and image_url:
            urls = [image_url]
        if not urls:
            return {"task_id": None, "status": "ERROR", "error": "no images provided"}

        payload = {
            "upload_id": upload_id,
            "image_url": urls[0] if len(urls) == 1 else None,
            "image_urls": urls,
            "backend_callback": backend_callback,
            "recon_id": recon_id,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/infer/smpl_multi",
                    json=payload,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"[ai_client] smpl_multi enqueue failed: {e}")
            return {"task_id": None, "status": "ERROR", "error": str(e)}

    # ─── Mock responses (no AI server needed for dev/demo) ─────────────────

    @staticmethod
    def _mock_measure(coarse_data: dict | None) -> dict:
        """Return deterministic mock measurement for development."""
        base = coarse_data or {}
        return {
            "task_id": f"mock-{uuid.uuid4().hex[:8]}",
            "status": "done",
            "measurement": {
                "height": base.get("height", 170.0),
                "shoulder_width": base.get("shoulder_width", 46.0),
                "chest": base.get("chest", 92.0),
                "waist": base.get("waist", 78.0),
                "hip": base.get("hip", 96.0),
                "inseam": base.get("inseam", 80.0),
                "arm_length": 62.0,
                "unit": "cm",
            },
        }

    @staticmethod
    def _mock_generate(prompt: str) -> dict:
        """Return deterministic mock generation result."""
        return {
            "task_id": f"mock-gen-{uuid.uuid4().hex[:8]}",
            "status": "done",
            "model_url": "/static/models/clothing_01.glb",
            "prompt": prompt,
        }

    @staticmethod
    def _mock_status(task_id: str) -> dict:
        """Return mock task status."""
        return {"task_id": task_id, "status": "done"}


# Singleton for use across routes
ai_client = AIClient()
