/**
 * MeasurementPage.jsx — 人体测量页面（拍照上传流）。
 *
 * 流程：
 * 1. getUserMedia → 实时摄像头预览（前置摄像头）
 * 2. 用户拍摄最多 2 张：正面 / 侧面
 * 3. 自动上传 → POST /api/uploads 收集 upload_ids
 * 4. 触发测量 → POST /api/measurements { upload_ids }
 * 5. 轮询 GET /api/measurements/{id}（2s）直到 status=done
 * 6. 显示身高 / 胸围 / 腰围 / 臀围
 *
 * 注意：当前 useCameraStream 是 RealSense 深度流 WebSocket hook，不适合
 * 拍照流程。本组件直接用浏览器 getUserMedia，不依赖 useCameraStream。
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { uploadsApi } from '../api/client';
import Navbar from '../components/Navbar';
import '../styles/global.css';

const SHOT_LABELS = ['正面', '侧面'];
const MAX_SHOTS = 2;

export default function MeasurementPage() {
  // shots live in the page so CameraStage (writer) and MeasurementPanel
  // (reader/uploader) can share them via plain props.
  const [shots, setShots] = useState([]); // [{label, file, url}]

  const addShot = useCallback((shot) => {
    setShots((prev) => (prev.length >= MAX_SHOTS ? prev : [...prev, shot]));
  }, []);

  const resetShots = useCallback(() => {
    setShots((prev) => {
      prev.forEach((s) => URL.revokeObjectURL(s.url));
      return [];
    });
  }, []);

  return (
    <div className="app">
      <Navbar />

      <main className="main">
        <div className="stage">
          <CameraStage shots={shots} addShot={addShot} resetShots={resetShots} />
        </div>
        <aside className="side">
          <MeasurementPanel shots={shots} resetShots={resetShots} />
        </aside>
      </main>
    </div>
  );
}

/* ─────────────────────────── CameraStage ─────────────────────────── */

