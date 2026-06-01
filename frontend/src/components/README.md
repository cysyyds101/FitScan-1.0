# FitScan Virtual Try-On Feature

A 3D virtual try-on system that allows users to upload clothing models and see how they look on a 3D human body with cloth physics simulation.

## Features

- **3D Human Model Display**: View a human body model with 360° rotation
- **Clothing Upload**: Upload your own GLB clothing models
- **Preset Clothing**: Choose from pre-configured clothing options
- **Position/Rotation/Scale Controls**: Fine-tune clothing placement
- **Cloth Physics**: Realistic wind and gravity effects on clothing
- **Responsive Design**: Works on desktop and mobile

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
npm install three@^0.182.0 three-simplecloth --legacy-peer-deps
```

### 2. Run Development Server

```bash
cd frontend
npm run dev
```

### 3. Open in Browser

Navigate to: http://localhost:5173/virtual-tryon

## Generating 3D Models

### Option 1: Use Model Generator Tool

1. Open `model-generator.html` in your browser
2. Click "一键生成所有模型" (Generate All Models)
3. Save the downloaded files to:
   - `humanoid.glb` → `frontend/public/models/human/default.glb`
   - `tshirt_red.glb` → `frontend/public/models/clothing/`
   - `hoodie_blue.glb` → `frontend/public/models/clothing/`
   - `dress_purple.glb` → `frontend/public/models/clothing/`

### Option 2: Download Free Models

Download rigged human models from:
- [CGTrader - Free Human Models](https://www.cgtrader.com/free-3d-models/character/woman)
- [Sketchfab - Rigged Models](https://sketchfab.com/search?q=rigged+human&type=models)

Save to `frontend/public/models/human/default.glb`

## Usage

### Basic Usage

```jsx
import { VirtualTryOn } from './components/VirtualTryOn';

function App() {
  return (
    <VirtualTryOn
      humanModelUrl="/models/human/default.glb"
      showControls={true}
    />
  );
}
```

### With Preset Clothing

```jsx
import { VirtualTryOn } from './components/VirtualTryOn';
import { PRESET_CLOTHING } from './utils/presetClothing';

function App() {
  return (
    <VirtualTryOn
      humanModelUrl="/models/human/default.glb"
      presetClothing={PRESET_CLOTHING}
      showControls={true}
    />
  );
}
```

### Custom Physics Settings

```jsx
<VirtualTryOn
  humanModelUrl="/models/human/default.glb"
  defaultPhysics={{
    stiffness: 0.5,
    dampening: 0.3,
    wind: { x: 1, y: 0, z: 0 },
    gravity: { x: 0, y: -9.8, z: 0 }
  }}
/>
```

## File Structure

```
frontend/src/
├── components/
│   ├── HumanModel.jsx      # Human model component
│   ├── ClothingOverlay.jsx  # Clothing positioning
│   ├── ClothingControls.jsx # Control panel UI
│   ├── ClothPhysics.jsx     # Physics simulation
│   └── VirtualTryOn.jsx     # Main container
├── pages/
│   └── VirtualTryOnPage.jsx
└── utils/
    ├── glbLoader.js        # GLB loading utilities
    └── presetClothing.js   # Preset clothing data

frontend/public/models/
├── human/
│   └── default.glb          # Human model
└── clothing/
    ├── tshirt_red.glb       # Sample clothing
    ├── hoodie_blue.glb
    └── dress_purple.glb
```

## Technology Stack

- **React 18** - UI framework
- **Three.js 0.182+** - 3D rendering
- **@react-three/fiber** - React renderer for Three.js
- **@react-three/drei** - Useful helpers for R3F
- **three-simplecloth** - Cloth physics simulation

## Browser Requirements

- Chrome 90+, Firefox 88+, Safari 15+, Edge 90+
- WebGL 2.0 support
- WebGPU support (for cloth physics, optional)

## Troubleshooting

### Model not loading
- Check browser console for errors
- Ensure the model URL path is correct
- Verify the model file exists in `public/models/`

### Cloth physics not working
- Requires WebGPU support
- May fall back to static display on unsupported browsers

### Performance issues
- Reduce model complexity (fewer triangles)
- Lower texture resolution
- Disable cloth physics on low-end devices

## License

MIT
