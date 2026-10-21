# FitScan 地基与范围（FOUNDATION）

**版本**：v1 · 2026-10-21
**地位**：本文件是 FitScan 的**现行规范**。与 `SPEC.md`（system-architecture-v1，2026-06-15）冲突时，以本文件为准；冲突清单见 §10。
**为什么要有这份文件**：`SPEC.md` 写于 6 月，前提已经失效（它假设开发机无 GPU），并且它规定的 8 个文件里有 5 个从未被创建过。继续照它施工只会制造更多漂移。

---

## 1. 产品定义

> 人站在显示屏前，屏幕里是**他自己**，他身上的衣服可以即时更换。现实中人没有换衣服。

这个定义里有三个承诺，它们的难度差了几个数量级，必须分开承诺、分开验收：

| 承诺 | 内容 | 延迟档位 | v1 是否交付 |
|---|---|---|---|
| **P-1 在场感** | 屏幕里看到的是真人，不是卡通替身 | 每帧 ≤16ms | ✅ 交付 |
| **P-2 跟手感** | 我动，衣服跟着动，不脱开、不穿帮 | 每帧 ≤16ms | ✅ 交付（上半身） |
| **P-3 合身** | 这件衣服穿在我这个身材上，尺寸是对的 | 一次性 ≤10s | ⚠️ 降级交付（见 §3 缺口 G-1） |
| ~~P-4 自定义设计~~ | 我画一件衣服，它能穿在身上 | 分钟级 | ❌ **v1 不做**（见 §8） |

**P-3 是整个项目唯一可能做不出来的承诺**，原因在 §3。

---

## 2. 现有材料盘点（硬事实，不含推测）

### 2.1 算力

| 位置 | 实际配置 | 状态 |
|---|---|---|
| 本机 | RTX 5070 **12GB**，驱动 616.64 | ✅ 已验证：torch 2.11.0+cu128，`sm_120` 在 arch list 内，`cuda.is_available()=True` |
| AI 服务器 | 4×RTX 3090（Linux） | ⚠️ `launcher.py:50-68` 硬禁 Windows；本机是 win32，此路当前不通 |

### 2.2 相机

Intel RealSense **SR300**。三个硬限制：

- **量程约 0.4–1.2m**，FOV 约 43°×29° → 1.2m 处横向覆盖不足 1m。**物理上拍不到 1.7m 高的全身。**
- 当前代码**只开深度流，从不开 color 流**（`capture.py:184-188`），RGB 是空字节（`capture.py:254`）。
- 本次会话**未连接**（172 个在位 PnP 设备中，Camera 类零个、`VID_8086` 零个）。

### 2.3 模型资产

| 资产 | 实际内容 | 能做什么 | 不能做什么 |
|---|---|---|---|
| `models/vitpose-plus-huge`（3.4GB） | ViTPose+ Huge 权重 | 2D 关键点估计 | **产出不了网格**；且 Huge 体量在 5070 上做不到实时 30fps |
| `SMPLer-X/`（286MB） | **只有代码，零个权重文件**（无 .pth/.ckpt） | 什么都做不了 | 需要 3 份官方 checkpoint + SMPL 模型 |
| SMPL 身体模型 | **全仓库不存在**（`*.pkl` / `basicModel*` 搜索结果为空） | — | 没有它，任何姿态估计都无法解码成人体网格 |

### 2.4 服装资产 —— 盘出来是零

数据库 `clothing` 表有 **8 行**，看起来像个目录。逐文件哈希+十六进制头核对后：

```
c01  T-Shirt       → clothing_01.glb   ┐ 同一文件
c03  Hoodie        → clothing_01.glb   ┘ ← 假目录项
c02  Vest          → clothing_02.glb
usr-*  ×5          → 12 字节空壳（GLB 头声明 totalLength=0）
```

而 `clothing_01.glb` / `clothing_02.glb` / `human.glb` 这三个"真模型"**开头不是 `glTF` 魔数**，`file(1)` 判为 `data`，three.js 无法解析；且三者**前 16 字节完全相同**。`ai_server/data/fixtures/sample.glb`（648B）是只声明了 asset 2.0 的**空场景**。

**有效 3D 模型：0 个。真实服装：0 件。** 应用里看到的体和衣，全是程序化兜底几何体。完整证据见 [`assets/CATALOG.md`](../assets/CATALOG.md)。

同理，`reconstructions` 表 14 行全部是 `sample.glb` 的字节级副本（`worker_process.py:107` 是 mock）。**"3D 人体重建"没有任何一行是真的。**