function CameraStage({ shots, addShot, resetShots }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);

  // Start / stop webcam on mount / unmount
  useEffect(() => {
    let cancelled = false;
    const start = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: 1280, height: 720 },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      } catch (e) {
        setError(e.message || '无法访问摄像头');
      }
    };
    start();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    };
  }, []);

  const capture = useCallback(() => {
    const video = videoRef.current;
    if (!video || !streamRef.current) return;

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (!blob) return;
      const idx = shots.length;
      const url = URL.createObjectURL(blob);
      const file = new File([blob], `shot-${idx}.jpg`, { type: 'image/jpeg' });
      addShot({ label: SHOT_LABELS[idx], file, url });
    }, 'image/jpeg', 0.92);
  }, [shots.length, addShot]);

  const retake = useCallback(() => {
    resetShots();
  }, [resetShots]);

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#000' }}>
      {error ? (
        <div style={{
          position: 'absolute', inset: 0, display: 'flex',
          alignItems: 'center', justifyContent: 'center',
          color: '#fca5a5', fontSize: 14, padding: 20, textAlign: 'center',
        }}>
          摄像头错误：{error}
        </div>
      ) : (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      )}

      {shots.length < MAX_SHOTS && !error && (
        <button
          type="button"
          className="capture-btn"
          onClick={capture}
        >
          📸 拍照 ({shots.length + 1}/{MAX_SHOTS})
        </button>
      )}

      {shots.length === MAX_SHOTS && (
        <button
          type="button"
          className="retake-btn"
          onClick={retake}
        >
          重新拍摄
        </button>
      )}

      {shots.length > 0 && (
        <div className="shot-thumbs">
          {shots.map((s, i) => (
            <img
              key={i}
              className="shot-thumb"
              src={s.url}
              alt={s.label}
              title={s.label}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/* ───────────────────────── MeasurementPanel ───────────────────────── */

function MeasurementPanel({ shots, resetShots }) {
  const [phase, setPhase] = useState('idle'); // idle | uploading | measuring | done | error
  const [progress, setProgress] = useState({ uploaded: 0, total: 0 });
  const [result, setResult] = useState(null); // { height, chest, waist, hips }
  const [errorMsg, setErrorMsg] = useState('');

  // Reset to idle if shots were cleared (e.g. user hit "重新拍摄" then idle again)
  useEffect(() => {
    if (phase === 'done' && shots.length === 0) {
      setPhase('idle');
      setResult(null);
    }
  }, [shots.length, phase]);

  const startMeasure = useCallback(async () => {
    if (shots.length === 0) return;

    setPhase('uploading');
    setErrorMsg('');
    setProgress({ uploaded: 0, total: shots.length });

    // 1. Sequential upload
    const uploadIds = [];
    for (let i = 0; i < shots.length; i++) {
      try {
        const r = await uploadsApi.create(shots[i].file);
        uploadIds.push(r.id);
        setProgress({ uploaded: i + 1, total: shots.length });
      } catch (e) {
        setPhase('error');
        setErrorMsg(`上传失败 (${i + 1}/${shots.length}): ${e.message || e}`);
        return;
      }
    }

    // 2. Trigger measurement
    setPhase('measuring');
    // TODO: replace mock with real POST /api/measurements
    // const session = await measurementsApi.create({ upload_ids: uploadIds });
    // const sessionId = session.id;
    const sessionId = 'mock-' + Date.now();
    const mockResult = { height: 172, chest: 92, waist: 76, hips: 96 };

    // 3. Poll every 2s until done
    const poll = setInterval(async () => {
      try {
        // TODO: replace mock with real GET /api/measurements/{id}
        // const r = await measurementsApi.get(sessionId);
        // if (r.status === 'done') { ... }
        // Simulated: complete after first poll
        clearInterval(poll);
        setResult(mockResult);
        setPhase('done');
      } catch (e) {
        clearInterval(poll);
        setPhase('error');
        setErrorMsg(`轮询失败: ${e.message || e}`);
      }
    }, 2000);
  }, [shots]);

  const reset = () => {
    setPhase('idle');
    setResult(null);
    setErrorMsg('');
    setProgress({ uploaded: 0, total: 0 });
    resetShots();
  };

  return (
    <div className="panel">
      <h3>人体测量</h3>

      {phase === 'idle' && (
        <>
          <p className="muted">点击拍照开始 · 已拍 {shots.length}/{MAX_SHOTS}</p>
          {shots.length > 0 && shots.length < MAX_SHOTS && (
            <p className="muted">提示：还差 {MAX_SHOTS - shots.length} 张（{SHOT_LABELS[shots.length]}）</p>
          )}
          <div className="row">
            <button
              className="apply"
              style={{ flex: 1, padding: '8px 12px' }}
              onClick={startMeasure}
              disabled={shots.length === 0}
            >
              开始测量
            </button>
          </div>
        </>
      )}

      {phase === 'uploading' && (
        <div className="row">
          <span className="spinner" />
          <span className="muted">
            上传中... {progress.uploaded}/{progress.total}
          </span>
        </div>
      )}

      {phase === 'measuring' && (
        <div className="row">
          <span className="spinner" />
          <span className="muted">测量中...（约10秒）</span>
        </div>
      )}

      {phase === 'done' && result && (
        <>
          <div className="measure-cards">
            <MeasureCard label="身高" value={result.height} />
            <MeasureCard label="胸围" value={result.chest} />
            <MeasureCard label="腰围" value={result.waist} />
            <MeasureCard label="臀围" value={result.hips} />
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="apply" onClick={reset} style={{ flex: 1 }}>
              重新测量
            </button>
          </div>
        </>
      )}

      {phase === 'error' && (
        <>
          <p className="err">错误：{errorMsg}</p>
          <div className="row">
            <button className="apply" onClick={reset} style={{ flex: 1 }}>
              重试
            </button>
          </div>
        </>
      )}
    </div>
  );
}

function MeasureCard({ label, value }) {
  return (
    <div className="measure-card">
      <div className="measure-label">{label}</div>
      <div className="measure-value">
        {value}
        <span> cm</span>
      </div>
    </div>
  );
}
