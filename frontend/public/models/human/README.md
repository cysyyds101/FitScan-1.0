# Virtual Try-On Models

This directory contains 3D models for the virtual try-on feature.

## Directory Structure

```
public/models/
├── human/           # Human body models
│   └── README.md    # This file
└── clothing/        # Clothing models
    └── README.md
```

## Adding Human Models

1. Download a rigged human model in GLB format:
   - [CGTrader: Realistic Human Female](https://www.cgtrader.com/free-3d-models/character/woman/realistic-human-female-full-body)
   - [Sketchfab: Rigged Human](https://sketchfab.com)

2. Place the `.glb` file in this directory:
   ```
   human/female_athletic.glb
   ```

3. The model should have:
   - Skeleton with bones
   - T-pose or A-pose for best compatibility
   - Less than 50,000 triangles for performance

## Adding Clothing Models

1. Download or create clothing models with vertex painting:
   - Red vertices = cloth simulation area
   - White vertices = static (attached to bones)

2. Place `.glb` files in the clothing directory:
   ```
   clothing/tshirt_red.glb
   clothing/jacket_blue.glb
   ```

## Performance Guidelines

| Type | Max Triangles | Max Texture Size |
|------|---------------|------------------|
| Human | 50,000 | 2048x2048 |
| Clothing | 20,000 | 1024x1024 |
