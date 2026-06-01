# Research: Virtual Try-On Clothing Overlay

## Research Summary

本功能基于网络搜索和技术分析，汇总以下技术方案：

## Decision 1: Cloth Physics Library

### three-simplecloth (选中)

**来源**: [bandinopla/three-simplecloth](https://github.com/bandinopla/three-simplecloth)

**特点**:
- Three.js WebGPU模块
- 将骨骼网格的顶点绘制部分转换为布料模拟
- 支持球形碰撞体
- 支持"磁铁"抓取交互
- GPU加速计算

**集成方式**:
```typescript
import { SimpleCloth } from "three-simplecloth";

const cloth = SimpleCloth.onSkinnedMesh(
  clothingMesh,
  renderer,
  {
    stiffness: 0.3,
    dampening: 0.5,
    windPerSecond: new Vector3(1, 0, 0),
    gravityPerSecond: new Vector3(0, -9.8, 0),
    collidersRoot: humanModel,
  }
);

useFrame((state, delta) => {
  cloth.update(delta);
});
```

### 备选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| three.js compute shader示例 | 原生、官方维护 | 需要自行适配 |
| Cannon.js | 成熟 | 不适合布料 |
| Ammo.js | 物理引擎 | 体积大 |

## Decision 2: Human Model Sources

### 免费资源

| 来源 | 模型 | 格式 | 许可 |
|------|------|------|------|
| CGTrader | 真实女性人体 | GLB (32.8MB) | 免费商用 |
| Sketchfab | 男女基础网格 | GLB | CC Attribution |
| Ready Player Me | 官方模板 | GLB | 免费商用 |

### 下载建议
- 优先选择 glTF 2.0 格式
- 确保包含骨骼绑定 (Skeleton)
- TPose 姿势便于初始定位

## Decision 3: GLB Loading

### Three.js GLB Loader

```typescript
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
loader.load(
  '/models/human.glb',
  (gltf) => {
    const model = gltf.scene;
    // 处理模型...
  },
  undefined,
  (error) => {
    console.error('Load error:', error);
  }
);
```

### DRACO 压缩支持

```typescript
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath('/draco/');

const loader = new GLTFLoader();
loader.setDRACOLoader(dracoLoader);
```

## Performance Considerations

| 优化项 | 建议 |
|--------|------|
| 布料顶点数 | ≤1000 (高性能) / ≤2000 (质量优先) |
| 纹理尺寸 | ≤2048x2048 |
| 模型格式 | GLB (二进制更小) |
| 加载策略 | 预加载 + 懒加载 |

## Browser Support

| 特性 | Chrome | Firefox | Safari | Edge |
|------|--------|---------|--------|------|
| WebGL 2.0 | 56+ | 51+ | 15+ | 79+ |
| WebGPU | 113+ | 可用(flag) | 不支持 | 113+ |

**降级策略**: WebGPU不可用时，three-simplecloth会自动降级到WebGL渲染模式（无GPU加速）。
