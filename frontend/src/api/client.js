// API client. Thin wrapper over fetch with base URL + JSON helpers.
// Backend base URL is read from Vite env (VITE_API_BASE) or defaults to
// the dev proxy path that Vite rewrites /api -> http://localhost:8000.

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function request(path, opts = {}) {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, detail || res.statusText);
  }
  // 204 / empty body
  if (res.status === 204) return null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return res.json();
  return res.text();
}

export class ApiError extends Error {
  constructor(status, detail) {
    super(`API ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

// ─── Clothing ───────────────────────────────────────────────────────────────

export const clothingApi = {
  list: () => request(`/clothing`),
  get: (id) => request(`/clothing/${id}`),
};

// ─── Uploads ────────────────────────────────────────────────────────────────

export const uploadsApi = {
  create: (file, { userId } = {}) => {
    const fd = new FormData();
    fd.append("file", file);
    if (userId) fd.append("user_id", userId);
    return fetch(`${BASE}/uploads`, { method: "POST", body: fd }).then((r) => {
      if (!r.ok) throw new ApiError(r.status, r.statusText);
      return r.json();
    });
  },
  get: (id) => request(`/uploads/${id}`),
  list: (limit = 20) => request(`/uploads?limit=${limit}`),
  triggerNormalize: (id) =>
    request(`/uploads/${id}/normalize`, { method: "POST" }),
  getNormalized: (id) => request(`/uploads/${id}/normalized`),
};

// ─── Reconstructions ────────────────────────────────────────────────────────

export const reconstructionsApi = {
  create: (data) =>
    request(`/reconstructions`, { method: "POST", body: JSON.stringify(data) }),
  get: (id) => request(`/reconstructions/${id}`),
  list: ({ limit = 20, uploadId } = {}) => {
    const qs = new URLSearchParams();
    qs.set("limit", String(limit));
    if (uploadId) qs.set("upload_id", uploadId);
    return request(`/reconstructions?${qs}`);
  },
  trigger: (id) =>
    request(`/reconstructions/${id}/trigger`, { method: "POST" }),
};

// ─── Try-on Sessions ─────────────────────────────────────────────────────────

export const tryonSessionsApi = {
  create: (data) =>
    request(`/tryon_sessions`, { method: "POST", body: JSON.stringify(data) }),
  list: (limit = 20) =>
    request(`/tryon_sessions?limit=${limit}`),
};

export default {
  clothing: clothingApi,
  uploads: uploadsApi,
  reconstructions: reconstructionsApi,
  tryonSessions: tryonSessionsApi,
};
