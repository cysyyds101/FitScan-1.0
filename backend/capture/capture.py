"""
capture.py — RealSense SR300 采集服务（集成人体测量）。

功能：
1. 获取 RGB + Depth 数据（RGB 按需启用）
2. 实时计算人体测量（身高、肩宽、臂长）
3. 通过 WebSocket 发送到前端

Usage:
    python capture.py [--simulate]

Environment:
    REAL_SENSE_SIMULATE=1    # 强制模拟数据
    CAPTURE_PORT=8765        # WebSocket 端口（默认 8765）

WebSocket 协议（与之前兼容）：
    发送（服务端 → 客户端）：
        Text:  JSON header (UTF-8)
        Binary:  \\n + depth binary (每帧)

    header 格式：
        {
          "type": "depth_frame",
          "timestamp": 1234567890.123,
          "width": 640,
          "height": 480,
          "fps": 30,
          "simulated": false,
          "body_measurements": {
            "height_cm": 170.2,
            "shoulder_width_cm": 46.5,
            "arm_length_cm": 62.0,
            "confidence": 0.82,
            "avg_depth_cm": 152.3
          }
        }

    控制消息（客户端 → 服务端）：
        {"type": "ping"}                  → {"type": "pong", "t": timestamp}
        {"type": "enable_rgb"}            → {"type": "rgb_enabled"}
        {"type": "disable_rgb"}           → {"type": "rgb_disabled"}
        {"type": "request_measure"}       → {"type": "measurement_snapshot", "measurements": {...}}
"""
import asyncio
import json
import math
import os
import struct
import sys
import time
from pathlib import Path
from typing import Optional
import numpy as np

# 确保 capture/ 在 path 中
sys.path.insert(0, str(Path(__file__).parent))
from body_measure import REALSENSE_INTRINSICS, measure_depth_frame, BodyMeasurements

try:
    import pyrealsense2 as rs
    _HAS_REALSENSE = True
except ImportError:
    _HAS_REALSENSE = False
    print("[capture] pyrealsense2 not found — running in SIMULATED mode")

try:
    import websockets
except ImportError:
    print("[capture] websockets not installed. Run: pip install websockets")
    sys.exit(1)


# ─── Configuration ──────────────────────────────────────────────────────────────

WIDTH = 640
HEIGHT = 480
FPS = 30
PORT = int(os.getenv("CAPTURE_PORT", "8765"))
SIMULATE = os.getenv("REAL_SENSE_SIMULATE", "0") == "1" or not _HAS_REALSENSE

print(f"[capture] Starting — simulate={SIMULATE}, port={PORT}, res={WIDTH}×{HEIGHT}")


# ─── 模拟摄像头（开发 / 无 RealSense 时使用）─────────────────────────────────────

