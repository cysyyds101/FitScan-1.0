# FitScan — 3D 虚拟试衣系统

## 项目简介

上传照片 → 3D 人体重建 → 虚拟试衣

## 系统架构

```
Frontend (React + Three.js)
        │
        │ HTTP
        ▼
Backend (FastAPI + SQLite)
        │
        │ Task Queue
        ▼
AI Server (4×RTX 3090, SMPLer-X)
        │
        │ Shared Storage
        ▼
/ai_storage/recon/{id}/model.glb
```

## 快速启动

### 前端

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### AI Server

```bash
cd ai_server
python worker.py
```

## 页面说明

- `/virtual-tryon` — 上传照片 → 触发重建 → 3D Avatar → 虚拟换衣
- `/measure` — 摄像头拍照 → 上传 → 返回身高 / 胸围 / 腰围 / 臀围

## 当前进度

| 阶段 | 状态 | 内容 |
|------|------|------|
| Phase A–F | ✅ 完成 | pipeline、重建、资产注册 |
| Phase G | ✅ 完成 | UI 整合、摄像头、导航、错误边界 |
| Phase H | 🔲 待办 | ClothingOverlay 接入真实 GLB |
| Phase I | 🔲 待办 | 真实 SMPLer-X、ECharts Dashboard |

## 技术栈

- **Frontend**: React 18, Three.js, @react-three/fiber, @react-three/drei, Vite
- **Backend**: FastAPI, SQLite, Python 3.10+
- **AI**: SMPLer-X, PyTorch, CUDA
