# FitScan Status — 2026-06-16

> 当前进度 + 后续 Phase 任务清单。**这是 SOURCE OF TRUTH**。每次开工前先读。

---

## 进度总览

```
[A] AI server 队列管道              ████████████ 100%  ✅ SP-1 verified
[B] dev machine 数据通路             ░░░░░░░░░░░░   0%  ← next
[C] upload + normalize (异步)        ░░░░░░░░░░░░   0%
[D] Fast path: 单图 SMPL 重建         ░░░░░░░░░░░░   0%
[E] Slow path: 多图 SMPLer-X 融合    ░░░░░░░░░░░░   0%
[F] 试穿: GLB + 后处理 + 简单物理    ░░░░░░░░░░░░   0%
[G] 前端 wiring                     ░░░░░░░░░░░░   0%
[H] E2E 烟测 + 收尾                  ░░░░░░░░░░░░   0%
```

---

## Phase A ✅ Done（15 任务）

详见 `ai_server/queue/` + `ai_server/launcher.py` + `ai_server/worker_process.py` + `ai_server/api.py` + `tests/sp1_smoke.py`

- T001-T015：全部完成
- SP-1：16/16 PASS（`python tests/sp1_smoke.py`）

---

## Phase B ⏳ Next — dev machine 数据通路

**目标**：让 dev machine 上 FastAPI backend 能存"用户上传的图片"和"AI server 返回的重建结果"。**不**调 AI server，**不**碰前端。

### 任务清单（计划）

```
T016 [P] 加 uploads 表 (id, path, mime, size, created_at, user_id) 到 storage.py
T017 [P] 加 reconstructions 表 (id, upload_id, method, glb_path, metrics_json, status, ai_task_id, created_at)
T018 [P] services/upload_storage.py: save_file_to_disk + insert + get + list
T019 [P] services/recon_storage.py: create + update_status + get + list
T020 [P] schemas.py: UploadItem, UploadCreate, ReconstructionItem, ReconstructionCreate
T021   api/routes/uploads.py: POST /api/uploads (multipart), GET /api/uploads/{id}, GET /api/uploads
T022   api/routes/reconstructions.py: POST/GET/LIST
T023   挂到 backend/app/main.py (include_router)
T024   Pydantic 配置 + CORS 验证 + 错误处理
SP-2 烟测: curl POST 一张测试图 → DB uploads 有记录 + 文件落地到 disk
```

### SP-2 烟测脚本结构

`tests/sp2_smoke.py`：直接调 service 层 + 用 `TestClient` 走 HTTP 路由

```python
# 期望输出
=== 1. uploads table schema ===        [OK]
=== 2. upload_storage CRUD ===          [OK]
=== 3. recon_storage CRUD ===            [OK]
=== 4. POST /api/uploads multipart ===   [OK]
=== 5. GET /api/uploads/{id} ===         [OK]
=== 6. POST /api/reconstructions ===     [OK]
=== 7. E2E: upload + reconstruction ===  [OK]
[OK]  SP-2 PASSED
```

---

## Phase C ⏳ — upload + normalize (异步)

**目标**：uploaded image → 调 AI server 拿 normalized body crop → 存本地。

**依赖**：Phase A (AI server) + Phase B (uploads 表)

### 任务清单（计划）

```
T025 [P] ai_server/api.py 加 POST /infer/normalize {upload_id, image_url}
T026 [P] worker_process.py 加 normalize handler (mock for now)
T027   backend/services/ai_client.py: client.normalize(upload_id, image_url)
T028   backend/services/normalize_service.py: orchestrate
T029   api/routes/uploads.py: POST /api/uploads/{id}/normalize 触发
T030   GET /api/uploads/{id}/normalized  查结果
SP-3 烟测: upload 一张图 → POST normalize → 等 status=done → 拿到 normalized crop path
```

---

## Phase D ⏳ — Fast path: 单图 SMPL 重建

**目标**：normalized body crop → AI server (worker role='fast') → SMPL parameters → 重建 GLB。

### 任务清单（计划）

```
T031 [P] ai_server/api.py: /infer/smpl_fast 已存在，验证 worker 端实现
T032 [P] worker_process.py: 替换 mock run_task 为真 SMPL 推理 (PyTorch)
T033   backend/api/routes/reconstructions.py: POST /api/reconstructions 触发 smpl_fast
T034   backend/services/recon_service.py: orchestrate
T035   GET /api/reconstructions/{id} 加 glb_url 字段
T036   前端: 把 status polling 接到 /reconstruct 页
T037   GLB 文件落地到 backend/frontend/public/models/
SP-4 烟测: 上传图 → 触发 smpl_fast → 拿到 GLB → 前端 <Canvas> 渲染
```