class SimulatedCamera:
    """
    生成带程序化人体的模拟深度图 + RGB。
    包含动态呼吸效果和轻微摇摆。
    """

    def __init__(self):
        self._frame = 0
        self._rgb_enabled = False

    def generate_frame(self) -> tuple[bytes, BodyMeasurements]:
        """返回 (depth_bytes, BodyMeasurements)。"""
        self._frame += 1
        t = self._frame * 0.05

        buf = bytearray(WIDTH * HEIGHT * 4)
        person_depth_mm = 1500.0  # 距摄像头 1.5m

        for y in range(HEIGHT):
            for x in range(WIDTH):
                nx = (x / WIDTH - 0.5) * 2
                ny = (y / HEIGHT - 0.5) * 2

                depth = 2000.0  # 背景默认 2m

                # 躯干（椭圆）
                torso_dx = nx / 0.28
                torso_dy = (ny + 0.1) / 0.38
                if torso_dx * torso_dx + torso_dy * torso_dy < 1.0:
                    depth = person_depth_mm - (1.0 - (torso_dx*torso_dx + torso_dy*torso_dy)) * 80.0

                # 头部（椭圆）
                head_dx = nx / 0.14
                head_dy = (ny + 0.55) / 0.16
                if head_dx * head_dx + head_dy * head_dy < 1.0:
                    depth = person_depth_mm - (1.0 - (head_dx*head_dx + head_dy*head_dy)) * 60.0

                # 手臂（两侧小椭圆）
                for sign in [-1, 1]:
                    arm_dx = (nx - sign * 0.35) / 0.08
                    arm_dy = (ny + 0.3) / 0.22
                    if arm_dx * arm_dx + arm_dy * arm_dy < 1.0:
                        depth = person_depth_mm - 20.0

                # 腿部（两个竖向椭圆）
                for leg_x in [-0.12, 0.12]:
                    leg_dx = (nx - leg_x) / 0.07
                    leg_dy = (ny - 0.65) / 0.30
                    if leg_dx * leg_dx + leg_dy * leg_dy < 1.0:
                        depth = person_depth_mm - 10.0

                # 呼吸 + 摇摆
                depth += math.sin(t + ny * 2.0) * 15.0
                depth += math.cos(t * 0.7 + nx * 1.5) * 8.0

                # 背景噪声
                noise = math.sin(x * 0.3 + t) * math.cos(y * 0.2 + t * 0.7) * 12.0
                depth += noise
                depth = max(500.0, min(3000.0, depth))

                offset = (y * WIDTH + x) * 4
                struct.pack_into('<f', buf, offset, depth)

        # 模拟测量（从已知参数）
        measurements = BodyMeasurements(
            height_cm=170.0 + math.sin(t) * 0.5,
            shoulder_width_cm=46.0 + math.sin(t * 1.3) * 0.3,
            arm_length_cm=62.0 + math.cos(t * 0.9) * 0.4,
            confidence=0.85 + math.sin(t * 0.5) * 0.05,
            avg_depth_cm=person_depth_mm / 10.0,
        )

        return bytes(buf), measurements

    def generate_rgb(self) -> bytes:
        """生成 640×480×3 RGB（伪彩色深度图）。"""
        depth_bytes, _ = self.generate_frame()
        depth = list(struct.unpack(f'<{WIDTH * HEIGHT}f', depth_bytes))
        rgb_buf = bytearray(WIDTH * HEIGHT * 3)

        for i, d in enumerate(depth):
            t_val = max(0, min(1, (d - 500) / 2000))
            idx = int(t_val * 255)
            r = max(0, min(255, 2 * idx - 256))
            g = max(0, min(255, 2 * idx))
            b = max(0, min(255, 2 * (256 - idx)))
            rgb_buf[i * 3]     = r
            rgb_buf[i * 3 + 1] = g
            rgb_buf[i * 3 + 2] = b

        return bytes(rgb_buf)


# ─── RealSense 摄像头 ─────────────────────────────────────────────────────────

class RealSenseCamera:
    """RealSense SR300 / D400 摄像头封装。"""

    def __init__(self):
        self._pipeline = rs.pipeline()
        self._config   = rs.config()
        self._config.enable_stream(rs.stream.depth, WIDTH, HEIGHT, rs.format.z16, FPS)
        self._profile  = self._pipeline.start(self._config)
        self._rgb_enabled = False

    def read_frame(self) -> Optional[tuple]:
        """
        返回 (depth_bytes, BodyMeasurements) 或 None（无帧）。
        RGB 禁用时 color_bytes 为空 bytes。
        """
        try:
            frames = self._pipeline.wait_for_frames(timeout_ms=3000)
            depth_frame = frames.get_depth_frame()
            color_frame = frames.get_color_frame() if self._rgb_enabled else None

            if not depth_frame:
                return None

            # Depth → float32 numpy array
            depth_np = np.asanyarray(depth_frame.get_data()).astype(np.float32).flatten()
            depth_buf = depth_np.tobytes()  # bytes for WebSocket transmission

            # Measurement — pass numpy array directly (avoids list conversion)
            measurements = measure_depth_frame(depth_np, WIDTH, HEIGHT)

            return bytes(depth_buf), measurements

        except Exception as e:
            print(f"[capture] RealSense read error: {e}")
            return None

    def stop(self):
        self._pipeline.stop()


# ─── WebSocket 服务器 ─────────────────────────────────────────────────────────