---

## 3. 材料缺口（阻塞项，必须先承认）

| ID | 缺口 | 影响 | 补齐成本 |
|---|---|---|---|
| **G-1** | 无 SMPL 身体模型 + 无任何可用的实时人体网格模型 | P-3「合身」无法实现；只能做"把预置 GLB 摆到固定位置" | SMPL/SMPL-X 模型需**机构授权申请**（非下载即用），周期以周计 |
| **G-2** | 无 RGB 流 | P-1「在场感」实现不了，镜子是黑的 | 低——`capture.py` 加 color 流 + align，本仓库内可解 |
| **G-3** | 有效 3D 服装 **0 件**（8 行目录全指向空壳或非 GLB 文件） | 换装无从演示；当前画面是程序化几何体冒充 | 高——每件服装要建模+打版+绑定，是**内容生产**不是写代码 |
| **G-4** | SR300 量程不足以拍全身 | 全身版产品形态不成立 | 高——要么换相机，要么把产品定义收窄到上半身 |

**G-1 和 G-3 是"不能异想天开"的两个硬边界。** 在拿到身体模型授权、以及服装库扩到 10 件以上之前，本项目**不具备**对外宣称"AI 量体裁衣"的材料条件。

---

## 4. 架构

### 4.1 进程拓扑

```
┌──────────────── 本机（RTX 5070）────────────────┐
│                                                 │
│  [MIRROR 进程]  ★新，独立，实时                  │
│    SR300 ──RGB-D 对齐──> 抠像 ──> 姿态/形状 ──>  │
│                     服装形变 ──> 合成 ──> 显示   │
│    约束：每帧 ≤16ms；不碰数据库；不调 REST        │
│                    │ 新帧协议（40B 定长头）       │
│                    ▼                             │
│  [FastAPI 单体] 8000  业务/存储/中继，非实时      │
│                    │                             │
│  [React] 5173 ───┘                               │
└────────────────────┬────────────────────────────┘
                     │ REST（异步任务，秒级~分钟级）
                     ▼
        [AI 服务器 4×3090]  只做离线：重建、服装资产生成、出片
```

**为什么 MIRROR 必须是独立进程**：实时路径上不能出现数据库锁、HTTP 客户端、Python GC 停顿。`SPEC.md §1.1` 的"Monolith FastAPI only"约束的是**业务层**，不是采集进程——该文件本身已把 `capture.py` 列为"standalone process, NO FastAPI import"（§2.1），MIRROR 沿用这个先例。

### 4.2 三层职责

| 层 | 位置 | 延迟 | 负责 | 不负责 |
|---|---|---|---|---|
| **L1 实时** | MIRROR 进程 + GPU | 每帧 ≤16ms | 渲染、骨骼动画、预烘焙形变插值 | ❌ 不做任何拟合计算、❌ 不做布料解算 |
| **L2 拟合** | 本机 GPU，异步 | 1–10s | 人体 shape 估计、服装↔身材绑定、结果落盘 | ❌ 不进每帧路径 |
| **L3 生成** | AI 服务器 / 云 | 秒~分钟 | 扩散试衣出图、服装资产生成 | ❌ 不承担交互 |

**核心设计原则（整个项目最重要的一句话）**：

> **拟合一次，渲染每帧。** 用户"换衣服"走 L2（秒级可接受，因为心理预期就是"切换"）；用户"动身体"走 L1（必须 16ms）。二者的产物之间用一份**预烘焙的形变目标集**（size set / blend shape）连接。

### 4.3 缝合交互（P-1 与 P-3 的调和）

人**动**的时候显示 L1（跟手、质感一般）；人**站住 0.8 秒**后，L3 的生成结果淡入覆盖（都不动了，慢无所谓）。用户感知为"一动就实时跟，一停就变照片"。

这不是取巧，这是在 12GB 显存上达到"Decart 级观感"的唯一可行路径。

### 4.4 端口

| 服务 | 端口 | 协议 |
|---|---|---|
| React dev | 5173 | HTTP |
| FastAPI | 8000 | HTTP / WS |
| MIRROR | 8766 | WS（新帧协议） |
| 旧 capture.py | 8765 | WS（保留给 `/measure`，逐步退役） |
| AI 服务器 | 8080 | HTTP REST |

---

## 5. 目录规范

