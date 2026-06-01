# Data Model: Virtual Try-On Clothing Overlay

## Entities

### HumanModel

| Field | Type | Description |
|-------|------|-------------|
| id | string | 唯一标识符 |
| modelUrl | string | GLB模型URL路径 |
| scale | number | 模型缩放比例 (相对于标准身高) |
| position | Vector3 | 模型位置 |
| rotation | Quaternion | 模型旋转 |
| bones | Bone[] | 骨骼数组 |
| mesh | SkinnedMesh | 渲染用的蒙皮网格 |

### ClothingModel

| Field | Type | Description |
|-------|------|-------------|
| id | string | 唯一标识符 |
| name | string | 服装名称 |
| modelUrl | string | GLB模型URL或Blob URL |
| fileSize | number | 文件大小(字节) |
| position | Vector3 | 服装位置偏移 |
| rotation | Vector3 | 服装旋转偏移 (Euler) |
| scale | number | 服装缩放 |
| isActive | boolean | 是否当前选中 |
| mesh | SkinnedMesh | 渲染用的蒙皮网格 |

### ClothSimulation

| Field | Type | Description |
|-------|------|-------------|
| id | string | 唯一标识符 |
| clothingId | string | 关联的服装ID |
| vertices | Float32Array | 顶点位置数组 |
| springs | Spring[] | 弹簧连接数组 |
| velocities | Float32Array | 顶点速度数组 |
| forces | Vector3 | 当前受力 (重力+风力) |
| isRunning | boolean | 是否正在运行 |

### SimulationConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| stiffness | number | 0.3 | 布料硬度 (0-1) |
| dampening | number | 0.5 | 阻尼系数 (0-1) |
| gravityPerSecond | Vector3 | (0,-9.8,0) | 重力加速度 |
| windPerSecond | Vector3 | (0,0,0) | 风力向量 |
| subSteps | number | 15 | 每帧模拟步数 |

### UserAdjustment

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| positionOffset | Vector3 | (0,0,0) | 位置偏移 |
| rotationOffset | Vector3 | (0,0,0) | 旋转偏移 (Euler degrees) |
| scale | number | 1.0 | 缩放比例 |

## Relationships

```
HumanModel 1 ──N──> ClothingModel (通过骨骼绑定)
ClothingModel 1 ──1──> ClothSimulation
ClothingModel 1 ──1──> UserAdjustment
```

## State Transitions

### ClothingModel States

| State | Trigger | Next State |
|-------|---------|------------|
| unloaded | 用户上传文件 | loading |
| loading | 文件解析完成 | ready |
| ready | 用户确认应用 | active |
| active | 用户选择其他服装 | ready |
| active | 用户移除服装 | unloaded |

### ClothSimulation States

| State | Trigger | Next State |
|-------|---------|------------|
| idle | 服装未激活 | running |
| running | 服装激活且可见 | paused |
| paused | 用户暂停模拟 | running |
| running | 服装被移除 | idle |
