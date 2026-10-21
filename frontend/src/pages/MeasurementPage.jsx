/**
 * MeasurementPage.jsx — 人体测量页面（RealSense 深度流）。
 *
 * Data flow (SPEC §3.2):
 *   capture.py (ws://localhost:8765)
 *     → FastAPI /ws/camera relay
 *     → useCameraStream (depth frames)
 *     → useMeasurement (coarse compute, real-time)
 *     → DepthCanvas (2D depth map visualization)
 *     → POST /api/ai/measure → useAIInference (precise result)
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import Navbar from '../components/Navbar';
import DepthCanvas from '../components/DepthCanvas';
import useCameraStream from '../hooks/useCameraStream';
import useMeasurement from '../hooks/useMeasurement';
import useAIInference from '../hooks/useAIInference';
import '../styles/global.css';

export default function MeasurementPage() {
  const [coarseData, setCoarseData] = useState(null);
  // One instance only: DepthStage's live overlay and the panel's scan controls
  // must read and write the same scanner state.
  const measurement = useMeasurement();

  return (
    <div className="app">
      <Navbar />

      <main className="main">
        <div className="stage">
          <DepthStage measurement={measurement} onCoarseResult={setCoarseData} />
        </div>
        <aside className="side">
          <MeasurementPanel coarseData={coarseData} measurement={measurement} />
        </aside>
      </main>
    </div>
  );
}

/* ─────────────────────────── DepthStage ─────────────────────────── */

function DepthStage({ measurement, onCoarseResult }) {
  const { latest: hookLatest, isScanning, processFrame } = measurement;

  const [depthData, setDepthData] = useState(null);
  const [depthSize, setDepthSize] = useState({ width: 640, height: 480 });

  const handleFrame = useCallback((frame) => {
    processFrame(frame);
    setDepthData(frame.depthData);
    setDepthSize({ width: frame.width, height: frame.height });
  }, [processFrame]);

  const { status: camStatus, metadata: camMeta, fps: camFps } = useCameraStream({
    onFrame: handleFrame,
    enabled: true,
  });

  const [latest, setLatest] = useState(null);

  // Sync live coarse result to parent and local state
  useEffect(() => {
    if (hookLatest) {
      setLatest(hookLatest);
      onCoarseResult?.(hookLatest);
    }
  }, [hookLatest, onCoarseResult]);

  const width  = camMeta?.width  ?? depthSize.width;
  const height = camMeta?.height ?? depthSize.height;

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Depth canvas fills the stage */}
      <div style={{
        position: 'absolute', inset: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: '#000',
        overflow: 'hidden',
      }}>
        <DepthCanvas
          depthData={depthData}
          width={width}
          height={height}
          status={camStatus}
          fps={camFps}
        />
      </div>

      {/* Live coarse measurements overlay — top-left */}
      {isScanning && latest && (
        <div style={{
          position: 'absolute',
          top: 8,
          left: 8,
          background: 'rgba(0,0,0,0.65)',
          borderRadius: 6,
          padding: '6px 12px',
          fontSize: 12,
          fontFamily: 'monospace',
          color: '#e2e8f0',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}>
          <div style={{ color: '#34d399', fontWeight: 600, marginBottom: 2 }}>粗算结果</div>
          <div>身高: {latest.height} cm</div>
          <div>肩宽: {latest.shoulder_width} cm</div>
          <div>胸围: {latest.chest} cm</div>
          <div>腰围: {latest.waist} cm</div>
        </div>
      )}

      {/* Connection status badge — top-right */}
      <div style={{
        position: 'absolute',
        top: 8,
        right: 8,
        background: 'rgba(0,0,0,0.65)',
        borderRadius: 6,
        padding: '4px 10px',
        fontSize: 12,
        fontFamily: 'monospace',
        color: {
          connecting: '#f59e0b',
          connected:   '#34d399',
          error:       '#f87171',
          closed:      '#f59e0b',
          idle:        '#64748b',
        }[camStatus] ?? '#64748b',
      }}>
        {{
          connecting: '连接中...',
          connected:  `已连接 · ${camFps} FPS`,
          error:     '未连接',
          closed:    '未连接（重连中...）',
          idle:      '未连接',
        }[camStatus] ?? camStatus}
      </div>
    </div>
  );
}

/* ───────────────────────── MeasurementPanel ─────────────────────── */