```
FitScan/
├── docs/
│   ├── FOUNDATION.md        ← 本文件（规范）
│   ├── ASSETS.md            ← 素材台账，唯一可信的资产清单（含 G-1~G-4 状态）
│   └── screenshots/
├── backend/
│   ├── app/                 FastAPI 单体：api/routes + services（业务，非实时）
│   ├── capture/             旧采集进程（/measure 用，待退役）
│   └── mirror/          ★   实时镜像子系统（独立进程，不 import FastAPI）
│       ├── protocol.py         帧协议（已建，40B 定长头）
│       ├── capture_rt.py       RGB-D 对齐采集 + 设备内参
│       ├── pipeline/           每帧阶段：segment / pose / fit / composite
│       ├── latency.py          motion-to-photon 打点
│       └── requirements.txt
├── ai_server/               离线 GPU 推理（queue / launcher / worker_process）
├── frontend/src/
│   ├── core/                Scene.jsx（全局唯一 Canvas）、GLBLoader.js
│   ├── mirror/          ★   镜像前端：protocol.js（已建）、管线调度、页面组件
│   ├── components/ hooks/ pages/ api/
│   └── styles/
├── assets/              ★   统一素材库（取代散落的 public/models 与骗人的 DB 目录）
│   ├── body/                人体 GLB
│   ├── garments/<id>/       每件服装一个目录：glb + 元数据 + 绑定信息
│   └── CATALOG.md           人工维护的真实目录，DB 从这里生成
├── tests/                   spN_smoke.py 约定（section/check/[OK]/[FAIL]/E2E）
└── scripts/                 一次性入口，根目录不放脚本
```

★ = 本次新增或重整。

**根目录清理**（2026-10-21 执行了一半，如实记录）：

已做（都是 tracked 文件，`dd9349c` 可还原）：
- 删 `src/`（只含一个 `downstream-browsers.json.md`）
- 删 `start-dev.sh` 与 `scripts/start_dev.sh`（见下）
- `test_sr300.py` → `scripts/test_sr300.py`
- `_tmp_assets/cdp_shot.mjs` → `scripts/cdp_shot.mjs`（不依赖 puppeteer 的 CDP 截图工具，值得留，从被忽略的目录里救进版本库）

**未做，等你点头**（这些是 gitignored 的，还原点保护不了，删了就是真没了；且 `.workbuddy-ai/memory/2026-10-12.md:53` 记录上次同类删除请求被你拒绝过）：
`.chrome-verify{,2,3,4}/`（合计 100MB Chrome profile）、`_chrome.err`、`_dom.html`、`commit_diff.txt`、`backend_uvicorn.log`、`logs/`（空）、`_tmp_assets/`（已空）。
它们已全部落在 `.gitignore` 内，不会污染提交，只占本地磁盘。

**启动脚本**：`start-dev.sh`（根）与 `scripts/start_dev.sh` **不是重复品**，是两份不同的、且在这台机器上都跑不起来的脚本——前者调 `pip`/`uvicorn`（PATH 上没有），后者调 `conda run -n fitscan-capture`（该环境不存在）。两者已删除，统一为 **`scripts/dev.sh`**，只用绝对解释器路径 `.venv/Scripts/python.exe`。

---

## 6. 复用矩阵

### 6.1 直接复用（已经是对的，别重写）

| 资产 | 位置 | 为什么可信 |
|---|---|---|
| 单 Canvas 约束 | `frontend/src/core/Scene.jsx` | 文件头 Rule 明确禁止子组件自建渲染器，且被遵守 |
| GLB 统一装载 | `core/GLBLoader.js` + `isValidGLB` | 所有 GLB 入口收敛在一处 |
| GLB 归一化/阴影 | `AvatarEntity.jsx:45-71` | `normalizeScaleAndCenter` + `applyShadows` 可直接搬 |
| SQLite 无 ORM 迁移模式 | `backend/app/services/storage.py:30-105` | `CREATE TABLE IF NOT EXISTS` + `PRAGMA table_info` 探测式 ALTER，符合 §1.1 约束 |
| 资产注册表 | `backend/app/services/asset_service.py` | register/lookup/public_url 已经是干净边界 |
| HTTP 客户端封装 | `frontend/src/api/client.js` | `request()` + `ApiError`，统一错误形态 |
| 烟测约定 | `tests/sp1..sp7_smoke.py` | `section()/check()/[OK]/[FAIL]` + 末段 E2E，SP-1 已验证可跑 |
| 帧协议 | `backend/mirror/protocol.py` + `frontend/src/mirror/protocol.js` | 本次新建，双端逐字节验证 |

