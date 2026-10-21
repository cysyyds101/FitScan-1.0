"""protocol.py — FitScan mirror frame wire format.

One WebSocket binary message == one frame:

    [ 40-byte fixed header ][ payload ]

The header is self-describing and requires no delimiter scanning. This replaces
the legacy capture.py framing (JSON text header, then b"\\n", then raw float32)
which the relay re-assembled into a single binary message while the browser
decoded that message as pure float32 -- silently shifting every depth sample by
(len(header)+1)/4 floats.

Payload meaning is selected by `kind`; the header is identical for all kinds.
`capture_ts_us` must be stamped by the sensor-reading thread as early as
possible -- it is the t0 for motion-to-photon latency.

Keep in sync with frontend/src/mirror/protocol.js. tests/test_protocol_vectors.py
asserts both ends against a shared hex vector.
"""
from __future__ import annotations

import struct
import time
from dataclasses import dataclass

MAGIC = b"FSMF"
VERSION = 1
HEADER_SIZE = struct.calcsize("<4s6H2q2I")

KIND_DEPTH_F32_MM = 1
KIND_RGB_JPEG = 2
KIND_META_JSON = 3
KIND_POSE_JSON = 4

FLAG_SIMULATED = 1 << 0
FLAG_FIRST_FRAME = 1 << 1

_FMT = struct.Struct("<4s6H2q2I")


def now_us() -> int:
    """Wall-clock microseconds, safe to compare across processes on one host."""
    return int(time.time() * 1_000_000)


@dataclass(frozen=True)
class Frame:
    kind: int
    width: int
    height: int
    fps_x100: int
    flags: int
    capture_ts_us: int
    emit_ts_us: int
    seq: int
    payload: bytes

    @property
    def fps(self) -> float:
        return self.fps_x100 / 100.0

    def age_ms(self, ref_us: int | None = None) -> float:
        """Milliseconds elapsed since the sensor produced this frame."""
        return ((ref_us if ref_us is not None else now_us()) - self.capture_ts_us) / 1000.0


def encode(
    kind: int,
    payload: bytes,
    *,
    width: int = 0,
    height: int = 0,
    fps: float = 0.0,
    flags: int = 0,
    capture_ts_us: int,
    seq: int,
    emit_ts_us: int | None = None,
) -> bytes:
    if len(payload) > 0xFFFFFFFF:
        raise ValueError(f"payload too large: {len(payload)} bytes")
    if width > 0xFFFF or height > 0xFFFF:
        raise ValueError(f"dimension overflows uint16: {width}x{height}")
    header = _FMT.pack(
        MAGIC,
        VERSION,
        kind,
        width,
        height,
        min(round(fps * 100), 0xFFFF),
        flags,
        capture_ts_us,
        emit_ts_us if emit_ts_us is not None else now_us(),
        seq & 0xFFFFFFFF,
        len(payload),
    )
    return header + payload


def decode(buf: bytes | bytearray | memoryview) -> Frame:
    view = memoryview(buf).cast("B")
    if len(view) < HEADER_SIZE:
        raise FrameError(f"truncated header: {len(view)} < {HEADER_SIZE} bytes")
    (
        magic,
        version,
        kind,
        width,
        height,
        fps_x100,
        flags,
        capture_ts_us,
        emit_ts_us,
        seq,
        payload_len,
    ) = _FMT.unpack_from(view)

    if magic != MAGIC:
        raise FrameError(f"bad magic {magic!r}, expected {MAGIC!r}")
    if version != VERSION:
        raise FrameError(f"unsupported version {version}, expected {VERSION}")
    if len(view) - HEADER_SIZE != payload_len:
        raise FrameError(f"payload length mismatch: header says {payload_len}, buffer has {len(view) - HEADER_SIZE}")

    return Frame(
        kind=kind,
        width=width,
        height=height,
        fps_x100=fps_x100,
        flags=flags,
        capture_ts_us=capture_ts_us,
        emit_ts_us=emit_ts_us,
        seq=seq,
        payload=bytes(view[HEADER_SIZE:]),
    )


class FrameError(ValueError):
    """Raised when a buffer is not a well-formed mirror frame."""
