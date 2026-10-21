/**
 * protocol.js — browser half of the FitScan mirror frame format.
 *
 * One WebSocket binary message == one frame:
 *   [ 40-byte fixed little-endian header ][ payload ]
 *
 * Must stay byte-identical with backend/mirror/protocol.py. The shared vector
 * below is asserted by both tests/test_protocol_vectors.py and
 * frontend/src/mirror/protocol.test.js.
 */

export const MAGIC = 'FSMF';
export const VERSION = 1;
export const HEADER_SIZE = 40;

export const KIND_DEPTH_F32_MM = 1;
export const KIND_RGB_JPEG = 2;
export const KIND_META_JSON = 3;
export const KIND_POSE_JSON = 4;

export const FLAG_SIMULATED = 1 << 0;
export const FLAG_FIRST_FRAME = 1 << 1;

export class FrameError extends Error {}

function assertMagic(view) {
  const magic = String.fromCharCode(
    view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3),
  );
  if (magic !== MAGIC) {
    throw new FrameError(`bad magic ${JSON.stringify(magic)}, expected "FSMF"`);
  }
}

/**
 * Decode a mirror frame. Accepts ArrayBuffer | ArrayBufferView.
 * Returns { kind, width, height, fps, flags, captureTsUs, emitTsUs, seq,
 *           simulated, payload } — payload is a Uint8Array view, zero-copy.
 */
export function decodeFrame(buf) {
  const bytes = buf instanceof ArrayBuffer ? new Uint8Array(buf) : new Uint8Array(buf.buffer, buf.byteOffset, buf.byteLength);
  if (bytes.length < HEADER_SIZE) {
    throw new FrameError(`truncated header: ${bytes.length} < ${HEADER_SIZE} bytes`);
  }
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  assertMagic(view);

  const version = view.getUint16(4, true);
  if (version !== VERSION) {
    throw new FrameError(`unsupported version ${version}, expected ${VERSION}`);
  }

  const kind = view.getUint16(6, true);
  const width = view.getUint16(8, true);
  const height = view.getUint16(10, true);
  const fpsX100 = view.getUint16(12, true);
  const flags = view.getUint16(14, true);
  const captureTsUs = Number(view.getBigInt64(16, true));
  const emitTsUs = Number(view.getBigInt64(24, true));
  const seq = view.getUint32(32, true);
  const payloadLen = view.getUint32(36, true);

  if (bytes.length - HEADER_SIZE !== payloadLen) {
    throw new FrameError(`payload length mismatch: header says ${payloadLen}, buffer has ${bytes.length - HEADER_SIZE}`);
  }

  return {
    kind,
    width,
    height,
    fps: fpsX100 / 100,
    flags,
    captureTsUs,
    emitTsUs,
    seq,
    simulated: (flags & FLAG_SIMULATED) !== 0,
    firstFrame: (flags & FLAG_FIRST_FRAME) !== 0,
    payload: bytes.subarray(HEADER_SIZE),
  };
}

/** Depth payload as Float32Array. Throws if the payload is not 4-byte aligned. */
export function depthPayloadToFloat32(frame) {
  if (frame.payload.byteLength % 4 !== 0) {
    throw new FrameError(`depth payload not 4-byte aligned: ${frame.payload.byteLength} bytes`);
  }
  return new Float32Array(frame.payload.buffer, frame.payload.byteOffset, frame.payload.byteLength / 4);
}

/**
 * Milliseconds elapsed since the sensor produced this frame.
 * `nowWallUs` must come from the same host clock as the capture process.
 */
export function frameAgeMs(frame, nowWallUs) {
  return (nowWallUs - frame.captureTsUs) / 1000;
}
