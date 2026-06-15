# FitScan 摄像头 WebSocket 服务使用指南

## 概述

本功能通过 WebSocket 协议将 Python 后端的摄像头画面实时传输到浏览器前端，实现远程摄像头控制和拍照功能。

## 架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户操作流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 用户打开前端页面                                             │
│         ▼                                                       │
│  2. 前端问 Python："有哪些摄像头？" ◄── Python 用 OpenCV 枚举设备│
│         ▼                                                       │
│  3. 前端显示摄像头列表给用户                                     │
│         ▼                                                       │
│  4. 用户点"开启" ──► 前端告诉 Python："打开 0 号摄像头"           │
│         ▼                                                       │
│  5. Python 用 cv2.VideoCapture(0) 打开摄像头                    │
│         ▼                                                       │
│  6. Python 每秒把画面编码为 JPEG，通过 WebSocket 推送给前端      │
│         ▼                                                       │
│  7. 前端收到图像，显示在 <img> 标签上 ←── 前端从来不碰摄像头硬件 │
│         ▼                                                       │
│  8. 用户点"拍照" ──► 前端告诉 Python："截一帧给我"               │
│         ▼                                                       │
│  9. Python 返回高清帧图像，前端送入 AI 模型推理                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 快速开始

### 1. 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

新增依赖：
- `websockets==12.0` - WebSocket 服务器
- `opencv-python==4.8.0` - 摄像头控制
- `numpy==1.24.0` - 图像处理

### 2. 启动摄像头 WebSocket 服务

```bash
cd backend
python run_camera_ws.py
```

输出示例：
```
==================================================
  FitScan 摄像头 WebSocket 服务
==================================================

启动参数:
  - 默认监听地址: 0.0.0.0
  - 默认端口: 8765

前端连接地址: ws://localhost:8765

按 Ctrl+C 停止服务
--------------------------------------------------

2024-01-01 12:00:00 - __main__ - INFO - Starting camera WebSocket server on ws://0.0.0.0:8765
2024-01-01 12:00:00 - __main__ - INFO - Camera WebSocket server running on ws://0.0.0.0:8765
```

### 3. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

### 4. 打开浏览器访问

打开 http://localhost:3000/，进入"智能尺寸测量"页面。

### 5. 使用远程摄像头

1. 点击 **"📡 连接远程摄像头"** 按钮
2. 前端会自动连接 Python 后端并枚举摄像头
3. 选择可用的摄像头并启动
4. 看到实时画面后，点击 **"📸 拍照识别"**

## WebSocket 消息协议

### 客户端 → 服务端消息

#### 1. 请求摄像头列表
```json
{ "type": "list_cameras" }
```

#### 2. 打开摄像头
```json
{
  "type": "open_camera",
  "camera_id": 0,
  "width": 640,
  "height": 480,
  "fps": 30
}
```

#### 3. 关闭摄像头
```json
{ "type": "close_camera", "camera_id": 0 }
```

#### 4. 获取单帧
```json
{ "type": "get_frame", "camera_id": 0 }
```

#### 5. 开始视频流
```json
{
  "type": "start_stream",
  "camera_id": 0,
  "quality": 85
}
```

#### 6. 停止视频流
```json
{ "type": "stop_stream" }
```

### 服务端 → 客户端消息

| type | 说明 | 数据结构 |
|------|------|----------|
| `camera_list` | 摄像头列表 | `{ cameras: [{id, name, available}] }` |
| `camera_opened` | 摄像头打开结果 | `{ success: bool, camera_id: int }` |
| `camera_closed` | 摄像头关闭结果 | `{ success: bool, camera_id: int }` |
| `frame` | 单帧图像 | `{ success: bool, data: "base64..." }` |
| `stream_started` | 视频流开始 | `{ success: bool, camera_id: int }` |
| `stream_frame` | 视频流帧 | `{ data: "base64..." }` |
| `stream_stopped` | 视频流停止 | `{ camera_id: int }` |
| `stream_error` | 视频流错误 | `{ message: string }` |
| `error` | 错误消息 | `{ message: string }` |

## 文件结构

```
backend/
├── app/
│   └── services/
│       ├── camera_service.py      # 摄像头管理服务（OpenCV 封装）
│       └── camera_socket.py       # WebSocket 服务（消息路由）
├── run_camera_ws.py               # 启动脚本
└── requirements.txt               # Python 依赖

frontend/
├── src/
│   ├── utils/
│   │   ├── cameraWebSocket.js     # WebSocket 客户端
│   │   └── ...
│   └── pages/
│       └── MeasurementPage.jsx    # 测量页面（已集成摄像头）
└── ...
```

## 核心 API

### Python CameraService

```python
from app.services.camera_service import camera_service

# 枚举摄像头
cameras = camera_service.enumerate_cameras(max_test=10)

# 打开摄像头
success = camera_service.open_camera(camera_id=0, width=640, height=480, fps=30)

# 获取单帧
frame_bytes = camera_service.get_frame(camera_id=0, max_jpeg_quality=85)

# 获取视频流（生成器）
for frame_bytes in camera_service.get_stream(camera_id=0, quality=85):
    # 发送帧...
    pass

# 关闭摄像头
camera_service.release_camera(camera_id=0)
```

### JavaScript CameraWebSocket

```javascript
import { cameraWebSocket } from '../utils/cameraWebSocket'

// 连接
await cameraWebSocket.connect()

// 获取摄像头列表
const cameras = await cameraWebSocket.listCameras()

// 打开摄像头
await cameraWebSocket.openCamera(0, 640, 480, 30)

// 开始视频流
await cameraWebSocket.startStream((base64Image) => {
  // base64Image 格式: "data:image/jpeg;base64,..."
  videoElement.src = base64Image
})

// 获取单帧
const base64Frame = await cameraWebSocket.getFrame()

// 停止视频流
await cameraWebSocket.stopStream()

// 关闭摄像头
await cameraWebSocket.closeCamera()

// 断开连接
cameraWebSocket.disconnect()
```

## 故障排除

### 1. 无法连接 WebSocket

- 确保 Python 服务已启动
- 检查端口 8765 是否被占用
- 确认防火墙允许连接

### 2. 摄像头枚举失败

- 确保已安装 `opencv-python`
- 检查摄像头权限（Windows 隐私设置）
- 尝试不同的 camera_id（0, 1, 2...）

### 3. 视频流卡顿

- 降低分辨率（如 320x240）
- 降低帧率（如 15fps）
- 降低 JPEG 质量（如 70）

### 4. 拍照黑屏

- 确保视频流正在运行
- 检查 `getCachedImage()` 是否返回数据
- 查看浏览器控制台错误信息

## 性能优化建议

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| 分辨率 | 640x480 | 平衡质量和性能 |
| 帧率 | 30fps | 流畅视频体验 |
| JPEG 质量 | 85 | 良好画质 + 较小体积 |
| 网络 | 本地局域网 | 延迟 < 50ms |

## 安全注意事项

1. **仅限本地使用**：此服务设计用于本地/局域网环境
2. **不暴露公网**：不要将 8765 端口暴露到公网
3. **摄像头权限**：确保用户授权摄像头访问

## 下一步

- [ ] 添加多摄像头同时支持
- [ ] 添加截图保存功能
- [ ] 支持 RTSP 流接入
- [ ] 添加人脸识别辅助对焦