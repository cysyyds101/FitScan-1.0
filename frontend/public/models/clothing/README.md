# Clothing Models Directory

Place clothing GLB models here for the virtual try-on feature.

## Requirements

- GLB format (binary glTF)
- Rigged with bones (for attachment to human model)
- Vertex painting for cloth simulation:
  - **Red** = vertices that will be simulated as cloth
  - **White** = vertices that stay attached to bones

## Example Models

```
clothing/
├── tshirt.glb
├── hoodie.glb
├── dress.glb
└── jacket.glb
```

## Creating Cloth-Ready Models

In Blender:
1. Weight paint the clothing to the human skeleton
2. Paint vertices that should flow like cloth with red color
3. Export as GLB with vertex colors