### 6.2 改造复用（方向对，实现有问题）

| 资产 | 缺陷 | 改造动作 |
|---|---|---|
| `backend/capture/capture.py` | 只有深度流；RGB 是空字节；`SIMULATE` 在模块导入时算死（`:79`），`--simulate` 参数在 `:376` 才设环境变量——**顺序反了** | 拆成 `mirror/capture_rt.py`（实时）+ 保留旧的给 `/measure` |
| `backend/app/services/camera_ws.py` | 开**两条**上游连接（`:73`、`:94`），capture.py 看到两个客户端；`_rgb_client_ids` 按浏览器 socket 的 `id(ws)` 记账，但帧是从 relay socket 发的——**控制与数据不在同一连接上** | 改单连接双向；换用新帧协议 |
| `backend/capture/body_measure.py` | 内参硬编码且错（`:51-58` 写 `hfov=73,vfov=59`，SR300 640×480 实际约 43×29）；每帧 `list(struct.unpack(...))` + `[[False]*w]*h` 掩码 ≈ **30.7 万次 Python 像素循环**，30fps 不可能 | numpy 向量化 + 内参从设备读 |
| `frontend/src/hooks/useCameraStream.js` | `:59` 把整个 ArrayBuffer 当纯 float32 解，不剥 header 前缀 → **每个采样偏移 (len(header)+1)/4 个 float**；`:92` 依赖数组缺 `metadata` → stale closure，宽高永久回落 640/480；WS 地址 `:15` 硬编码 `:8000`，绕过 vite proxy | 按新协议重写，metadata 改 useRef |
| `ClothingOverlay.jsx:117-119` | 服装靠 **group transform** 摆在旁边，不是绑在身体上 → 人一动衣服就留在原地 | 改成绑定到骨骼/网格 |
| `ClothPhysics.jsx:41-44` | `useFrame` 正弦抖动，不是物理 | 改名 `BreathingHint` 或直接删——**别在规范里叫它 physics** |
| `AvatarEntity.jsx:64-71` | `rebindSkeleton` 只塞 `userData.rootBone`，**全仓库无人消费**；Phase F 的"skeleton-swap"名不副实 | 要么真做重定向，要么把这个说法从提交信息里撤掉 |

### 6.3 必须新写（当前为零）

1. **RGB-D 对齐采集**（`mirror/capture_rt.py`）— G-2 的唯一出路
2. **人体抠像阶段** — 把真人从背景切出来，这是"在场感"的实现体
3. **实时姿态 → 身体 shape** — 受 G-1 阻塞，可先用 2D 关键点做占位（ViTPose+ 已有，但需降到能实时的档位）
4. **服装↔身材绑定与 size set 烘焙** — L2 的核心产物
5. **延迟打点与读数**（`mirror/latency.py`）— 没有它，"实时"只是形容词
6. **MirrorPage 管线调度** — 插槽式，每段可单独关
7. **`assets/CATALOG.md` + 生成脚本** — 取代骗人的 DB 目录

---

## 7. 现有实现的缺陷清单（按严重度）

