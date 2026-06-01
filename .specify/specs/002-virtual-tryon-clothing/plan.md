# Implementation Plan: Virtual Try-On Clothing Overlay with Cloth Physics

**Branch**: `002-virtual-tryon-clothing` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-virtual-tryon-clothing/spec.md`

## Summary

实现一个3D虚拟换衣系统，允许用户上传服装GLB模型并叠加到人体模型上，通过布料物理模拟实现真实的服装飘动和重力效果。核心功能包括：3D人体模型展示、服装上传与叠加、服装位置旋转调整、布料物理模拟。

## Technical Context

**Language/Version**: JavaScript/TypeScript (ES2022+)

**Primary Dependencies**:
- Three.js 0.162.0 (已有)
- @react-three/fiber 8.18.0 (已有)
- @react-three/drei 9.122.0 (已有)
- three-simplecloth (新增 - 布料物理)

**Storage**: N/A (前端仅需客户端存储)

**Testing**: 手动功能测试 + 性能基准测试

**Target Platform**: Web浏览器 (Chrome/Firefox/Safari/Edge 最新版本)

**Project Type**: Web前端功能模块

**Performance Goals**: 布料模拟 ≥30 FPS，模型加载 <3秒

**Constraints**: 浏览器需支持WebGL 2.0，服装文件 ≤10MB

**Scale/Scope**: 单用户本地操作，无服务端依赖

## Constitution Check

*无宪法违规。项目为前端功能扩展，使用现有技术栈。*

## Project Structure

### Documentation (this feature)

```text
.specify/specs/002-virtual-tryon-clothing/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Technical research (integrated)
├── data-model.md        # Entity definitions
├── quickstart.md        # Quick start guide
└── tasks.md             # Task list (/speckit-tasks output)
```

### Source Code (repository root)

```text
frontend/src/
├── components/
│   ├── ModelViewer3D.jsx      # 现有 - 3D查看器
│   ├── HumanModel.jsx         # 新增 - 人体模型组件
│   ├── ClothingOverlay.jsx    # 新增 - 服装叠加组件
│   ├── ClothPhysics.jsx       # 新增 - 布料物理组件
│   ├── ClothingControls.jsx    # 新增 - 服装控制面板
│   └── VirtualTryOn.jsx       # 新增 - 虚拟换衣主容器
├── pages/
│   └── VirtualTryOnPage.jsx   # 新增 - 换衣页面
└── utils/
    ├── glbLoader.js           # 新增 - GLB加载工具

public/
└── models/
    └── human.glb              # 新增 - 人体模型文件
```

### Structure Decision

扩展现有 `frontend/src/components/` 目录，新增以下组件：
- `HumanModel.jsx` - 替换现有几何体为真实GLB人体模型
- `ClothingOverlay.jsx` - 服装加载和叠加逻辑
- `ClothPhysics.jsx` - three-simplecloth 布料模拟封装
- `ClothingControls.jsx` - UI控制面板（滑块）
- `VirtualTryOn.jsx` - 整合所有子组件的容器

## Complexity Tracking

无复杂度违规。

## Technical Decisions

### Decision 1: 布料物理库选择

| 选项 | 优点 | 缺点 |
|------|------|------|
| **three-simplecloth** (选中) | WebGPU加速、与Three.js深度集成、支持骨骼蒙皮 | 需要WebGPU支持 |
| three.js官方compute shader示例 | 原生支持 | 代码复杂，需自行适配 |
| Cannon.js/Rapier3D | 成熟稳定 | 不适合布料模拟 |

**Rationale**: three-simplecloth 提供开箱即用的解决方案，与现有Three.js生态完美集成，支持GPU加速计算。

### Decision 2: 人体模型格式

| 选项 | 优点 | 缺点 |
|------|------|------|
| **GLB (glTF二进制)** (选中) | 高压缩、广泛支持、包含材质和骨骼 |
| FBX | 通用但需转换 | 文件更大 |
| OBJ | 简单 | 无骨骼和动画 |

**Rationale**: GLB是Web 3D的标准格式，与Three.js生态系统无缝对接。

### Decision 3: 服装叠加方案

| 选项 | 优点 | 缺点 |
|------|------|------|
| **骨骼蒙皮权重** (选中) | 服装随人体变形、自然贴合 |
| 顶点匹配 | 精确 | 需要预先处理服装 |
| 位置绑定 | 简单 | 变形不自然 |

**Rationale**: 使用骨骼蒙皮权重可以让服装自然地跟随人体姿态变化，适合虚拟试衣场景。

## Integration Points

### 入口点
- 新增路由 `/virtual-tryon` 指向 `VirtualTryOnPage.jsx`
- 可从导航栏 "虚拟换衣" 按钮进入

### 依赖项
- `three-simplecloth` npm包
- 免费人体GLB模型 (CGTrader/Sketchfab)

## Risks & Mitigations

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 浏览器不支持WebGPU | 中 | 降级到WebGL布料模拟或简化物理效果 |
| GLB模型格式不兼容 | 高 | 提供多种格式支持，显示友好错误 |
| 布料性能不足 | 中 | 降低布料顶点数，限制模拟区域 |
| 服装定位不准 | 中 | 提供详细的手动调整控制 |

## Milestones

| 里程碑 | 完成标准 | 预计时间 |
|--------|----------|----------|
| M1: 基础人体 | GLB模型成功加载并显示 | Day 2 |
| M2: 服装叠加 | 用户可上传并看到服装在人体上 | Day 5 |
| M3: 布料效果 | 服装有风吹/重力物理效果 | Day 8 |
| M4: 功能完善 | 控制面板完整，交互流畅 | Day 10 |
