/**
 * ClothingControls.jsx — 合并后的统一控制面板。
 *
 * 由两个原面板合并而成：
 *  - 服装列表选择（来源：旧 ClothingPanel.jsx）
 *  - 位置/旋转/缩放滑块 + 伪布料开关 + 重置（来源：旧 ControlSliders.jsx）
 *  - H1: ⬆ 用户上传 GLB 服装
 *
 * 规则（Frontend Rule #5）：
 *  - UI 只发事件，不直接操作 3D 对象
 *  - 所有 onChange 通过 props 回调上抛
 *
 * H1 设计：
 *  - useClothingList 自定义 hook 集中管理服装列表（拉取 + 上传后追加）
 *  - UploadPanel 子组件做 multipart POST
 *  - 上传成功后调 onUploaded(item) 回调，让 page 层可以选择自动选中
 *  - 上传后立即把新 item 追加到本地 list，无需重新拉取
 */
import { useEffect, useState, useCallback, useRef } from 'react';

const API_BASE = (import.meta.env.VITE_API_BASE ?? '/api');

export const DEFAULT_TRANSFORM = {
  position: [0, 0, 0],
  rotation: [0, 0, 0],
  scale: [1, 1, 1],
};

const SLIDER_ROWS = [
  { key: 'posX', label: '位置 X', min: -1, max: 1, step: 0.01, axis: 0, group: 'position' },
  { key: 'posY', label: '位置 Y', min: -1, max: 1, step: 0.01, axis: 1, group: 'position' },
  { key: 'posZ', label: '位置 Z', min: -1, max: 1, step: 0.01, axis: 2, group: 'position' },
  { key: 'rotX', label: '旋转 X', min: -Math.PI, max: Math.PI, step: 0.01, axis: 0, group: 'rotation' },
  { key: 'rotY', label: '旋转 Y', min: -Math.PI, max: Math.PI, step: 0.01, axis: 1, group: 'rotation' },
  { key: 'rotZ', label: '旋转 Z', min: -Math.PI, max: Math.PI, step: 0.01, axis: 2, group: 'rotation' },
  { key: 'scl',  label: '缩放',   min: 0.5, max: 1.8, step: 0.01, axis: 0, group: 'scale' },
];

const CATEGORY_OPTIONS = [
  { value: 'top',       label: '上装' },
  { value: 'bottom',    label: '下装' },
  { value: 'outer',     label: '外套' },
  { value: 'full',      label: '全身' },
  { value: 'accessory', label: '配件' },
];

function getValue(transform, row) {
  if (row.group === 'scale') return transform.scale[row.axis];
  return transform[row.group][row.axis];
}

function setValue(transform, row, v) {
  const next = JSON.parse(JSON.stringify(transform));
  if (row.group === 'scale') {
    next.scale = [v, v, v];
  } else {
    next[row.group][row.axis] = v;
  }
  return next;
}

/**
 * H1: 自定义 hook 管理服装列表（GET + 手动追加）。
 */