| # | 严重度 | 缺陷 | 位置 |
|---|---|---|---|
| D-1 | 🔴 阻断 | 无 RGB 流，镜子是黑的 | `capture.py:184-188`、`:254` |
| D-2 | 🔴 阻断 | 深度帧协议三端不一致，浏览器每帧错位 | `camera_ws.py:117` ↔ `useCameraStream.js:59` |
| D-3 | 🔴 阻断 | 无身体模型，"重建"14 行全是 mock 副本 | `worker_process.py:107` |
| D-4 | 🔴 阻断 | 相机内参硬编码且数值错误 | `body_measure.py:51-58` |
| D-5 | 🟠 高 | 服装目录造假：c03 与 c01 指向同一 GLB | `clothing` 表 |
| D-6 | 🟠 高 | 服装未绑定身体，人动衣不动 | `ClothingOverlay.jsx:117-119` |
| D-7 | 🟠 高 | relay 开两条上游连接，控制与数据错配 | `camera_ws.py:73,94` |
| D-8 | 🟠 高 | `SmplFastRequest` 未声明 `backend_callback`/`recon_id`，被 Pydantic 静默丢弃 → 回调链断 | `ai_server/api.py` |
| D-9 | 🟡 中 | 每帧 30.7 万次 Python 像素循环，30fps 不可能 | `body_measure.py:249` |
| D-10 | 🟡 中 | `useMeasurement()` 双实例（**本次已修**） | `MeasurementPage.jsx` |
| D-11 | 🟡 中 | `launcher.py` 硬禁 Windows，本机无法起 AI 服务器 | `launcher.py:50-68` |
| D-12 | 🟡 中 | README 声称结果落在 `/ai_storage/recon/{id}/model.glb`，该路径全仓库不存在 | `README.md:22` |
| D-13 | 🟢 低 | `STATUS.md` 停在 2026-06-16 且标 Phase B 为 next，实际已到 G | `STATUS.md:1` |
| D-14 | 🟢 低 | 归一化逻辑两处重复实现 | `AvatarEntity.jsx:45` / `HumanModel.jsx:85` |
| D-15 | 🔴 阻断 | **项目里没有任何有效 3D 模型**：三个"模型"文件缺 `glTF` 魔数且前 16 字节相同，八个是 `totalLength=0` 的空壳 | 见 `assets/CATALOG.md` §1 |
| D-16 | 🟠 高 | `isValidGLB` 只校验 4 字节魔数 → 空壳被判合法、SP-4/SP-5 断言的是文件头而非模型；**本次已修为魔数+版本+totalLength 三项** | `core/GLBLoader.js:34-70` |
| D-17 | 🟢 低 | 两份启动脚本互相冲突且都跑不起来（调 PATH 上不存在的 `pip`/`conda`）；**本次已合并为 `scripts/dev.sh`** | `start-dev.sh`、`scripts/start_dev.sh` |

---

## 8. 行业共有痛点 —— 本项目明确不解决

写下来是为了**将来不被人拿这些问倒**，也为了**自己不顺手去做**。

| 痛点 | 为什么全世界都没解决 | 本项目态度 |
|---|---|---|
| **实时布料解算** | 碰撞检测 + 摩擦 + 自碰撞在消费级 GPU 上做不到稳定 60fps | ❌ 不做。用预烘焙形变 + 顶点动画冒充，并在文档里**明说是冒充** |
| **单目绝对尺度** | 单目 RGB 的米制尺度是病态问题，±5–10cm 是常态 | ❌ 不试图用算法解决。**依赖深度相机**；深度不可用时明确降级为"不承诺尺寸准确" |
| **真实衣服遮挡** | 虚拟衣服贴合身体，真实衣服有体积，投影必然冲突 | ❌ 不用算法解决。**用产品约定解决**：要求紧身打底衣（同实体试衣间） |
| **2D 图 → 可穿 3D 服装** | 缺少打版/缝合/拓扑约束，生成出来的是"像衣服的物体"不是服装 | ❌ v1 不做。这就是 P-4 被砍的根本原因 |
| **松量与版型偏好** | 同一个三围，不同人想要的合身度不同，这是数据问题不是算法问题 | ❌ 不做推荐算法。只报数字，不替用户判断"合不合身" |
| **镜面视差 / 半反半透光损** | 光学几何限制，算法补不了 | ❌ 不做光学补偿。治具设计上规避（相机贴近屏幕中心） |

**范围红线（一句话版）**：v1 = **上半身 + 深度定尺度 + 预烘焙形变 + 站定后出图**。超出这个范围的功能，一律先写进 §8 讨论，不许直接开工。

**并且要说清楚**：服装资产（≥10 件带绑定的真 GLB）是 v1 的**前置条件**，不是 v1 的**成果**。当前是 0 件（D-15），所以 v1 的实际开工闸门在 §11 的 D-B，不在代码里。

---

## 9. 可测的成功判据

替代 `SPEC.md §6`（那 8 条里没有一条涉及实时性，SC-03 只要求"深度流到浏览器 30fps"）。

| ID | 判据 | 目标 | 怎么测 |
|---|---|---|---|
| F-01 | 屏幕里能看到 RGB 真人画面 | 30fps 连续 60s 不掉帧 | MIRROR 自检日志 |
| F-02 | motion-to-photon 延迟 | ≤120ms（可用）/ ≤60ms（好） | 手机慢动作拍屏，帧计数 |
| F-03 | 深度帧协议正确性 | 合成向量双端逐字节一致 | `tests/sp8_smoke.py` |
| F-04 | 身体轮廓 vs mesh 投影轮廓 | 肩宽/胸围误差 <2cm | 标定板 + 叠图 |
| F-05 | 转身穿帮 | 转身 180°，衣服不脱开身体、不穿透 | 人工录像逐帧看 |
| F-06 | 换装响应 | 点击到衣服上身 ≤3s | 前端计时 |
| F-07 | 回归 | SP-1~SP-8 全绿 | CI / 本地脚本 |

