# Contracts: Virtual Try-On Clothing Overlay

## Component Interfaces

### VirtualTryOn Component

```typescript
interface VirtualTryOnProps {
  humanModelUrl: string;           // 人体模型GLB路径
  presetClothing?: ClothingPreset[]; // 预设服装列表
  defaultPhysics?: PhysicsConfig;    // 默认物理参数
  showControls?: boolean;            // 是否显示控制面板
  onClothingChange?: (clothing: ClothingModel) => void;
  onPhysicsChange?: (config: PhysicsConfig) => void;
}

interface ClothingPreset {
  id: string;
  name: string;
  url: string;
  thumbnail?: string;
}

interface PhysicsConfig {
  stiffness: number;      // 0-1
  dampening: number;      // 0-1
  gravity: Vector3;
  wind: Vector3;
}
```

### ClothingOverlay Component

```typescript
interface ClothingOverlayProps {
  clothingUrl: string | null;
  humanModel: HumanModel | null;
  adjustment: UserAdjustment;
  onAdjustmentChange: (adjustment: UserAdjustment) => void;
}

interface UserAdjustment {
  positionOffset: { x: number; y: number; z: number };
  rotationOffset: { x: number; y: number; z: number };
  scale: number;
}
```

### ClothPhysics Component

```typescript
interface ClothPhysicsProps {
  clothingMesh: SkinnedMesh;
  config: PhysicsConfig;
  collidersRoot?: Object3D;
  onError?: (error: Error) => void;
}

interface ClothPhysicsReturn {
  update: (delta: number) => void;
  setWind: (wind: Vector3) => void;
  setGravity: (gravity: Vector3) => void;
  dispose: () => void;
}
```

## Events

### VirtualTryOn Events

| Event | Payload | Description |
|-------|---------|-------------|
| `clothing-loaded` | `ClothingModel` | 服装加载完成 |
| `clothing-applied` | `ClothingModel` | 服装应用到人体 |
| `clothing-removed` | `string` | 服装被移除 |
| `physics-updated` | `PhysicsConfig` | 物理参数更新 |
| `error` | `Error` | 发生错误 |

## File Requirements

### Supported Formats
- `.glb` - glTF Binary (推荐)
- `.gltf` - glTF with external resources

### File Constraints
- 最大文件大小: 10MB
- 必需包含骨骼绑定
- 推荐三角面数: <50,000
- 推荐纹理尺寸: ≤2048x2048
