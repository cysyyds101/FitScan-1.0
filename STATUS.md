# FitScan Status

**更新**：2026-10-21
**本文件只记"现在在哪"。** 规范在 [`docs/FOUNDATION.md`](docs/FOUNDATION.md)，素材实况在 [`assets/CATALOG.md`](../assets/CATALOG.md)。

> 旧版 STATUS.md（2026-06-16）自称 SOURCE OF TRUTH，却把 Phase B 标为 next，而实际已推进到 Phase G，
> 且其 T016–T028 任务清单早已被执行或被 FOUNDATION §11 取代。它已整体作废，历史内容见 commit `dd9349c`
> 之前的版本。**下次不要再在这里维护任务清单。**

---

## 已完成

| Phase | 内容 | 状态 |
|---|---|---|
| A | AI server 队列管道（`ai_server/queue/`） | ✅ SP-1 全绿（queue 曾被误删，2026-10-21 恢复） |
| B–C | dev machine 数据通路 + upload/normalize | ✅ |
| D–E | SMPL 重建管线、多视角路由 | ⚠️ **代码在，结果是 mock**（见下"未完成的真相"） |
| F | 资产注册表 + AvatarEntity + 自适应轮询 | ⚠️ "skeleton-swap" 名不副实，见 FOUNDATION D 表 |
| G | UI 整合（Navbar / ErrorBoundary / 页头） | ✅ |
| — | 实时镜像地基：帧协议、环境、素材台账、启动脚本 | ✅ 2026-10-21 |

## 未完成的真相

三件事必须写在最显眼处，否则会被"7 个 Phase 都绿了"的表象盖住：

1. **项目里没有任何有效 3D 模型**（0 个）。三个 `.glb` 缺 `glTF` 魔数，八个是 `totalLength=0` 的空壳。应用里看到的是程序化兜底几何体。证据：[`assets/CATALOG.md`](../assets/CATALOG.md) §1。
2. **"3D 人体重建"14 行结果全是同一个 648 字节空场景的副本**。`worker_process.py:107` 是 mock。
3. **采集层没有 RGB 流**（`capture.py:184-188` 只开深度，`:254` 的 RGB 是空字节）。实时试衣镜的前提尚未成立。

## 当前阻塞

| ID | 阻塞 | 谁能解 |
|---|---|---|
| G-1 | 无 SMPL/SMPL-X 身体模型（需机构授权，周期以周计） | 你 |
| G-3 | 有效服装 0 件 | 你（采买/打版决策） |
| G-4 | SR300 量程拍不到站立全身；且本次会话未连接 | 你（换相机 or 接受上半身） |
| — | `launcher.py:50-68` 硬禁 Windows，本机起不了真 AI server | 我可改，但需先定 D-D |

## 下一步

不依赖硬件、我现在就能推：T003（回调链）、T004+T005（三端迁移到新帧协议，`--simulate` 可验）、T012（SP-8 烟测）、T017（清 DB 假目录）。

完整依赖排序见 [`docs/FOUNDATION.md`](docs/FOUNDATION.md) §11。