**F-02 和 F-04 是产品成立与否的分水岭。** 任一不达标，路线 C 需要重新评估。

---

## 10. 与 SPEC.md 的冲突（需你拍板）

| # | SPEC.md 原文 | 冲突 | 建议 |
|---|---|---|---|
| C-1 | §1.1「**No GPU on dev machine** — All AI inference must run on AI server」 | 本机有 RTX 5070 且已验证可用；路线 C **要求**本地推理 | **删除该硬约束**，改为「实时推理在本机 MIRROR 进程；离线推理在 AI 服务器」 |
| C-2 | §2.1「Outputs raw depth frame as binary (**no JSON overhead**)」+ §3.1「binary 640×480×4 float32」 | 纯 payload 无法携带时间戳、无法复用同一条流传 RGB | 改为「40 字节定长二进制头 + payload」（即已实现的协议） |
| C-3 | §2.1 要求 `backend/capture/depth_streamer.py` | 从未创建 | 随 G-2 一并落到 `mirror/capture_rt.py`，撤掉该要求 |
| C-4 | §2.3 要求 `core/DepthRenderer.jsx`、`components/MeasurementOverlay.jsx` | 从未创建 | DepthRenderer 撤掉（深度可视化走 2D canvas 已够）；MeasurementOverlay 并入镜像管线 |
| C-5 | §2.4 要求 `ai_server/models/*`、`inference/run.py` | 实际是 `queue/`+`launcher.py`+`worker_process.py`+`api.py` | 按实际改写 §2.4 |
| C-6 | §5.1 要求 `backend/.env` | 全仓库**没有任何 .env 加载器**，配置是 `os.getenv` 在 import 时读死 | 要么引入加载器，要么在规范里承认现状 |
| C-7 | §9 Phase 2–5 全部未勾选 | 实际 Phase A–G 已提交 | 用 §9 的新判据取代 |
| C-8 | §7 风险表 | 未覆盖 G-1~G-4 中任何一项 | 补入 |

---

## 11. 下一步（按依赖排序）

```
已完成（2026-10-21）
  T001  恢复 ai_server/queue/，SP-1 全绿
  T002  capture/requirements.txt 补 numpy + opencv
  T006  MeasurementPage useMeasurement 单例化
  T008  新帧协议（40B 定长头），双端逐字节验证
  T013  assets/CATALOG.md 素材台账 —— 盘出有效 3D 模型为 0（D-15）
  T014  根目录清理 + scripts/dev.sh 统一入口 + isValidGLB 补长度校验（D-16/D-17）
  —     .venv 环境建立、依赖钉死、踩坑写进 scripts/setup_mirror_env.sh
  —     还原点 commit dd9349c

立即可做（不依赖硬件）
  T003  修 SmplFastRequest 缺字段，接回回调链        ai_server/api.py
  T004  三端迁移到新帧协议（--simulate 可验证）      capture.py / camera_ws.py / useCameraStream.js
  T005  随 T004 一并解决 stale closure
  T012  tests/sp8_smoke.py（协议 + 合成帧往返）
  T017  清 DB 假目录（c03 重复项 + 8 个空壳行），改为从 CATALOG.md 生成

插上 SR300 之后
  T007  RGB-D 对齐采集 + 设备真实内参                mirror/capture_rt.py
  T009  body_measure 向量化                          backend/capture/body_measure.py
  T010  motion-to-photon 打点                        mirror/latency.py
  T015  F-02 / F-04 实测，出数字

需要外部决策（不是写代码能解决的）
  D-A   申请 SMPL / SMPL-X 模型授权（解 G-1）        ← 周期以周计，越早越好
  D-B   服装 3D 资产从哪来：买 / 打版 / 开源库 / 改走 2D 试衣（解 G-3）
        ★ v1 的真闸门。当前 0 件，代码写到天黑也没有衣服可试。
  D-C   换相机 或 正式接受"只做上半身"（解 G-4）
  D-D   §10 的 8 条 SPEC 冲突逐条拍板
```

**D-A 到 D-C 是本项目当前真正的瓶颈。** 代码层面我能继续推，但两件事不写代码就没有：P-3「合身」在拿到身体模型授权之前做不出来（G-1），换装在有效服装为 0 件之前无从演示（G-3）。