function MeasurementPanel({ coarseData, measurement }) {
  const { measure, pollStatus, loading: aiLoading, error: aiError } = useAIInference();

  const [aiState, setAiState] = useState('idle'); // idle | scanning | measuring | done | error
  const [preciseResult, setPreciseResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const taskIdRef = useRef(null);

  const { latest, isScanning, startScan, stopScan } = measurement;

  // Polling effect: start polling when taskId is set, cancel on cleanup/change
  useEffect(() => {
    const tid = taskIdRef.current;
    if (!tid) return;

    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      setAiState('error');
      setErrorMsg('AI 测量超时（60 秒）');
      pollStatus.cancelPoll?.(tid);
    }, 60_000);

    pollStatus(tid, {
      interval: 2000,
      maxAttempts: 30,
      onResult: (status) => {
        if (timedOut) return;
        clearTimeout(timer);
        if (status.status === 'done') {
          setPreciseResult(status.result ?? status);
          setAiState('done');
        } else if (status.status === 'error' || status.status === 'timeout') {
          setErrorMsg(status.error ?? 'AI 测量失败');
          setAiState('error');
        }
      },
    });

    return () => {
      clearTimeout(timer);
      pollStatus.cancelPoll?.(tid);
    };
  }, [taskIdRef.current]); // eslint-disable-line

  const handleStartScan = () => {
    setAiState('scanning');
    setErrorMsg('');
    setPreciseResult(null);
    startScan();
  };

  const handleStopAndMeasure = async () => {
    const coarse = stopScan();
    if (!coarse) {
      setAiState('error');
      setErrorMsg('未能获取有效粗算数据');
      return;
    }

    setAiState('measuring');
    setErrorMsg('');

    try {
      const res = await measure(coarse);
      taskIdRef.current = res.task_id;
    } catch (e) {
      setAiState('error');
      setErrorMsg(`请求失败: ${e.message}`);
    }
  };

  const handleRetry = () => {
    taskIdRef.current = null;
    setAiState('idle');
    setPreciseResult(null);
    setErrorMsg('');
  };

  // Merge coarse live data for display during scanning
  const liveResult = preciseResult ?? latest ?? coarseData ?? {};

  return (
    <div className="panel">
      <h3>人体测量</h3>

      {/* ── idle ── */}
      {aiState === 'idle' && (
        <>
          <p className="muted">对准摄像头，点击开始扫描</p>
          <div className="row">
            <button
              className="apply"
              style={{ flex: 1, padding: '8px 12px' }}
              onClick={handleStartScan}
            >
              开始扫描
            </button>
          </div>
        </>
      )}

      {/* ── scanning ── */}
      {aiState === 'scanning' && (
        <>
          <p className="muted" style={{ marginBottom: 8 }}>
            实时粗算（请保持站立不动）
          </p>
          <div className="measure-cards" style={{ fontSize: 13 }}>
            <MeasureCard label="身高" value={liveResult.height} />
            <MeasureCard label="肩宽" value={liveResult.shoulder_width} />
            <MeasureCard label="胸围" value={liveResult.chest} />
            <MeasureCard label="腰围" value={liveResult.waist} />
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button
              className="apply"
              style={{ flex: 1, padding: '8px 12px' }}
              onClick={handleStopAndMeasure}
            >
              停止扫描 + 精确测量
            </button>
          </div>
        </>
      )}

      {/* ── measuring ── */}
      {aiState === 'measuring' && (
        <div className="row">
          <span className="spinner" />
          <span className="muted">AI 精确测量中...</span>
        </div>
      )}

      {/* ── done ── */}
      {aiState === 'done' && preciseResult && (
        <>
          <div className="measure-cards">
            <MeasureCard label="身高"  value={preciseResult.height} />
            <MeasureCard label="肩宽"  value={preciseResult.shoulder_width} />
            <MeasureCard label="胸围"  value={preciseResult.chest} />
            <MeasureCard label="腰围"  value={preciseResult.waist} />
            <MeasureCard label="臀围"  value={preciseResult.hip ?? preciseResult.hips} />
            <MeasureCard label="臂长"  value={preciseResult.arm_length ?? preciseResult.inseam} />
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button
              className="apply"
              style={{ flex: 1 }}
              onClick={handleRetry}
            >
              重新测量
            </button>
          </div>
        </>
      )}

      {/* ── error ── */}
      {aiState === 'error' && (
        <>
          <p className="err">错误：{errorMsg}</p>
          <div className="row" style={{ marginTop: 8 }}>
            <button
              className="apply"
              style={{ flex: 1 }}
              onClick={handleRetry}
            >
              重试
            </button>
          </div>
        </>
      )}
    </div>
  );
}

/* ─────────────────────────── MeasureCard ───────────────────────── */

function MeasureCard({ label, value }) {
  if (value == null) return null;
  return (
    <div className="measure-card">
      <div className="measure-label">{label}</div>
      <div className="measure-value">
        {typeof value === 'number' ? value.toFixed(1) : value}
        <span> cm</span>
      </div>
    </div>
  );
}
