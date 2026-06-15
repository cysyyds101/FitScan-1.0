# FitScan - 智能人体尺寸估算系统

基于单目视觉与参照物校准的智能人体尺寸测量工具，利用普通摄像头即可快速测量人体尺寸并推荐服装尺码。

## ✨ 核心功能

- **实时视频采集** - OpenCV 摄像头调用，支持多种分辨率
- **参照物校准** - 自动识别 A4 纸、身份证、银行卡，计算像素比例
- **人体关键点提取** - MediaPipe Pose / MoveNet 提取 33 个关键点
- **尺寸计算** - 肩宽、臂长、腿长、身高、胸围、腰围、臀围
- **尺码推荐** - 智能匹配最佳服装尺码（宽松版/修身版）
- **可视化展示** - AR 实时标注 + 雷达图体型分析

## 📁 项目结构

```
FitScan/
├── main/                    # 核心算法区（Python 桌面版）
│   ├── main.py              # 主程序入口
│   ├── geometry_calculator.py   # 几何计算模块
│   ├── size_recommender.py      # 尺码推荐模块
│   └── visualizer.py            # 可视化/雷达图
│
├── backend/                 # Flask 后端 + 桌面应用
│   ├── main.py              # pywebview 桌面应用入口
│   ├── app/                 # Flask 应用与摄像头服务
│   ├── requirements.txt     # Python 依赖
│   └── FitScan.spec         # PyInstaller 打包配置
│
├── frontend/                # React 前端应用
│   ├── src/
│   │   ├── pages/           # 页面组件（扫描/结果/历史）
│   │   ├── utils/           # 工具（图像处理、姿态估计、尺寸映射）
│   │   └── styles/          # 样式
│   └── package.json
│
├── fitscan_tauri/           # Tauri 桌面应用（备选方案）
│   ├── src/                 # Tauri 前端源码
│   └── tauri.conf.json      # Tauri 配置
│
├── movenet_model/           # MoveNet 姿态估计模型
├── videos/                  # 测试资源
└── sdkconfig/               # 编译配置与优化指南
```

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + Chart.js + TensorFlow.js |
| 后端 | Flask + WebSocket |
| 桌面端 | pywebview / Tauri |
| AI 模型 | MediaPipe Pose / MoveNet |
| 图像处理 | OpenCV |

## 🚀 快速开始

### 环境要求
- Python 3.7+
- Node.js 16+
- 摄像头设备

### 安装依赖

```bash
# Python 依赖
pip install -r backend/requirements.txt

# 前端依赖
cd frontend && npm install
```

### 运行方式

**方式一：Web 开发模式**
```bash
# 终端 1：启动后端
cd backend && python main.py

# 终端 2：启动前端
cd frontend && npm run dev
```

**方式二：桌面应用**
```bash
cd backend && python main.py
```

**方式三：原始 Python 版**
```bash
pip install -r sdkconfig/requirements.txt
python main/main.py
```

## 📖 使用说明

1. **校准** - 将 A4 纸/身份证/银行卡贴近胸前，系统自动检测参照物
2. **扫描** - 站在摄像头前，保持自然站姿，微微张开双臂
3. **结果** - 系统实时显示测量数据和推荐尺码
4. **按键** - `s` 锁定结果 / `r` 重新校准 / `q` 退出

## ⚠️ 注意事项

- 确保光线充足，避免背光
- 背景尽量简洁，避免复杂图案
- 摄像头与身体保持 1-2 米距离
- 参照物应与身体测量部位在同一平面
- 使用较大尺寸参照物（A4 纸优于银行卡）

## 📊 测量精度

| 尺寸 | 精度 |
|------|------|
| 肩宽 | ±2cm |
| 臂长 | ±3cm |
| 腿长 | ±3cm |
| 身高 | ±5cm（估算） |
| 围度 | ±4~5cm（估算） |

## 📄 许可证

MIT License