class CaptureServer:
    def __init__(self):
        self._clients: set = set()
        self._camera = None  # RealSenseCamera | SimulatedCamera
        self._running = False
        self._rgb_enabled = False
        self._rgb_client_ids: set = set()  # 请求 RGB 的客户端

    async def _broadcast_loop(self):
        """读取摄像头帧 → 计算测量 → 广播给所有客户端。"""
        global SIMULATE
        while self._running:
            if SIMULATE:
                frame, measurements = self._simulated.generate_frame()
                rgb_frame = self._simulated.generate_rgb() if self._rgb_enabled else b''
            else:
                if self._camera is None:
                    try:
                        self._camera = RealSenseCamera()
                        print("[capture] RealSense initialized")
                    except Exception as e:
                        print(f"[capture] Failed to init RealSense: {e}, falling back to simulation")
                        SIMULATE = True
                        self._simulated = SimulatedCamera()
                        continue

                result = self._camera.read_frame()
                if result is None:
                    await asyncio.sleep(0.001)
                    continue
                frame, measurements = result
                rgb_frame = b''  # RealSense RGB 需要额外处理

            if not self._clients:
                await asyncio.sleep(1.0 / FPS)
                continue

            # 构建 header（每帧带测量）
            header = {
                "type": "depth_frame",
                "timestamp": time.time(),
                "width": WIDTH,
                "height": HEIGHT,
                "fps": FPS,
                "simulated": SIMULATE,
                "rgb_enabled": self._rgb_enabled,
                "body_measurements": measurements.to_dict(),
            }

            header_bytes = json.dumps(header, ensure_ascii=False).encode()

            dead = set()
            for ws in list(self._clients):   # snapshot to avoid RuntimeError
                try:
                    # 始终发 depth header
                    await ws.send(header_bytes)
                    await ws.send(b'\n')
                    await ws.send(frame)

                    # 仅对请求 RGB 的客户端发 RGB
                    if self._rgb_enabled and id(ws) in self._rgb_client_ids:
                        rgb_header = json.dumps({
                            "type": "rgb_frame",
                            "timestamp": header["timestamp"],
                            "width": WIDTH,
                            "height": HEIGHT,
                        }).encode()
                        await ws.send(rgb_header)
                        await ws.send(b'\n')
                        await ws.send(rgb_frame)

                except Exception:
                    dead.add(ws)

            self._clients -= dead
            await asyncio.sleep(1.0 / FPS)

    async def _handler(self, ws):
        """处理单个客户端连接。"""
        client_id = id(ws)
        print(f"[capture] Client connected: {ws.remote_address}")
        self._clients.add(ws)

        try:
            async for raw in ws:
                if isinstance(raw, str):
                    try:
                        msg = json.loads(raw)
                        t = msg.get("type", "")

                        if t == "ping":
                            await ws.send(json.dumps({"type": "pong", "t": time.time()}))

                        elif t == "enable_rgb":
                            self._rgb_enabled = True
                            self._rgb_client_ids.add(client_id)
                            await ws.send(json.dumps({
                                "type": "rgb_enabled",
                                "note": "RGB streaming enabled",
                            }))

                        elif t == "disable_rgb":
                            self._rgb_client_ids.discard(client_id)
                            # 只有所有客户端都禁用时才关闭摄像头 RGB 流
                            if client_id not in self._rgb_client_ids:
                                self._rgb_enabled = False
                            await ws.send(json.dumps({"type": "rgb_disabled"}))

                        elif t == "request_measure":
                            # 手动请求一次精确测量快照
                            if SIMULATE:
                                _, measurements = self._simulated.generate_frame()
                            elif self._camera and isinstance(self._camera, RealSenseCamera):
                                result = self._camera.read_frame()
                                measurements = result[1] if result else None
                            else:
                                measurements = None

                            if measurements:
                                await ws.send(json.dumps({
                                    "type": "measurement_snapshot",
                                    "timestamp": time.time(),
                                    "measurements": measurements.to_dict(),
                                }))

                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            print(f"[capture] Client error: {e}")
        finally:
            self._clients.discard(ws)
            self._rgb_client_ids.discard(client_id)
            print(f"[capture] Client disconnected: {ws.remote_address}")

    async def start(self):
        self._running = True
        if SIMULATE:
            self._simulated = SimulatedCamera()
            print("[capture] Using SIMULATED data (no RealSense)")
            print("[capture] Simulated body: height=170cm, shoulder=46cm, arm=62cm")

        async with websockets.serve(
            self._handler, "localhost", PORT,
            max_size=4 * 1024 * 1024,   # 4 MB — fits 640×480 float32 depth frame
        ):
            print(f"[capture] WebSocket server listening on ws://localhost:{PORT}")
            await self._broadcast_loop()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--simulate":
        os.environ["REAL_SENSE_SIMULATE"] = "1"

    server = CaptureServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("[capture] Shutting down")
