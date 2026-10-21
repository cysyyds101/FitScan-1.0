# FitScan System Specification

**System Branch**: `system-architecture-v1`
**Created**: 2026-06-15
**Status**: Active

**Hardware Context**:
- Dev machine: Laptop without GPU (runs FastAPI + React dev server)
- AI Server: 4×NVIDIA RTX 3090 (runs AI inference only)
- Camera: Intel RealSense SR300 (USB connected to dev machine)

**Input**: User architecture requirements — Virtual Try-On, Real-time Body Measurement, 3D Model Generation, all under Monolith FastAPI + React constraints.

---

## 1. Architecture Overview

### 1.1 Hard Constraints (Non-Negotiable)

| Constraint | Rule |
|---|---|
| Monolith FastAPI only | No microservices, no Celery, no Redis |
| PostgreSQL / SQLite only | No InfluxDB, no MinIO, no object storage |
| Single Canvas per app | One `<Canvas>` in `core/Scene.jsx` |
| REST + WebSocket only | No gRPC, no MQTT |
| No GPU on dev machine | All AI inference must run on AI server |
| Must be runnable | MVP first, not over-engineered |

### 1.2 System Topology

```
┌─────────────────────────────────────────────────────────────┐
│  DEV MACHINE (Laptop, no GPU)                               │
│                                                             │
│  ┌──────────┐   ┌─────────────────┐   ┌─────────────────┐  │
│  │ React    │   │ FastAPI         │   │ RealSense SR300  │  │
│  │ Browser  │◄──│ (Monolith)      │   │ (USB)            │  │
│  │          │◄──│  - REST routes   │   └────────┬────────┘  │
│  │ - 3D     │◄──│  - WebSocket    │            │           │
│  │ - UI     │◄──│  - Business     │            ▼           │
│  │ - WS Rx  │   │    logic        │   ┌─────────────────┐  │
│  └──────────┘   └────────┬────────┘   │ capture.py      │  │
│                           │            │ (Python capture  │  │
│                           │            │  script, local)  │  │
│                           └────────────┤                  │  │
│                                       └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │ REST / WS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  AI SERVER (4×RTX 3090, GPU Farm)                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ FastAPI (Inference-only, stateless)                 │    │
│  │                                                      │    │
│  │  POST /ai/measure          → Precise body measure   │    │
│  │  POST /ai/generate-model   → 3D model generation    │    │
│  │                                                      │    │
│  │  [PyTorch / TensorFlow inference, no business logic] │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Data Flow Summary

| Feature | Data Source | Compute Location | Client Location |
|---|---|---|---|
| Virtual Try-On | Pre-loaded GLB models | Frontend (browser) | Frontend |
| Real-time Measurement | RealSense SR300 depth | Frontend (粗算) + AI Server (精算) | Frontend |
| 3D Model Generation | User photo / scan | AI Server (4×3090) | Frontend |
| Camera Stream | RealSense SR300 | capture.py (dev machine) | Frontend via WS |

### 1.4 Network Ports

| Service | Host | Port | Protocol |
|---|---|---|---|
| React dev server | localhost | 5173 | HTTP |
| FastAPI (dev) | localhost | 8000 | HTTP / WS |
| RealSense capture | localhost | 8765 | WebSocket |
| AI Server inference | `<AI_SERVER_IP>` | 8080 | HTTP REST |

---

## 2. Module Specifications

### 2.1 RealSense Camera Capture (`capture.py`)

**Location**: `backend/capture/`
**Purpose**: Read RealSense SR300 depth frames, stream to browser via WebSocket.

**Constraints**:
- Python script, runs as standalone process on dev machine
- NO FastAPI import (simple `websockets` library only)
- Outputs raw depth frame as binary (no JSON overhead)
- Falls back to simulated data if no RealSense connected

**Interface**:
```
WebSocket server: ws://localhost:8765
Message format: binary (640×480×4 bytes, float32 depth in mm)
```

**Behavior**:
1. Initialize RealSense pipeline
2. On each new frame, serialize depth data to binary
3. Broadcast to all connected WebSocket clients
4. If RealSense not connected, emit simulated sinusoidal depth pattern

**Files**:
```
backend/capture/
├── capture.py          # Main entry point
├── depth_streamer.py  # RealSense reader + fallback
└── requirements.txt    # pyrealsense2 + websockets
```

### 2.2 FastAPI Backend (Monolith)

**Location**: `backend/app/`
**Purpose**: Single FastAPI process, all business logic.

**API Routes**:

| Method | Path | Description | AI Server? |
|---|---|---|---|
| GET | `/api/health` | Health check | No |
| GET | `/api/clothing` | List clothing items | No |
| GET | `/api/clothing/{id}` | Get clothing detail | No |
| WS | `/ws/camera` | RealSense depth stream (relay) | No |
| POST | `/api/measurements` | Create measurement session | No |
| GET | `/api/measurements/{id}` | Get measurement result | No |
| POST | `/api/ai/measure` | Precise measurement (delegates to AI server) | **Yes** |
| POST | `/api/ai/generate` | Generate 3D model | **Yes** |
| GET | `/api/ai/status/{task_id}` | Check AI task status | No |

**Database Schema** (SQLite for dev):

```sql
CREATE TABLE measurements (
    id          TEXT PRIMARY KEY,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    raw_data    TEXT,     -- JSON blob of coarse measurement from frontend
    precise_data TEXT,    -- JSON blob from AI server
    status      TEXT DEFAULT 'pending',  -- pending / processing / done / error
    ai_task_id  TEXT      -- reference to AI server task
);

