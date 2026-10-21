# FitScan 素材台账（ASSETS）

**这是唯一可信的资产清单。** 数据库 `clothing` 表、README、STATUS 都不可信——理由见下。
**核对时间**：2026-10-21 · 方法：逐文件 md5 + 十六进制头 + `file(1)` 类型判定
**关联**：`docs/FOUNDATION.md` §2.3、§2.4、§3、§7

---

## 0. 一句话结论

> **本项目当前拥有的有效 3D 模型数量：0。**
> 应用里看到的"人体"和"衣服"，全部是 `ClothingOverlay.jsx` / `HumanModel.jsx` 的**程序化兜底几何体**（圆柱、立方体拼的），不是加载出来的模型。

这不是"素材少"，是**素材根本不存在**。任何基于"我们有 3D 服装库"的方案都不成立。

---

## 1. 被当作模型资产提交的文件，实际是什么

| 文件 | 大小 | 头 4 字节 | 是 GLB 吗 | 真相 |
|---|---|---|---|---|
| `frontend/public/models/human.glb` | 83,764 | `75ab5a9a` | ❌ | 非 GLB 容器 |
| `frontend/public/models/clothing_01.glb` | 18,828 | `75ab5a9a` | ❌ | 非 GLB 容器 |
| `frontend/public/models/clothing_02.glb` | 31,360 | `75ab5a9a` | ❌ | 非 GLB 容器 |
| `ai_server/data/fixtures/sample.glb` | 648 | `glTF` | ✅ | **空场景**，只有 JSON 块声明 asset 2.0，无 mesh |
| `backend/data/clothing/*.glb` ×4 | 各 12 | `glTF` | ⚠️ | 头部声明 `totalLength=0`，**零内容** |
| `backend/data/uploads/clothing/*.glb` ×3 | 各 12 | `glTF` | ⚠️ | 同上，零内容 |
| `data/uploads/clothing/test_smoke.glb` | 12 | `glTF` | ⚠️ | 同上，零内容 |

三条关键证据：

1. **三个"真模型"的开头不是 `glTF` 魔数**（GLB 规范强制要求），`file(1)` 判为 `data`。三.js `GLTFLoader` 无法解析。
2. **这三个文件前 16 字节完全相同**（`75ab5a9a875e97f825b5ff9b8a76abc9`）——它们不是三个独立模型，是同一个头拼了不同的体。
3. **那 8 个 12 字节文件是合法的 GLB 头 + 声明长度为 0**，即"我是一个 12 字节的 GLB，里面什么都没有"。

> 来源未确认。`create-human-model.js`（已在 WIP commit 中删除）用 `THREE.GLTFExporter` 导出，其输出必然以 `glTF` 开头，所以这三个文件**不是**它的产物。它们是怎么进来的，需要你回忆或查更早的历史。

---

## 2. 数据库在骗人

`backend/fitscan.db` 的 `clothing` 表有 8 行，实际指向的文件：

```
c01  T-Shirt        → clothing_01.glb   ┐
c03  Hoodie         → clothing_01.glb   ┘ 同一文件，Hoodie 是假目录项
c02  Vest           → clothing_02.glb
usr-55ecf66a6ad5   Test Jacket          → 12B 空壳
usr-119f3fb7bdaf   H1 Smoke Jacket      → 12B 空壳
usr-a9335532a9b8   H1 Smoke Jacket v2   → 12B 空壳
usr-f57b524539af   Spec Jacket          → 12B 空壳
usr-eb313227b4bb   Spec Jacket          → 12B 空壳
```

**真实服装：0 件。** 有效 GLB 容器：0 个。表里 8 行，没有一行指向一个能被渲染的服装。

`reconstructions` 表 14 行，全部是 `sample.glb`（648B 空场景）的字节级副本 —— `worker_process.py:107` 是 mock。**真实重建结果：0 个。**

---

## 3. 为什么之前没人发现

`frontend/src/core/GLBLoader.js:44-46` 的 `isValidGLB` **只检查 4 字节魔数**：

```js
const magic = String.fromCharCode(view[0], view[1], view[2], view[3]);
const ok = magic === 'glTF';
```

- 三个假模型魔数不对 → 被拒 → 静默走程序化兜底 → **看起来"能跑"**
- 八个空壳魔数正确 → 被判"合法" → **SP-4 / SP-5 的 E2E 断言因此通过**

