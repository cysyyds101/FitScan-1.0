// ReconstructionPanel — 上传 + normalize + recon 的 UI 面板。
//
// 流程（multi-image, 1–8 张）：
//   1. 用户选 1–8 张图（<input multiple>）→ 缩略图预览
//   2. 点"上传" → 逐张 POST /api/uploads（FormData），收集 upload_ids
//   3. 逐张触发 normalize（best-effort）
//   4. 点"触发重建" → POST /api/reconstructions {method, image_urls}
//        - 1 张 → method = "smpl_fast"
//        - 2–8 张 → method = "smpl_multi"
//        - image_urls: uploadIds.map(id => `/uploads/{id}/normalized`)
//   5. useReconstructions hook 轮询，AI server 完成 → status=done
//   6. 用户点"使用此模型" → onPickedGlb(glb_url)

import { useEffect, useRef, useState } from "react";
import { uploadsApi, reconstructionsApi } from "../api/client";
import { useReconstructions } from "../hooks/useReconstructions";

const STATUS_BADGE = {
  pending:    { label: "等待", color: "#a3a3a3" },
  processing: { label: "处理中", color: "#f59e0b" },
  done:       { label: "完成", color: "#10b981" },
  failed:     { label: "失败", color: "#ef4444" },
};

const MAX_IMAGES = 8;

export default function ReconstructionPanel({ uploadId, onUploadId, onPickedGlb }) {
  const [files, setFiles] = useState([]);           // [{file, previewUrl}]
  const [uploadIds, setUploadIds] = useState([]);   // ordered parallel to files
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [triggering, setTriggering] = useState(false);
  const [triggerError, setTriggerError] = useState(null);

  // Revoke object URLs when files change / unmount to avoid memory leaks.
  const previewsRef = useRef([]);
  useEffect(() => {
    previewsRef.current = files.map((f) => f.previewUrl);
    return () => {
      previewsRef.current.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [files]);

  // Sync the "primary" uploadId to the parent (first uploaded image).
  useEffect(() => {
    if (uploadIds.length > 0) onUploadId?.(uploadIds[0]);
  }, [uploadIds, onUploadId]);

  const { items, latest, loading, error, reload } = useReconstructions(uploadId);

  const onPickFiles = (e) => {
    const picked = Array.from(e.target.files || []).slice(0, MAX_IMAGES);
    // Revoke any previous previews before replacing.
    setFiles((prev) => {
      prev.forEach((f) => URL.revokeObjectURL(f.previewUrl));
      return picked.map((f) => ({ file: f, previewUrl: URL.createObjectURL(f) }));
    });
    // Clear previously uploaded ids — new selection means a new recon session.
    setUploadIds([]);
    setUploadError(null);
    // Reset the input value so the same file can be picked again if needed.
    e.target.value = "";
  };

  const removeAt = (idx) => {
    setFiles((prev) => {
      const next = prev.slice();
      const removed = next.splice(idx, 1)[0];
      if (removed) URL.revokeObjectURL(removed.previewUrl);
      return next;
    });
    setUploadIds((prev) => prev.filter((_, i) => i !== idx));
  };

  const onUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setUploadError(null);
    const ids = [];
    try {
      // Sequential uploads keep the AI server's normalize queue ordered.
      for (const { file } of files) {
        const r = await uploadsApi.create(file);
        ids.push(r.id);
        try {
          await uploadsApi.triggerNormalize(r.id);
        } catch (e) {
          console.warn("normalize trigger failed:", r.id, e);
        }
      }
      setUploadIds(ids);
    } catch (e) {
      setUploadError(e.message || String(e));
    } finally {
      setUploading(false);
    }
  };

  const onTriggerRecon = async () => {
    if (uploadIds.length === 0) return;
    setTriggering(true);
    setTriggerError(null);
    try {
      const method = uploadIds.length === 1 ? "smpl_fast" : "smpl_multi";
      const image_urls = uploadIds.map((id) => `/uploads/${id}/normalized`);
      await reconstructionsApi.create({
        upload_id: uploadIds[0],
        method,
        image_urls,
      });
      reload();
    } catch (e) {
      setTriggerError(e.message || String(e));
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="panel">
      <h3>人体重建</h3>

      <div className="row">
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={onPickFiles}
        />
        <button onClick={onUpload} disabled={files.length === 0 || uploading}>
          {uploading ? "上传中..." : `上传 (${files.length})`}
        </button>
      </div>

      {files.length > 0 && (
        <div className="thumbs">
          {files.map((f, i) => (
            <div className="thumb" key={f.previewUrl}>
              <img src={f.previewUrl} alt={`img-${i}`} />
              {uploadIds[i] ? (
                <span className="thumb-badge" title={uploadIds[i]}>
                  ✓
                </span>
              ) : null}
              <button
                type="button"
                className="thumb-remove"
                onClick={() => removeAt(i)}
                title="移除"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      {files.length > 0 && files.length < 2 && (
        <p className="muted">提示：选 2–8 张多角度照片可启用多视角重建 (smpl_multi)。</p>
      )}

      {uploadError && <p className="err">上传失败：{uploadError}</p>}

      {uploadIds.length > 0 && (
        <>
          <p className="muted">upload: {uploadIds[0]} ({uploadIds.length} 张)</p>
          <div className="row">
            <button onClick={onTriggerRecon} disabled={triggering}>
              {triggering
                ? "触发中..."
                : `触发重建 (${uploadIds.length === 1 ? "smpl_fast" : "smpl_multi"})`}
            </button>
            <button onClick={reload} disabled={loading}>刷新</button>
          </div>
          {triggerError && <p className="err">触发失败：{triggerError}</p>}
        </>
      )}

      {error && <p className="err">加载失败：{String(error.message || error)}</p>}

      {items.length > 0 && (
        <ul className="list">
          {items.map((r) => {
            const badge = STATUS_BADGE[r.status] || STATUS_BADGE.pending;
            return (
              <li key={r.id} className="item">
                <span>
                  <span className="dot" style={{ background: badge.color }} />
                  <span>
                    <div className="name">{r.method}</div>
                    <div className="meta">
                      {badge.label} · {r.id.slice(-8)}
                    </div>
                  </span>
                </span>
                {r.status === "done" && r.glb_url && (
                  <button
                    className="apply"
                    onClick={() => onPickedGlb(r.glb_url)}
                  >
                    使用
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {latest && latest.status !== "done" && (
        <p className="muted">最新任务：{latest.status}（自适应轮询中）</p>
      )}
    </div>
  );
}
