# FitScan Handoff — 2026-06-16

> 上一位 AI agent 的交接文档。在删记录 / 开新对话后读这个。

---

## 1. 我是谁 / 之前是谁

- **承接方**：MiniMax-M3（Cursor 编码 agent，模型版本见 Cursor 设置）
- **原作者**：在 FitScan 仓库 `c:\FitScan` 上工作的 AI agent（之前完成 Phase A）
- **交接原因**：用户准备清空 Cursor 对话记录，需要把上下文固化到文件里
- **项目根**：`C:\FitScan`（Windows dev machine）

---

## 2. 项目目标（一句话）

3D 虚拟试衣 + 实时人体测量。dev machine 跑 FastAPI monolith + React；GPU inference 跑在 4×RTX 3090 的 AI server 上，通过 HTTP REST + 任务队列（不是微服务）解耦。

---

## 3. 硬约束（违反即返工）

来自 `C:\FitScan\.cursor\rules\GLOBAL-RULES.mdc`：

- **架构 = 单体 FastAPI + React**，禁止微服务 / Celery / Redis / InfluxDB
- **DB = PostgreSQL or SQLite**（dev 用 SQLite，路径在 `backend/fitscan.db`）
- **AI server = 4×RTX 3090 单独机器**（**不是** dev machine，dev machine 无 GPU）
- **3D 单 Canvas**：前端只有一个 `<Canvas>`，在 `frontend/src/core/Scene.jsx`
- **API 分层**：`router` 禁止写业务逻辑，全在 `service`
- **MVP 优先**：能跑 > 完美设计
- **数据模型 4 张表**：users / measurements / clothing_models / tryon_sessions
- **AI 生成必须异步 + 缓存**

---

## 4. 仓库现状（截至交接）

### 4.1 已完成 = Phase A：AI server 队列管道 ✅

| 文件 | 作用 |
|------|------|
| `ai_server/launcher.py` | 父进程：platform check + 4 worker supervisor + GPU breaker (5 restart/10min) |
| `ai_server/worker_process.py` | 子进程：dequeue → mark_running → run → mark_done/FAILED；带 HeartbeatWriter 线程 |
| `ai_server/api.py` | FastAPI 网关：`/health` `/infer/smpl_fast` `/infer/smpl_multi` `/status/{id}` `/result/{id}` |
| `ai_server/queue/task.py` | `Task` dataclass + `TaskStatus` enum + transition guard |
| `ai_server/queue/persistence.py` | SQLite schema (WAL mode) + CRUD：`insert_pending` / `mark_running` / `heartbeat` / `mark_done` / `mark_failed` / `reset_to_pending` |
| `ai_server/queue/inproc_queue.py` | `mp.Queue` 包装 + `SHUTDOWN_EVENT` + `enqueue()` |
| `ai_server/queue/recovery.py` | 启动时从 SQLite 重建 queue |
| `ai_server/queue/watchdog.py` | `HeartbeatWatchdog` 后台线程（API 进程内 30s 扫一次） |
| `tests/sp1_smoke.py` | SP-1 烟测脚本，16/16 PASS |

### 4.2 未完成（按 SPEC.md Phase 排序）

| Phase | 内容 | 任务数 | 状态 |
|-------|------|--------|------|
| **A** | AI server 队列管道 | 15 | ✅ Done, SP-1 verified |
| **B** | dev machine 数据通路（uploads + reconstructions 表 + 路由） | ~9 | ⏳ 下一站 |
| **C** | upload + normalize（异步）| ~6 | pending |
| **D** | Fast path：单图 SMPL 重建（calls AI server） | ~7 | pending |
| **E** | Slow path：多图 SMPLer-X 融合 | ~6 | pending |
| **F** | 试穿：GLB 下载 + 后处理 + 简单物理 | ~8 | pending |
| **G** | 前端 wiring：upload → 3D 展示 → 试穿 UI | ~7 | pending |
| **H** | E2E 烟测 + 收尾 | ~5 | pending |

> 详见 `STATUS.md`（每个 Phase 展开任务列表 + 烟测点）

### 4.3 已有但**可能冲突**的旧文件

- `ai_server/main.py`（旧版 mock，**已被新的 `ai_server/api.py` 替代**，可删）
- `backend/app/api/measurement.py`（D，**已被 `routes/measurements.py` 替代**）
- `backend/app/services/measurement_service.py`（D，**已被 `services/storage.py` 替代**）
- `backend/capture/capture.py`（D，**Phase B 才用，现在保留无害**）

---

## 5. 关键设计决策（不要再争论）

1. **AI server 和 backend 是**两个独立进程**，HTTP REST 通信**。**不是**两个 FastAPI app 共享代码包。
2. **任务队列跨进程用 SQLite 持久化 + mp.Queue 缓冲**。mp.Queue 是**暂存**，SQLite 是 SoT。重启时 `recovery.py` 从 SQLite 重建。
3. **AI server worker 进程和 API 进程隔离**：worker 跑 GPU，API 跑 watchdog + FastAPI，**不会 OOM 互相影响**。
4. **CUDA_VISIBLE_DEVICES=<id>**：每个 worker 只看 1 张卡，独立 CUDA context。
5. **AI server 必须 Linux/WSL2**（Windows 上 launcher 会主动 raise，参见 `launcher._assert_platform`）。**真生产部署在 Linux box**，本机 dev 用模拟模式。
6. **DB schema 极简**：4 张表，**禁止**为了"未来扩展"加字段。YAGNI。

