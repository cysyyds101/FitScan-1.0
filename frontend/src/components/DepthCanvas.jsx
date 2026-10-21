/**
 * DepthCanvas.jsx — 实时深度图画布（2D）。
 *
 * 渲染从 useCameraStream 接收的 Float32 depth 数据为伪彩色热力图。
 * 不使用 Three.js，纯 2D Canvas API。
 *
 * 用法:
 *   <DepthCanvas width={640} height={480} fps={fps} status={status} />
 *
 * 色彩映射：near (蓝) → mid (绿/黄) → far (红)
 */
import { useEffect, useRef } from 'react';

const W = 640;
const H = 480;

// Pseudo-color LUT: index 0-255 → [R,G,B]
// Blue(0) → Cyan → Green → Yellow → Red(255)
function depthToRGB(depth_mm, near = 500, far = 2500) {
  const t = Math.max(0, Math.min(1, (depth_mm - near) / (far - near)));
  const i = Math.floor(t * 255);
  const r = Math.min(255, Math.max(0, 2 * i - 256));
  const g = Math.min(255, Math.max(0, 2 * i));
  const b = Math.min(255, Math.max(0, 2 * (256 - i)));
  return `${r},${g},${b}`;
}

export default function DepthCanvas({ depthData, width = W, height = H, fps, status, simulated }) {
  const canvasRef = useRef(null);
  const lastFpsRef = useRef(0);

  useEffect(() => {
    if (!depthData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const imageData = ctx.createImageData(width, height);
    const d = imageData.data;

    for (let i = 0; i < width * height; i++) {
      const depth = depthData[i];
      let r, g, b;

      if (depth <= 0 || depth > 3000) {
        // No-data pixel: dark
        r = g = b = 15;
      } else {
        const t = Math.max(0, Math.min(1, (depth - 500) / 2000));
        const idx = Math.floor(t * 255);
        r = Math.min(255, Math.max(0, 2 * idx - 256));
        g = Math.min(255, Math.max(0, 2 * idx));
        b = Math.min(255, Math.max(0, 2 * (256 - idx)));
      }

      d[i * 4]     = r;
      d[i * 4 + 1] = g;
      d[i * 4 + 2] = b;
      d[i * 4 + 3] = 255;
    }

    ctx.putImageData(imageData, 0, 0);

    // FPS update (throttled)
    if (fps && fps !== lastFpsRef.current) {
      lastFpsRef.current = fps;
    }
  }, [depthData, width, height, fps]);

  const statusColor = {
    idle: '#64748b',
    connecting: '#f59e0b',
    connected: '#34d399',
    error: '#f87171',
    closed: '#f59e0b',
  }[status] ?? '#64748b';

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        style={{
          display: 'block',
          borderRadius: '8px',
          background: '#0f172a',
          maxWidth: '100%',
          maxHeight: '100vh',
          objectFit: 'contain',
        }}
      />
      {/* Status overlay */}
      <div style={{
        position: 'absolute',
        top: 8,
        left: 8,
        background: 'rgba(0,0,0,0.65)',
        borderRadius: '6px',
        padding: '4px 10px',
        fontSize: 12,
        fontFamily: 'monospace',
        color: statusColor,
        display: 'flex',
        gap: 12,
        alignItems: 'center',
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%',
            background: statusColor,
            display: 'inline-block',
          }} />
          {status}
        </span>
        {fps > 0 && <span>{fps} FPS</span>}
        {simulated && <span style={{ color: '#f59e0b' }}>SIMULATED</span>}
      </div>
      {/* Color bar legend */}
      <div style={{
        position: 'absolute',
        right: 8,
        bottom: 8,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        gap: 2,
      }}>
        <div style={{ fontSize: 10, color: '#94a3b8', fontFamily: 'monospace' }}>2500mm</div>
        <div style={{
          width: 12, height: 80,
          background: 'linear-gradient(to bottom, #ff4444, #ffff00, #00ff00, #00ffff, #4444ff)',
          borderRadius: 3,
        }} />
        <div style={{ fontSize: 10, color: '#94a3b8', fontFamily: 'monospace' }}>500mm</div>
      </div>
    </div>
  );
}
