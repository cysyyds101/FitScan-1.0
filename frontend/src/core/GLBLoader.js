/**
 * 统一 GLB 加载器（核心层）。
 *
 * 规则（Frontend Rule）：
 *  - 所有 3D 组件必须通过此 loader 加载 GLB
 *  - 不允许在组件内自己 new GLTFLoader
 *  - 提供 url -> scene 缓存
 *  - 通过 useGLTF 触发加载并暴露 loading / error
 */
import { useGLTF } from '@react-three/drei';
import { useEffect, useMemo, useState } from 'react';

// 预热缓存：让 drei 内部按 url 复用同一份 GLTF
const _cache = new Set();
const _validityCache = new Map();  // url -> boolean (valid GLB?)

export function preloadGLB(url) {
  if (!url || _cache.has(url)) return;
  _cache.add(url);
  try {
    useGLTF.preload(url);
  } catch (_) {
    /* ignore */
  }
}

/**
 * 探测 URL 是否是合法 GLB（首 4 字节 === 'glTF'）。
 * 用于在 useGLTF 之前挡住：404 的（不存在）、或返回 200 但内容损坏的（如 demo 里
 * 那些被误填成二进制垃圾的占位文件）—— useGLTF 对后者会抛 "is not valid JSON"。
 *
 * 结果按 url 缓存，避免重复 fetch。
 */
export async function isValidGLB(url) {
  if (!url) return false;
  if (_validityCache.has(url)) return _validityCache.get(url);
  try {
    const r = await fetch(url, { cache: 'no-cache' });
    if (!r.ok) {
      _validityCache.set(url, false);
      return false;
    }
    const buf = await r.arrayBuffer();
    const ok = validateGLBBuffer(buf);
    _validityCache.set(url, ok);
    if (!ok) {
      // eslint-disable-next-line no-console
      console.warn(`[GLBLoader] ${url} is not a loadable GLB, falling back to procedural`);
    }
    return ok;
  } catch (e) {
    _validityCache.set(url, false);
    return false;
  }
}

/**
 * A GLB is a 12-byte header (magic "glTF", version, totalLength) followed by chunks.
 * Checking the magic alone is not enough: 12-byte stubs that declare totalLength=0
 * passed validation and then rendered nothing, which made the procedural fallback
 * look like a working 3D garment.
 */
export function validateGLBBuffer(buf) {
  if (!buf || buf.byteLength < 12) return false;
  const view = new DataView(buf);
  const magic = String.fromCharCode(
    view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3),
  );
  if (magic !== 'glTF') return false;
  if (view.getUint32(4, true) !== 2) return false;
  const totalLength = view.getUint32(8, true);
  return totalLength >= 12 && totalLength === buf.byteLength;
}

/**
 * 在组件内安全地加载一个 GLB。
 * 返回 { scene, loading, error }。
 */
export function useGLBModel(url, fallback = true) {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // useGLTF 内部会 throw promise 让 Suspense 处理，我们用 try/catch 兜底
  let gltf = null;
  try {
    gltf = url ? useGLTF(url, true, true, (e) => setError(e)) : null;
  } catch (e) {
    // Suspense fallback 已经在父级处理，这里只做标记
    error && setError(e);
  }

  useEffect(() => {
    if (!url) {
      setLoading(false);
      return;
    }
    setLoading(false);
  }, [url]);

  return { scene: gltf?.scene ?? null, loading, error };
}
