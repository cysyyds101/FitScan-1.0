"""WebSocket relay: browser ↔ capture.py.

FastAPI WebSocket endpoint that relays binary depth frames
from the local capture.py process to the browser.

Why relay instead of browser → capture.py directly?
- Avoids CORS / firewall issues on some networks
- Allows FastAPI to inject auth / metering later
- Single URL for all WebSocket traffic (camera + future signals)
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Ensure backend is on path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import websockets
except ImportError:
    websockets = None

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

CAPTURE_WS = os.getenv("CAPTURE_WS_URL", "ws://localhost:8765")


# ─── WebSocket client pool (FastAPI shares state across requests) ──────────────
_active_relay_tasks: set = set()


# ─── Relay endpoint: browser → FastAPI → capture.py → browser ────────────────
@router.websocket("/camera")
async def camera_ws(ws: WebSocket):
    """Relay depth frames from capture.py to the browser.

    Protocol (binary frames):
        Client sends:  nothing (passive receive)
        Server sends:  JSON header + binary depth frame
                      {
                        "type": "depth_frame",
                        "timestamp": 1234567890.123,
                        "width": 640,
                        "height": 480,
                        "fps": 30,
                        "simulated": false
                      }
                      \n
                      <640×480×4 bytes float32 depth in mm>

    Control messages (JSON):
        {"type": "ping"}  →  {"type": "pong", "t": timestamp}
    """
    await ws.accept()
    logger.info(f"[ws/camera] Browser connected from {ws.client}")

    capture_url = CAPTURE_WS
    capture_task = None
    relay_connected = False

    async def pipe_browser_to_capture():
        """Forward browser control messages (ping) upstream to capture.py."""
        nonlocal relay_connected
        try:
            async with websockets.connect(capture_url, ping_interval=None, max_size=4 * 1024 * 1024) as capture_ws:
                relay_connected = True
                logger.info(f"[ws/camera] Connected to capture.py at {capture_url}")
                async for raw in ws.iter_text():
                    try:
                        msg = json.loads(raw)
                        await capture_ws.send(json.dumps(msg))
                    except (json.JSONDecodeError, Exception):
                        pass
        except Exception as e:
            logger.warning(f"[ws/camera] capture.py pipe error: {e}")
            relay_connected = False

    async def pipe_capture_to_browser():
        """Receive depth frames from capture.py, reassemble into single
        binary message that useCameraStream.js expects:
          [header_json_bytes] + [b'\n'] + [depth_float32_bytes]
        all in ONE WebSocket binary message.
        """
        nonlocal relay_connected
        try:
            async with websockets.connect(
                capture_url, ping_interval=None, max_size=4 * 1024 * 1024
            ) as capture_ws:
                relay_connected = True
                logger.info("[ws/camera] Streaming from capture.py")

                header_bytes = None   # last received JSON header as bytes
                got_newline  = False  # have we seen the b'\n' separator?

                async for msg in capture_ws:
                    if isinstance(msg, str):
                        # JSON header — store as bytes, also forward as text
                        # so the frontend metadata handler fires
                        await ws.send_text(msg)
                        header_bytes = msg.encode()
                        got_newline  = False

                    elif isinstance(msg, bytes):
                        if msg == b'\n':
                            got_newline = True

                        elif got_newline and header_bytes is not None:
                            # depth frame — reassemble and send as ONE binary msg
                            combined = header_bytes + b'\n' + msg
                            await ws.send_bytes(combined)
                            header_bytes = None
                            got_newline  = False
                        else:
                            # unexpected binary — forward as-is
                            await ws.send_bytes(msg)

        except Exception as e:
            logger.warning(f"[ws/camera] Stream pipe error: {e}")
            relay_connected = False

    # Start both pipes concurrently
    try:
        await asyncio.gather(
            pipe_browser_to_capture(),
            pipe_capture_to_browser(),
        )
    except WebSocketDisconnect:
        pass
    finally:
        logger.info(f"[ws/camera] Browser disconnected")
