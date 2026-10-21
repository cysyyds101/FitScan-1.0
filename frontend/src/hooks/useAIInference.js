/**
 * useAIInference.js — AI 服务器推理调用 hook.
 *
 * 封装所有 AI 服务器通信：
 *  - POST /api/ai/measure       精确测量
 *  - POST /api/ai/generate      3D 模型生成
 *  - GET  /api/ai/status/{tid} 轮询任务状态
 */
import { useCallback, useRef, useState } from 'react';

const API = (import.meta.env.VITE_API_BASE ?? '/api') + '/ai';

async function postJSON(url, body) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

async function getJSON(url) {
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

/**
 * useAIInference hook.
 *
 * Usage:
 *   const { measure, generate, pollStatus, loading, error } = useAIInference();
 */
export default function useAIInference() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollTimers = useRef({});

  // ─── Precise measurement ──────────────────────────────────────────────────

  const measure = useCallback(async (coarseData) => {
    setLoading(true);
    setError(null);
    try {
      const result = await postJSON(`${API}/measure`, { coarse_data: coarseData });
      return result; // {task_id, status, measurement?}
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  // ─── 3D model generation ────────────────────────────────────────────────

  const generate = useCallback(async (prompt) => {
    setLoading(true);
    setError(null);
    try {
      const result = await postJSON(`${API}/generate`, { prompt });
      return result; // {task_id, status, model_url?}
    } catch (e) {
      setError(e.message);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  // ─── Status polling ─────────────────────────────────────────────────────

  const pollStatus = useCallback((taskId, { onResult, interval = 2000, maxAttempts = 30 } = {}) => {
    let attempts = 0;
    const tid = setInterval(async () => {
      attempts++;
      try {
        const status = await getJSON(`${API}/status/${taskId}`);
        if (status.status === 'done' || status.status === 'error') {
          clearInterval(tid);
          delete pollTimers.current[taskId];
          onResult?.(status);
        } else if (attempts >= maxAttempts) {
          clearInterval(tid);
          delete pollTimers.current[taskId];
          onResult?.({ task_id: taskId, status: 'timeout' });
        }
      } catch (e) {
        // Silently retry
      }
    }, interval);
    pollTimers.current[taskId] = tid;
  }, []);

  const cancelPoll = useCallback((taskId) => {
    clearInterval(pollTimers.current[taskId]);
    delete pollTimers.current[taskId];
  }, []);

  return { measure, generate, pollStatus, cancelPoll, loading, error };
}