也就是说：校验闸门给出了假信心，烟测断言的是文件头而不是模型。

**已修**（2026-10-21）：`isValidGLB` 现在校验魔数 + 版本 + `totalLength === 实际字节数`。实测：三个假模型 REJECT，八个空壳 REJECT，`sample.glb` PASS（但它是空场景，长度校验测不出来）。

---

## 4. 其它模型资产

| 资产 | 路径 | 状态 | 能做什么 |
|---|---|---|---|
| ViTPose+ Huge | `models/vitpose-plus-huge/`（3.4GB） | ✅ 权重齐全 | 2D 关键点估计。**产出不了网格**；Huge 档在 5070 上做不到实时 30fps |
| SMPLer-X | `SMPLer-X/`（286MB） | ❌ **只有代码，零个权重**（无 .pth/.ckpt） | 什么都做不了 |
| SMPL / SMPL-X 身体模型 | 全仓库 | ❌ **不存在**（`*.pkl` / `basicModel*` 搜索为空） | 没有它，任何姿态估计都无法解码成人体网格 |

**这三条合起来就是 `FOUNDATION.md` 的缺口 G-1。** 需要机构授权申请，周期以周计。

---

## 5. 采集设备

| 设备 | 状态 | 硬限制 |
|---|---|---|
| Intel RealSense SR300 | 本次会话**未连接**（172 个在位 PnP 设备中 Camera 类 0 个、`VID_8086` 0 个） | 量程约 0.4–1.2m、FOV 约 43°×29° → **拍不到站立的人的全身** |
| 当前代码 | 只开深度流，**从不开 color 流**（`capture.py:184-188`）；RGB 是空字节（`capture.py:254`） | 镜子是黑的 |

---

## 6. 算力

| 位置 | 配置 | 验证状态 |
|---|---|---|
| 本机 | RTX 5070 **12GB** | ✅ torch 2.11.0+cu128、`sm_120` 在 arch list、`cuda.is_available()=True` |
| AI 服务器 | 4×RTX 3090 | ⚠️ `launcher.py:50-68` 硬禁 Windows，本机起不来 |

12GB 的实际含义：抠像 + 姿态 + 渲染同卡可跑，但**放不下 SMPLer-X 级别的大模型**。

---

## 7. 缺口汇总与补齐路径

| ID | 缺什么 | 补齐方式 | 谁来补 |
|---|---|---|---|
| **G-1** | 身体模型（SMPL/SMPL-X）+ 可用的实时人体网格模型 | 官方授权申请；周期以周计 | **你**（需要机构/邮箱资质） |
| **G-2** | RGB 流 | 本仓库内可解：`capture.py` 加 color 流 + `rs.align` | 我（T007） |
| **G-3** | 服装 3D 资产 ≥10 件，且带绑定 | 买 / 用 CLO3D 打版 / 找开源服装库 / 或改走 2D 试衣 | **你**（内容采买决策） |
| **G-4** | 能拍全身的深度相机 | 换 D435/D455 或 LiDAR；或正式接受"只做上半身" | **你** |

**在 G-1 和 G-3 补齐之前，本项目不具备对外宣称"AI 量体裁衣"或"3D 虚拟试衣"的材料条件。** 能宣称的是：实时 RGB-D 采集 + 人体测量 + 程序化服装占位演示。

---

## 8. 本目录的维护规则

`assets/` 是素材的**唯一入口**，`assets/CATALOG.md`（本文件）是它的账本。

```
assets/
├── CATALOG.md          ← 本文件
├── body/               人体模型
└── garments/<id>/      每件服装一个目录：
                        model.glb + meta.json（版本、来源、授权、绑定信息）
```

**入库规矩**（每条都对应本次发现的一个问题）：

1. 任何 `.glb` 入库前必须过 `validateGLBBuffer`——**魔数、版本、totalLength 三项都要对**。
2. 必须人工在 three.js 里**真的渲染出来看一眼**，长度校验通过的空场景仍算无效。
3. 目录表（DB `clothing`）由 `assets/CATALOG.md` 生成，**不允许手工往 DB 里加行**。
4. 每个服装目录必须有 `meta.json` 说明**来源与授权**，否则不许商用。

> 目前 `assets/` 是空的——因为没有任何资产值得搬进来。等 G-1/G-3 有进展再填。