---

## 6. 如何继续

### 6.1 立刻要做

1. 读 `C:\FitScan\STATUS.md`（未完成 Phase 任务清单 + 烟测点）
2. 读 `C:\FitScan\SPEC.md`（特别是 §2 模块规格、§9 Phase 拆分）
3. 读 `C:\FitScan\.cursor\rules\*.mdc`（workspace 规则，5 个文件）

### 6.2 开始 Phase B

按 CLAUDE.md 的强制工作流：

```
你接手后 → 检查点 1：复述用户当前目标（dev machine 数据通路）
         → 检查点 2：方案（schema + service + router 3 文件 + mount）
         → 检查点 3：任务清单 T016-T024
         → 用户确认 → 开始执行
```

**不要**直接开始写代码。**先复述、问用户。**

### 6.3 跑烟测

每个 Phase 完了跑 `python tests/sp<N>_smoke.py`。**当前 SP-1 已通过**。

### 6.4 完整重启 AI server（在 Linux box 上）

```bash
cd /path/to/FitScan
pip install -r ai_server/requirements.txt
python -m ai_server.launcher
# 期望日志：[launcher] schema initialized → recovered 0 tasks → watchdog started
#          → [supervisor] API gateway spawned pid=... → spawned worker gpu=0 ...
```

---

## 7. 容易踩的坑（已知 + 修复历史）

| 坑 | 触发条件 | 修复 |
|---|---------|------|
| `Task.from_row`：`if d["result_json"]` 跳过 `None` 导致 `pop` 漏 | SQL row 的 `result_json` 列 value = NULL | 先 `pop` 再判断，已在 `task.py` 修 |
| `HeartbeatWriter.stop()` 撞 `Thread._stop` 内部方法，`join` 崩 | 继承 Thread 又覆盖 stop | 改名 `request_stop`，已修 |
| Windows 终端 GBK，print unicode 报错 | `print("✓")` | 改 ASCII `[OK]/[FAIL]`，已修 |
| SQLite `_local.conn` 跨进程不复用 | 多进程 / test 干扰 | 用环境变量 `FITSCAN_QUEUE_DB` 切 DB，已实现 |
| `mp.Queue.qsize()` 在 Windows raise | 监控用 | `queue_size()` 内部 try/except，已实现 |

---

## 8. 不想读 SPEC.md 也能看懂的"接口约定"

### 8.1 AI server endpoints (api.py)

```
GET  /health                                  → 队列 + 状态统计
POST /infer/smpl_fast  {upload_id, image_url} → 202 {task_id, status: "PENDING"}
POST /infer/smpl_multi {upload_id, urls[]}    → 202 {task_id, status: "PENDING"}
GET  /status/{task_id}                        → {status: PENDING|RUNNING|DONE|FAILED, ...}
GET  /result/{task_id}                        → {status, result: {...} | null}
```

### 8.2 dev machine backend（待加，Phase B）

```
POST /api/uploads             multipart file → upload_id + url
GET  /api/uploads/{id}                          → 上传详情
GET  /api/uploads                               → 列表
POST /api/reconstructions  {upload_id, method}  → 触发 AI server 重建
GET  /api/reconstructions/{id}                  → 重建结果 (glb_url + metrics)
GET  /api/reconstructions                       → 列表
```

### 8.3 Frontend routes（待加，Phase G）

```
/upload         上传页（拍照/选图）
/reconstruct    3D 预览（自动轮询 status）
/tryon          试穿（GLB + transform controls）
```

---

## 9. 用户偏好记录

来自对话观察（不确定百分百准确，但接班时注意）：

- **喜欢"分阶段 + 阶段汇报 + 跑烟测"的工作流**（用户原话"按 Phase 走，每完成一个 Phase 给汇报 + 跑对应烟测"）
- **接受度高**：3 个选项里 1=A 接受 2=全收 3=按 Phase 走（用户选 3）
- **会反问验证**：会问"你不知道密钥怎么做的"——**不要瞎编**，如实说不知道
- **会要求保留工作**：删记录前要先把代码/进度/对话固化到文件
- **不需要 emoji**（CLAUDE.md 也没要）
- **不需要在代码注释里解释改动**（workspace rule）

---

## 10. 紧急联系 / 上下文出处

- 当前对话时间：2026-06-16 20:30 UTC+8
- Agent transcript: `C:\Users\33965\.cursor\projects\c-FitScan\agent-transcripts\<uuid>.jsonl`（删了就没了，但代码 + git + HANDOFF.md + STATUS.md 才是真源）
- Git 仓库：本地 `C:\FitScan`（注意 git status 里有一堆 `??` 未追踪文件，**没 commit 不算永久**）

---

*最后修改：2026-06-16 20:30 UTC+8 by 前任 AI agent*