function useClothingList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API_BASE}/clothing`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      setItems(data.items ?? []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const append = useCallback((item) => {
    setItems((prev) => [...prev, item]);
  }, []);

  return { items, loading, error, refresh, append };
}

/**
 * 服装选择子组件（受控：items 由父组件传入）。
 */
function ClothingList({ items, loading, error, selectedId, onSelect }) {
  if (loading) {
    return (
      <div className="panel">
        <h3>服装</h3>
        <p className="muted">加载中...</p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="panel">
        <h3>服装</h3>
        <p className="err">无法连接后端：{error}</p>
        <p className="muted">请确保 FastAPI 在 :8000 端口运行</p>
      </div>
    );
  }

  return (
    <div className="panel">
      <h3>服装</h3>
      <div className="list">
        {items.map((it) => (
          <button
            key={it.id}
            className={`item ${selectedId === it.id ? 'active' : ''}`}
            onClick={() => onSelect(it)}
          >
            <span className="item-main">
              <span className="dot" data-id={it.id} />
              <span>
                <div className="name">{it.name}</div>
                <div className="meta">
                  {it.category}
                  {it.id?.startsWith('usr-') && ' · 自定义'}
                </div>
              </span>
            </span>
          </button>
        ))}
        {items.length === 0 && <p className="muted">暂无服装，请上传一个 .glb</p>}
      </div>
    </div>
  );
}

/**
 * H1: 用户上传 GLB 子组件。
 */
function UploadPanel({ onUploaded }) {
  const [name, setName] = useState('');
  const [category, setCategory] = useState('top');
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileInputRef = useRef(null);

  const reset = () => {
    setName('');
    setFile(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!f.name.toLowerCase().endsWith('.glb')) {
      setError('请选择 .glb 文件');
      return;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError(`文件过大（${(f.size / 1024 / 1024).toFixed(1)} MB），最大 10 MB`);
      return;
    }
    setFile(f);
    setError(null);
    // Default name to filename without extension
    if (!name) {
      setName(f.name.replace(/\.glb$/i, ''));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('请先选择 .glb 文件');
      return;
    }
    setBusy(true);
    setError(null);
    setSuccess(null);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('category', category);
      if (name.trim()) form.append('name', name.trim());
      const r = await fetch(`${API_BASE}/clothing/upload`, {
        method: 'POST',
        body: form,
      });
      if (!r.ok) {
        const detail = await r.json().catch(() => ({ detail: `HTTP ${r.status}` }));
        throw new Error(detail.detail || `HTTP ${r.status}`);
      }
      const item = await r.json();
      setSuccess(`已添加：${item.name}`);
      onUploaded?.(item);
      reset();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="panel">
      <h3>上传服装 (.glb)</h3>
      <form onSubmit={handleSubmit}>
        <div className="row">
          <label>
            <span>文件</span>
            {file && <span className="val">{(file.size / 1024).toFixed(1)} KB</span>}
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".glb,model/gltf-binary"
            onChange={handleFile}
            disabled={busy}
          />
        </div>
        <div className="row">
          <label><span>名称（可选）</span></label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="默认使用文件名"
            disabled={busy}
            style={{
              flex: 1, padding: '6px 8px', background: '#0f172a',
              color: '#e2e8f0', border: '1px solid #334155', borderRadius: 4,
            }}
          />
        </div>
        <div className="row">
          <label><span>类别</span></label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            disabled={busy}
            style={{
              flex: 1, padding: '6px 8px', background: '#0f172a',
              color: '#e2e8f0', border: '1px solid #334155', borderRadius: 4,
            }}
          >
            {CATEGORY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>
        {error && <p className="err">上传失败：{error}</p>}
        {success && <p className="muted" style={{ color: '#10b981' }}>{success}</p>}
        <button
          type="submit"
          className="apply"
          disabled={!file || busy}
          style={{ width: '100%', marginTop: 4 }}
        >
          {busy ? '上传中…' : '⬆ 上传'}
        </button>
      </form>
    </div>
  );
}

/**
 * 变换控制子组件。
 */
function TransformPanel({ transform, setTransform, vertexOffset, setVertexOffset }) {
  const reset = () => setTransform(DEFAULT_TRANSFORM);

  return (
    <div className="panel">
      <h3>变换控制</h3>
      {SLIDER_ROWS.map((row) => {
        const v = getValue(transform, row);
        return (
          <div className="row" key={row.key}>
            <label>
              <span>{row.label}</span>
              <span className="val">{v.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min={row.min}
              max={row.max}
              step={row.step}
              value={v}
              onChange={(e) => setTransform(setValue(transform, row, parseFloat(e.target.value)))}
            />
          </div>
        );
      })}

      <div className="row toggle">
        <label>
          <input
            type="checkbox"
            checked={vertexOffset}
            onChange={(e) => setVertexOffset(e.target.checked)}
          />
          <span>伪布料（vertex offset）</span>
        </label>
      </div>

      <button className="reset" onClick={reset}>
        重置
      </button>
    </div>
  );
}

/**
 * ClothingControls — 统一对外组件。
 *
 * Props:
 *  - selectedId, onSelect           (服装选择)
 *  - transform, setTransform         (变换)
 *  - vertexOffset, setVertexOffset   (伪布料)
 *
 * H1 行为：
 *  - 上传新 GLB 成功后：自动调 onSelect(item) 立即试穿
 *
 * Page/容器层只 import 这一个文件。
 */
export default function ClothingControls({
  selectedId,
  onSelect,
  transform,
  setTransform,
  vertexOffset,
  setVertexOffset,
}) {
  const { items, loading, error, append } = useClothingList();

  const handleUploaded = (item) => {
    append(item);
    onSelect?.(item);
  };

  return (
    <>
      <ClothingList
        items={items}
        loading={loading}
        error={error}
        selectedId={selectedId}
        onSelect={onSelect}
      />
      <UploadPanel onUploaded={handleUploaded} />
      {transform !== undefined && (
        <TransformPanel
          transform={transform}
          setTransform={setTransform}
          vertexOffset={vertexOffset}
          setVertexOffset={setVertexOffset}
        />
      )}
    </>
  );
}
