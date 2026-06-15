# FitScan 桌面应用使用指南

## 概述

FitScan 桌面应用将 React 前端、Python 后端（OpenCV 摄像头 + AI 推理）和 pywebview 整合成一个独立的 .exe 文件，双击即可运行。

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    FitScan.exe                              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Python 后端 (后台线程)                     │  │
│  │                                                       │  │
│  │  ┌─────────────────────┐  ┌────────────────────────┐  │  │
│  │  │   Flask 服务器      │  │  WebSocket 服务器      │  │  │
│  │  │   (端口 5000)       │  │  (端口 8765)           │  │  │
│  │  │                     │  │                        │  │  │
│  │  │  - 托管前端静态文件  │  │  - OpenCV 摄像头管理   │  │  │
│  │  │  - 提供 API 接口    │  │  - 视频流推送          │  │  │
│  │  └─────────────────────┘  └────────────────────────┘  │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              pywebview 窗口                            │  │
│  │                                                       │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  前端 React 页面 (http://127.0.0.1:5000)        │  │  │
│  │  │                                                 │  │  │
│  │  │  ┌─────────────┐  ┌─────────────────────────┐  │  │  │
│  │  │  │ 摄像头画面  │  │  识别结果展示             │  │  │  │
│  │  │  │ (WebSocket) │  │  (localStorage)          │  │  │  │
│  │  │  └─────────────┘  └─────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 首次设置

**1. 安装 Python 依赖**

```bash
cd C:\FitScan\backend
pip install -r requirements.txt
```

**2. 构建前端**

```bash
cd C:\FitScan\frontend
npm run build
```

**3. 测试运行**

```bash
cd C:\FitScan\backend
python main.py
```

### 打包成 .exe

```bash
cd C:\FitScan\backend
pip install pyinstaller
pyinstaller FitScan.spec
```

打包完成后，可执行文件位于：
```
C:\FitScan\backend\dist\FitScan\FitScan.exe
```

### 日常使用

双击 `FitScan.exe` 即可启动应用。

---

## 文件结构

```
FitScan/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask 应用（含静态文件服务）
│   │   ├── config.py                # 配置
│   │   └── services/
│   │       ├── camera_service.py    # 摄像头管理
│   │       └── camera_socket.py     # WebSocket 服务
│   ├── main.py                      # 主入口（Flask + WS + pywebview）
│   ├── run_camera_ws.py             # 仅 WebSocket 服务（开发用）
│   ├── FitScan.spec                 # PyInstaller 打包配置
│   └── requirements.txt             # Python 依赖
├── frontend/
│   ├── src/
│   │   ├── utils/
│   │   │   ├── cameraWebSocket.js   # WebSocket 客户端
│   │   │   └── ...
│   │   └── pages/
│   │       └── MeasurementPage.jsx  # 测量页面
│   ├── dist/                        # 构建产物（由 npm run build 生成）
│   └── package.json
└── FitScan.exe                      # 最终可执行文件
```

---

## 开发模式 vs 桌面模式

### 开发模式（前端热更新）

```bash
# 窗口 1: Python WebSocket 服务
cd backend
python run_camera_ws.py

# 窗口 2: 前端开发服务器
cd frontend
npm run dev
```

访问 http://localhost:3000/

### 桌面模式（完整应用）

```bash
cd backend
python main.py
```

自动打开原生窗口，访问 http://127.0.0.1:5000

---

## 功能特性

### 1. 离线识别

- 上传照片 → 本地 MoveNet 模型推理
- 结果摘要：身高、推荐尺码
- 历史记录本地保存（localStorage）

### 2. 远程摄像头

- Python 后端通过 OpenCV 控制摄像头
- WebSocket 实时推送视频流
- 前端显示画面并拍照

### 3. 响应式设计

- 支持手机/平板/桌面
- 自适应布局

---

## 打包配置详解

### FitScan.spec

```python
datas=[
    # 包含前端构建产物
    ('frontend/dist', 'frontend/dist'),
]

hiddenimports=[
    'websockets',      # WebSocket 服务器
    'cv2',             # OpenCV
    'numpy',           # 数值计算
    'app.services.camera_service',
    'app.services.camera_socket',
]
```

### PyInstaller 命令

```bash
# 基本打包
pyinstaller FitScan.spec

# 单目录打包（调试用）
pyinstaller --onedir FitScan.spec

# 单文件打包（发布用）
pyinstaller --onefile FitScan.spec
```

---

## 故障排除

### 1. 窗口打开后显示空白

- 检查前端是否已构建：`frontend/dist/index.html` 是否存在
- 检查 Python 依赖是否安装完整

### 2. 摄像头无法使用

- 确保已安装 opencv-python
- 检查摄像头权限（Windows 隐私设置）
- 尝试不同的 camera_id

### 3. 打包后文件过大

- MoveNet 模型文件约 18MB
- 可使用 UPX 压缩：`--upx-dir=/path/to/upx`

### 4. pywebview 窗口无法打开

- 确保安装了 pywebview
- Windows 需要 WebView2 运行时（Windows 10/11 自带）
- 如需使用 Chromium 后端：`pip install pywebview[chromium]`

---

## 自定义

### 修改窗口大小

编辑 `backend/main.py`：

```python
WINDOW_SIZE = (1280, 800)  # 修改这里
```

### 修改端口

```python
FLASK_PORT = 5000   # Flask 端口
WS_PORT = 8765      # WebSocket 端口
```

### 修改应用标题

```python
WINDOW_TITLE = 'FitScan - 智能尺寸测量'  # 修改这里
```

---

## 下一步

- [ ] 添加自动更新功能
- [ ] 支持多语言
- [ ] 添加数据导出功能
- [ ] 优化打包体积