# Quickstart: 3D 人体测量服务

**Version**: 1.0.0 | **Prerequisites**: Python 3.11+, Docker, Docker Compose

---

## 1. 环境准备

### 1.1 克隆项目

```bash
git clone https://github.com/your-org/fitscan.git
cd fitscan
```

### 1.2 环境变量配置

创建 `.env` 文件：

```bash
# API 配置
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secure-api-key

# Redis (任务队列)
REDIS_URL=redis://localhost:6379/0

# InfluxDB
INFLUXDB_URL=http://localhost:8086
INFLUXDB_ORG=fitscan
INFLUXDB_BUCKET=measurements
INFLUXDB_TOKEN=your-influxdb-token

# MinIO (对象存储)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=measurements

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=fitscan-api
```

### 1.3 启动依赖服务

```bash
docker-compose up -d redis influxdb minio
```

验证服务运行：

```bash
docker-compose ps
```

---

## 2. 本地开发

### 2.1 安装依赖

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\Activate.ps1  # Windows

pip install -r requirements.txt
```

### 2.2 生成 Protobuf 代码

```bash
cd backend
python -m grpc_tools.protoc \
  -I./protos \
  --python_out=./src/websocket \
  --grpc_python_out=./src/websocket \
  ./protos/measurement.proto
```

### 2.3 启动服务

```bash
# 终端 1: 启动 FastAPI
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 终端 2: 启动 Celery Worker
celery -A src.worker.tasks worker --loglevel=info
```

### 2.4 验证服务

```bash
curl http://localhost:8000/health
```

预期响应：

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-26T12:00:00Z"
}
```

---

## 3. API 使用示例

### 3.1 创建扫描会话

```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "session_type": "realtime",
    "device_info": {
      "device_id": "CAM-001",
      "device_type": "depth_camera_v2"
    }
  }'
```

### 3.2 WebSocket 扫描

Python 示例：

```python
import asyncio
import websockets
from src.websocket import measurement_pb2

async def scan_session():
    uri = "ws://localhost:8000/ws/scan/{session_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with websockets.connect(uri, extra_headers=headers) as ws:
        # 开始扫描
        await ws.send('{"command": "start_scan", "params": {}}')
        response = await ws.recv()
        print(f"Started: {response}")

        # 发送帧数据（需要实际点云数据）
        # frame = measurement_pb2.ScanFrame()
        # await ws.send(frame.SerializeToString())

        # 结束扫描
        await ws.send('{"command": "end_scan", "params": {}}')
        response = await ws.recv()
        print(f"Result: {response}")

asyncio.run(scan_session())
```

### 3.3 上传离线文件

```bash
curl -X POST http://localhost:8000/api/v1/upload/glb \
  -H "Authorization: Bearer your-api-key" \
  -F "file=@./test_data/model.glb" \
  -F "user_id=550e8400-e29b-41d4-a716-446655440002" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440001"
```

### 3.4 查询测量结果

```bash
curl http://localhost:8000/api/v1/measurements?user_id=550e8400-e29b-41d4-a716-446655440002 \
  -H "Authorization: Bearer your-api-key"
```

---

## 4. 运行测试

### 4.1 单元测试

```bash
cd backend
pytest tests/unit/ -v
```

### 4.2 集成测试

```bash
# 确保所有依赖服务运行
docker-compose up -d

# 运行集成测试
pytest tests/integration/ -v
```

### 4.3 契约测试

```bash
pytest tests/contract/ -v
```

---

## 5. 项目结构概览

```
backend/
├── src/
│   ├── main.py              # FastAPI 应用入口
│   ├── api/
│   │   ├── routes/          # REST API 路由
│   │   └── deps.py          # 依赖注入
│   ├── websocket/
│   │   ├── manager.py       # 连接管理
│   │   ├── handler.py       # 消息处理
│   │   └── protocol.py      # 协议实现
│   ├── worker/
│   │   ├── tasks.py         # Celery 任务
│   │   └── processor.py     # 3D 处理逻辑
│   ├── storage/
│   │   ├── influxdb.py      # 时序数据库
│   │   └── minio.py         # 对象存储
│   ├── models/              # Pydantic 模型
│   ├── security/            # 认证 & 隐私
│   └── observability/        # 追踪 & 指标
├── protos/
│   └── measurement.proto    # Protobuf 定义
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── Dockerfile
```

---

## 6. 常见问题

### Q: WebSocket 连接被拒绝？
检查：
1. API Key 是否正确
2. session_id 是否存在
3. Nginx 代理是否允许 WebSocket

### Q: 文件上传失败？
检查：
1. 文件大小是否超过 100MB
2. MinIO 服务是否运行
3. 桶是否已创建

### Q: 测量结果为空？
检查：
1. 扫描帧是否足够（建议 > 300 帧）
2. 点云质量是否足够
3. Worker 是否正常运行

---

## 7. 下一步

- 阅读 [API 契约](contracts/rest-api.md)
- 阅读 [WebSocket 协议](contracts/websocket.md)
- 阅读 [数据模型](data-model.md)
- 查看 [研究文档](research.md)