---

## Phase E ⏳ — Slow path: 多图 SMPLer-X 融合

**目标**：多张图 → SMPLer-X 多视角融合 → 更准的 GLB。

### 任务清单（计划）

```
T038 [P] ai_server/api.py: /infer/smpl_multi 已存在
T039 [P] worker_process.py: 替换 mock 为 SMPLer-X (PyTorch3D)
T040   backend/api/routes/reconstructions.py: POST /api/reconstructions {method: 'multi', image_urls: [...]}
T041   backend/services/recon_service.py: 分发 fast/multi
T042   GET /api/reconstructions 加 method 字段过滤
SP-5 烟测: 上传 3 张同人多角度图 → 触发 smpl_multi → 拿到比 smpl_fast 更高质量的 GLB
```

---

## Phase F ⏳ — 试穿: GLB + 后处理 + 简单物理

**目标**：把 GLB 套到人体模型上 + 简单 transform 控件 + 伪布料效果。

### 任务清单（计划）

```
T043 [P] frontend/src/core/GLBLoader.js: 统一加载 + 缓存
T044 [P] frontend/src/components/ClothingOverlay.jsx: 挂载到 HumanModel group
T045 [P] frontend/src/components/ClothPhysics.jsx: vertex offset (breathing)
T046   frontend/src/components/ClothingControls.jsx: position/rotation/scale sliders
T047   frontend/src/components/VirtualTryOn.jsx: 容器
T048   frontend/src/pages/VirtualTryOnPage.jsx: 页
T049   frontend/src/hooks/useTryOnState.js: 状态管理
SP-6 烟测: 选 1 件衣服 → 加载 GLB → 拖动滑块 → 截图对比初始 vs 调整后
```

---

## Phase G ⏳ — 前端 wiring

**目标**：把所有后端 API 接到前端 UI。

### 任务清单（计划）

```
T050 [P] frontend/src/hooks/useUploads.js: 调 /api/uploads
T051 [P] frontend/src/hooks/useReconstructions.js: 调 /api/reconstructions
T052 [P] frontend/src/hooks/useAIInference.js: 调 AI server
T053   frontend/src/pages/UploadPage.jsx: 拍照 / 选图
T054   frontend/src/pages/ReconstructPage.jsx: 3D 预览 + status polling
T055   frontend/src/App.jsx: 路由
T056   frontend/src/pages/TryOnPage.jsx (在 Phase F 写, 这里 wire 状态)
SP-7 烟测: 用户视角: 上传 → 重建 → 试穿 一条龙
```

---

## Phase H ⏳ — E2E 烟测 + 收尾

```
T057   docs/QUICKSTART.md: 完整跑通步骤
T058   docs/DEPLOYMENT.md: AI server Linux 部署
T059   .env.example: 全环境变量清单
T060   README.md 更新
SP-8  端到端烟测脚本: upload 1 张图 → 重建 → 试穿 → 截图
```

---

## 烟测累计

| ID | Phase | 状态 |
|----|-------|------|
| SP-1 | A | ✅ 16/16 |
| SP-2 | B | ⏳ |
| SP-3 | C | ⏳ |
| SP-4 | D | ⏳ |
| SP-5 | E | ⏳ |
| SP-6 | F | ⏳ |
| SP-7 | G | ⏳ |
| SP-8 | H | ⏳ |

每次跑：`python tests/sp<N>_smoke.py`

---

## 文件清单（速查）

### 已写（commit 候选）

```
HANDOFF.md                        ← 接班用
STATUS.md                         ← 本文件
ai_server/launcher.py             ← AI server 入口（Linux only）
ai_server/worker_process.py       ← GPU worker
ai_server/api.py                  ← AI server HTTP API
ai_server/queue/__init__.py
ai_server/queue/task.py
ai_server/queue/persistence.py
ai_server/queue/inproc_queue.py
ai_server/queue/recovery.py
ai_server/queue/watchdog.py
tests/sp1_smoke.py                ← 通过
SPEC.md                           ← 已有
ai_server/main.py                 ← 旧版 mock（可删）
ai_server/requirements.txt        ← 已有
```

### 待写（Phase B+）

```
backend/app/services/upload_storage.py    ← T018
backend/app/services/recon_storage.py     ← T019
backend/app/api/routes/uploads.py         ← T021
backend/app/api/routes/reconstructions.py ← T022
tests/sp2_smoke.py                        ← T024
... （详见各 Phase）
```

---

*最后更新：2026-06-16 20:30 UTC+8*
