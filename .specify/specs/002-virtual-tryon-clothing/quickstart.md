# Quick Start: Virtual Try-On Clothing Overlay

## Prerequisites

- Node.js 18+
- npm 9+
- 现代浏览器 (Chrome 90+, Firefox 88+, Safari 15+, Edge 90+)
- WebGL 2.0 支持

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install three-simplecloth
```

### 2. Download Human Model

下载免费人体GLB模型:
- [CGTrader: Realistic Human Female](https://www.cgtrader.com/free-3d-models/character/woman/realistic-human-female-full-body)
- 或 [Sketchfab: Human Basemesh Rigged](https://sketchfab.com/3d-models/human-malefemale-basemesh-rigged-96fa14a)

放置到: `frontend/public/models/human.glb`

### 3. Create Clothing Directory

```bash
mkdir -p frontend/public/models/clothing
```

## Usage Scenarios

### Scenario 1: Basic Model Display

```jsx
import { VirtualTryOn } from './components/VirtualTryOn';

function App() {
  return (
    <VirtualTryOn
      humanModelUrl="/models/human.glb"
      showControls={true}
    />
  );
}
```

### Scenario 2: With Preset Clothing

```jsx
const PRESET_CLOTHING = [
  { id: 'tshirt', name: 'T恤', url: '/models/clothing/tshirt.glb' },
  { id: 'jacket', name: '外套', url: '/models/clothing/jacket.glb' },
];

<VirtualTryOn
  humanModelUrl="/models/human.glb"
  presetClothing={PRESET_CLOTHING}
  onClothingChange={(clothing) => console.log('Selected:', clothing.name)}
/>
```

### Scenario 3: Custom Physics Settings

```jsx
<VirtualTryOn
  humanModelUrl="/models/human.glb"
  defaultPhysics={{
    stiffness: 0.5,
    dampening: 0.3,
    wind: { x: 1, y: 0, z: 0 },
    gravity: { x: 0, y: -9.8, z: 0 }
  }}
/>
```

### Scenario 4: File Upload

用户可以直接上传自己的GLB服装:

```jsx
<input
  type="file"
  accept=".glb,.gltf"
  onChange={(e) => {
    const file = e.target.files[0];
    if (file) {
      handleClothingUpload(file);
    }
  }}
/>
```

## Performance Tips

| 场景 | 建议 |
|------|------|
| 布料性能差 | 降低布料顶点数，使用 `maxVertices: 1000` |
| 模型加载慢 | 使用DRACO压缩，纹理尺寸 ≤2048px |
| 移动设备 | 降低渲染分辨率，限制布料模拟 |
| 低端设备 | 禁用布料物理，使用静态服装 |

## Testing Checklist

- [ ] 人体模型正确加载并显示
- [ ] 可以360度旋转查看
- [ ] 可以缩放模型
- [ ] 可以上传GLB服装文件
- [ ] 服装正确叠加在人体上
- [ ] 位置调整滑块正常工作
- [ ] 旋转调整滑块正常工作
- [ ] 缩放调整滑块正常工作
- [ ] 布料重力下垂效果可见
- [ ] 风力变化时服装飘动
- [ ] 布料参数调整实时生效
- [ ] 错误处理正常工作

## Troubleshooting

### WebGL Not Supported
```
错误: "WebGL 2.0 is required"
解决: 更新浏览器或使用Chrome/Firefox
```

### Model Load Failed
```
错误: "Failed to load GLB model"
解决: 检查文件路径、格式、文件完整性
```

### Cloth Physics Not Working
```
错误: 服装保持静止不动
解决: 检查three-simplecloth安装、确认WebGPU支持
```
