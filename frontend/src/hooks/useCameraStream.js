/**
 * useCameraStream.js — 摄像头深度流 WebSocket hook.
 *
 * 连接 FastAPI /ws/camera relay → capture.py → RealSense。
 * 将二进制深度帧存入 ref buffer（避免 React re-render 过度），
 * 通过 onFrame 回调通知消费者（DepthCanvas / useMeasurement）。
 *
 * Protocol:
 *   Server → Client (text): JSON header
 *     {"type":"depth_frame","timestamp":...,"width":640,"height":480,"simulated":bool}
 *   Server → Client (binary): \n + 640×480×4 bytes float32 depth in mm
 */
import { useEffect, useRef, useState, useCallback } from 'react';

const WS_URL = `ws://${window.location.hostname}:8000/ws/camera`;
const RECONNECT_DELAY_MS = 2000;

export default function useCameraStream({ onFrame, enabled = true } = {}) {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const [status, setStatus] = useState('idle'); // idle | connecting | connected | error | closed
  const [metadata, setMetadata] = useState(null); // {width, height, fps, simulated}
  const frameCountRef = useRef(0);
  const lastFpsTimeRef = useRef(performance.now());
  const [fps, setFps] = useState(0);

  const connect = useCallback(() => {
    if (!enabled) return;
    setStatus('connecting');

    const ws = new WebSocket(WS_URL);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      setMetadata(null);
      frameCountRef.current = 0;
      lastFpsTimeRef.current = performance.now();
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        // JSON header — parse metadata
        try {
          const meta = JSON.parse(event.data);
          if (meta.type === 'depth_frame') {
            setMetadata({
              width: meta.width,
              height: meta.height,
              fps: meta.fps,
              simulated: meta.simulated,
            });
          }
        } catch (_) {}
      } else if (event.data instanceof ArrayBuffer) {
        // Binary depth frame — raw float32 depth data (no header prefix)
        // Header arrives as a separate text message before this binary frame
        const depthBytes = new Uint8Array(event.data);

        // Convert to Float32Array (depth in mm)
        const depthData = new Float32Array(depthBytes.buffer, depthBytes.byteOffset, depthBytes.byteLength / 4);

        // Use metadata from the last received text header
        const w = metadata?.width ?? 640;
        const h = metadata?.height ?? 480;

        // FPS counter
        frameCountRef.current++;
        const now = performance.now();
        if (now - lastFpsTimeRef.current >= 1000) {
          setFps(Math.round(frameCountRef.current * 1000 / (now - lastFpsTimeRef.current)));
          frameCountRef.current = 0;
          lastFpsTimeRef.current = now;
        }

        onFrame?.({ depthData, width: w, height: h, simulated: metadata?.simulated ?? false });
      }
    };

    ws.onerror = () => {
      setStatus('error');
    };

    ws.onclose = () => {
      setStatus('closed');
      wsRef.current = null;
      if (enabled) {
        reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
      }
    };
  }, [enabled, onFrame]);

  useEffect(() => {
    if (!enabled) {
      wsRef.current?.close();
      clearTimeout(reconnectTimer.current);
      setStatus('idle');
      return;
    }
    connect();
    return () => {
      wsRef.current?.close();
      clearTimeout(reconnectTimer.current);
    };
  }, [enabled, connect]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    setStatus('idle');
  }, []);

  return { status, metadata, fps, disconnect };
}