CREATE TABLE tryon_sessions (
    id          TEXT PRIMARY KEY,
    clothing_id TEXT,
    transform   TEXT,     -- JSON {position, rotation, scale}
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Service Layer** (`backend/app/services/`):
```
services/
├── storage.py       # SQLite via sqlite3 (no ORM)
├── ai_client.py     # HTTP client to AI server (httpx)
├── camera_ws.py     # WebSocket relay: browser ↔ capture.py
└── measurement.py   # Measurement business logic
```

**AI Server Communication** (`ai_client.py`):
```python
# All AI calls go through here. Dev machine has no GPU.
# AI server is a dumb inference endpoint, no business logic.
AI_SERVER_BASE = os.getenv("AI_SERVER_URL", "http://<AI_SERVER_IP>:8080")
```

### 2.3 Frontend Architecture

**Location**: `frontend/src/`

```
frontend/src/
├── core/
│   ├── Scene.jsx              # Only Canvas, camera, lights
│   ├── GLBLoader.js           # Unified GLB loading utility
│   └── DepthRenderer.jsx      # RealSense depth map → Three.js texture
├── components/
│   ├── HumanModel.jsx          # Human model (GLB + procedural fallback)
│   ├── ClothingOverlay.jsx     # Clothing overlay (group transform binding)
│   ├── ClothPhysics.jsx        # Pseudo-cloth vertex offset
│   ├── ClothingControls.jsx    # Unified UI panel (list + sliders)
│   ├── VirtualTryOn.jsx        # Try-on container + useTryOnState hook
│   ├── MeasurementOverlay.jsx  # Real-time measurement visualization
│   └── DepthCanvas.jsx         # Depth map display (2D canvas + 3D)
├── pages/
│   ├── VirtualTryOnPage.jsx    # Virtual try-on page
│   └── MeasurementPage.jsx    # Body measurement page
├── hooks/
│   ├── useCameraStream.js      # WebSocket → depth frame buffer
│   ├── useMeasurement.js       # Frontend coarse measurement logic
│   └── useAIInference.js       # AI server REST calls
└── App.jsx
```

**Key Design Decisions**:
- One `<Canvas>` only, in `core/Scene.jsx`
- Camera stream goes to **2D canvas** (depth visualization) AND **3D scene** (measurement overlay)
- Frontend does **coarse measurement** (3-5 cm accuracy) for real-time display
- AI server does **precise measurement** (sub-cm accuracy) for final results
- All AI calls are HTTP REST from frontend → FastAPI → AI Server

### 2.4 AI Server

**Location**: `ai_server/`
**Purpose**: GPU inference only. No FastAPI business logic.

**Endpoints**:

| Method | Path | Description |
|---|---|---|
| POST | `/infer/measure` | Precise body measurement from depth data |
| POST | `/infer/generate` | 3D model generation from photo/scan |
| GET | `/status/{task_id}` | Check async task status |

**Implementation Notes**:
- Uses `FastAPI` but only for routing inference calls
- No database, no business logic
- Model files stored locally on GPU server
- Returns JSON results (measurement numbers or model URL)
- For MVP: returns mock results (deterministic fake data) to verify full pipeline

**Files**:
```
ai_server/
├── main.py              # FastAPI inference app
├── models/
│   ├── measurement.py   # Measurement inference model
│   └── generator.py     # 3D model generation (Tripo/MNISTR3D/etc.)
├── inference/
│   └── run.py           # Model loading + inference
└── requirements.txt
```

---

## 3. Data Flow Details

### 3.1 RealSense Camera Stream

```
[RealSense SR300]  ──USB──  [capture.py:8765]
                                    │
                              binary depth frame
                                    │
                              WebSocket
                                    │
                               [FastAPI /ws/camera]
                                    │
                              relay (no processing)
                                    │
                              WebSocket
                                    │
                               [Browser]
                                    │
                         ┌──────────┴──────────┐
                         │                     │
                   [DepthCanvas]         [useMeasurement]
                   (2D depth map)        (coarse measure)
```

**Protocol**:
- `capture.py` → FastAPI: raw binary WebSocket
- FastAPI → Browser: raw binary WebSocket relay (no modification)
- Frame rate: ~30 FPS
- Data: 640×480 float32 depth values (mm), 1.2 MB/frame

### 3.2 Body Measurement Pipeline

```
Step 1: Frontend coarse measurement (real-time, ~3-5cm accuracy)
  [Depth frame] → [useMeasurement] → Display "Processing..."

Step 2: Frontend sends to FastAPI
  POST /api/measurements {session_id, coarse_data}

Step 3: FastAPI proxies to AI Server
  POST {AI_SERVER}/infer/measure {depth_blob}

Step 4: AI Server (4×3090) computes precise measurement
  Returns: {shoulder_width, chest, waist, inseam, ...} in mm

Step 5: FastAPI stores result, returns task_id
  GET /api/measurements/{id} → {precise_data, status: 'done'}

Step 6: Frontend polls or WebSocket notification
  Display precise measurement result on human model overlay
```

### 3.3 3D Model Generation Pipeline

```
User photo/scan → Frontend → POST /api/ai/generate
                                ↓
                        FastAPI (assign task_id, store 'pending')
                                ↓
                        POST {AI_SERVER}/infer/generate
                                ↓
                        AI Server (4×3090 runs Tripo/MNISTR3D, ~10-30s)
                                ↓
                        Model saved to /static/models/{task_id}.glb
                                ↓
                        GET /api/ai/status/{task_id} → {status: 'done', model_url}
                                ↓
                        Frontend loads GLB → VirtualTryOn → display on human
```

---

## 4. Frontend Pages

### 4.1 VirtualTryOnPage (`/virtual-tryon`)

- Loads human model (GLB / procedural)
- Clothing selection from API
- Transform controls (position / rotation / scale)
- Pseudo-cloth effect (breathing vertex offset)
- No camera dependency (works offline)

### 4.2 MeasurementPage (`/measure`)

- Connects to RealSense via WebSocket (`/ws/camera`)
- Displays live depth map (2D canvas)
- Shows coarse measurement overlay on 3D human model
- "Scan" button → sends to AI server for precise measurement
- Displays final measurement results

---

## 5. Configuration

### 5.1 Environment Variables

**Dev machine** (`backend/.env`):
```env
AI_SERVER_URL=http://<AI_SERVER_IP>:8080
SQLITE_DB=./fitscan.db
CAPTURE_WS_URL=ws://localhost:8765
CORS_ORIGINS=http://localhost:5173
```

**AI Server** (`ai_server/.env`):
```env
MODEL_PATH=./models
PORT=8080
GPU_IDS=0,1,2,3
```

### 5.2 Development vs Production

| Aspect | Dev | Prod |
|---|---|---|
| Database | SQLite | PostgreSQL |
| AI inference | Mock / localhost | 4×3090 remote |
| Camera | RealSense / simulated | RealSense |
| Static files | Local `public/` | CDN |
| Deployment | `npm run dev` + `uvicorn` | Docker / bare metal |

---

## 6. Success Criteria

| ID | Criteria | Target |
|---|---|---|
| SC-01 | Virtual try-on page loads with human model | < 3s |
| SC-02 | Clothing overlay renders and transforms | 30+ FPS |
| SC-03 | RealSense depth stream reaches browser | 30 FPS |
| SC-04 | Frontend coarse measurement displays | Real-time |
| SC-05 | AI server precise measurement returns | < 5s |
| SC-06 | 3D model generation pipeline end-to-end | < 30s |
| SC-07 | App runs without GPU on dev machine | ✓ |
| SC-08 | Architecture stays monolith FastAPI | ✓ (no microservices) |

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| RealSense SR300停产/驱动问题 | 高 | capture.py 有模拟数据回退；用 Realsense D400 系列替代 |
| AI服务器网络不稳定 | 中 | AI调用加超时重试（3次）；前端显示"离线模式"降级 |
| 4×3090 显存不够 | 低 | 模型分片加载；限制并发推理数 |
| RealSense深度精度不足 | 中 | 前端粗算+AI精算两层；SR300(~1mm精度)实际够用 |
| 前端WebSocket断连 | 低 | 自动重连；capture.py 广播给所有客户端 |

---

## 8. File Structure (Complete)

```
FitScan/
├── frontend/                    # React + Vite
│   ├── src/
│   │   ├── core/
│   │   │   ├── Scene.jsx
│   │   │   ├── GLBLoader.js
│   │   │   └── DepthRenderer.jsx
│   │   ├── components/
│   │   │   ├── HumanModel.jsx
│   │   │   ├── ClothingOverlay.jsx
│   │   │   ├── ClothPhysics.jsx
│   │   │   ├── ClothingControls.jsx
│   │   │   ├── VirtualTryOn.jsx
│   │   │   ├── MeasurementOverlay.jsx
│   │   │   └── DepthCanvas.jsx
│   │   ├── pages/
│   │   │   ├── VirtualTryOnPage.jsx
│   │   │   └── MeasurementPage.jsx
│   │   ├── hooks/
│   │   │   ├── useCameraStream.js
│   │   │   ├── useMeasurement.js
│   │   │   └── useAIInference.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── public/
│       └── models/           # GLB assets
│
├── backend/                    # FastAPI Monolith
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── schemas.py
│   │   │   └── routes/
│   │   │       ├── clothing.py
│   │   │       ├── measurements.py
│   │   │       └── ai_inference.py
│   │   └── services/
│   │       ├── storage.py      # SQLite
│   │       ├── ai_client.py    # httpx → AI server
│   │       ├── camera_ws.py   # WS relay
│   │       └── measurement.py
│   ├── capture/               # RealSense capture (standalone)
│   │   ├── capture.py
│   │   ├── depth_streamer.py
│   │   └── requirements.txt
│   └── requirements.txt
│
├── ai_server/                 # GPU Inference Server
│   ├── main.py
│   ├── models/
│   ├── inference/
│   └── requirements.txt
│
└── SPEC.md                    # This file
```

---

## 9. Implementation Priority

### Phase 1: Foundation (No camera, no AI)
- [x] FastAPI monolith with clothing API
- [x] React VirtualTryOn with GLB human + clothing
- [x] Frontend project structure (current sprint)

### Phase 2: RealSense Integration
- [ ] `capture.py` with simulated depth data (fallback)
- [ ] FastAPI `/ws/camera` WebSocket relay
- [ ] Frontend `useCameraStream` hook
- [ ] `DepthCanvas.jsx` (2D depth map)
- [ ] `MeasurementPage.jsx` skeleton

### Phase 3: Frontend Measurement
- [ ] `useMeasurement.js` (coarse, client-side)
- [ ] `MeasurementOverlay.jsx` on human model
- [ ] POST `/api/measurements` pipeline

### Phase 4: AI Server Integration
- [ ] AI Server stub (mock inference)
- [ ] `ai_client.py` in backend
- [ ] POST `/api/ai/measure` → AI Server
- [ ] POST `/api/ai/generate` → AI Server
- [ ] Frontend `useAIInference` hook

### Phase 5: Real Hardware
- [ ] Connect RealSense SR300 (verify driver)
- [ ] Replace simulated data with real depth
- [ ] Verify measurement accuracy
- [ ] 3D model generation end-to-end demo

---

*Architecture designed for MVP-first, single FastAPI monolith, no microservices.*
