# WebSocket Protocol Specification: 3D 人体测量服务

**Version**: 1.0.0 | **Path**: `/ws/scan/{session_id}`

## Connection

**Endpoint**: `wss://api.example.com/ws/scan/{session_id}`

**Headers**:
```
Authorization: Bearer <api_key>
```

**Connection Flow**:
1. 客户端连接到 WebSocket 端点
2. 服务器验证 session_id 和认证信息
3. 连接成功返回确认消息
4. 双方开始交换消息

---

## Message Format

所有消息使用 Protobuf 二进制格式（见 `protos/measurement.proto`）。

**消息类型**:
- `WSCommand` (Client → Server)
- `WSResponse` (Server → Client)
- `ScanFrame` (Client → Server, binary)

---

## Client → Server Messages

### 1. Start Scan Command

开始扫描会话。

```json
{
  "command": "start_scan",
  "params": {
    "device_id": "CAM-001",
    "resolution": "1280x720",
    "frame_rate": "30"
  }
}
```

**Server Response**:
```json
{
  "success": true,
  "message": "Scan started",
  "payload": {
    "status": "scanning"
  }
}
```

---

### 2. Send Frame

发送一帧 3D 点云数据。

**Binary Message**: 直接发送 `ScanFrame` Protobuf 消息

```
[4 bytes: message_size][message_size bytes: ScanFrame binary]
```

**Server Response** (异步，批量发送):
```json
{
  "success": true,
  "message": "Frame received",
  "payload": {
    "frame_number": 42,
    "processing_status": "queued"
  }
}
```

---

### 3. End Scan Command

结束扫描并触发处理。

```json
{
  "command": "end_scan",
  "params": {}
}
```

**Server Response**:
```json
{
  "success": true,
  "message": "Scan ended, processing started",
  "payload": {
    "status": "processing",
    "estimated_completion_ms": 15000
  }
}
```

---

### 4. Get Status

查询当前处理状态。

```json
{
  "command": "get_status",
  "params": {}
}
```

**Server Response**:
```json
{
  "success": true,
  "message": "Status retrieved",
  "payload": {
    "status": "processing",
    "frames_received": 450,
    "progress_percent": 75
  }
}
```

---

## Server → Client Messages

### 1. Measurement Result

测量完成通知。

```json
{
  "success": true,
  "message": "Measurement completed",
  "payload": {
    "measurement": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "completed_at": 1716729615000,
      "status": "COMPLETED",
      "metrics": [
        {"type": "height", "value": 175.5, "unit": "cm", "confidence": 0.95},
        {"type": "chest_circumference", "value": 92.3, "unit": "cm", "confidence": 0.88}
      ]
    }
  }
}
```

---

### 2. Progress Update

处理进度通知。

```json
{
  "success": true,
  "message": "Processing update",
  "payload": {
    "status": "processing",
    "progress_percent": 45,
    "current_step": "point_cloud_alignment"
  }
}
```

---

### 3. Error Notification

错误通知。

```json
{
  "success": false,
  "message": "Processing error occurred",
  "payload": {
    "status": "ERROR",
    "error_code": "LOW_QUALITY_SCAN",
    "error_message": "Insufficient point cloud coverage",
    "recovery_hint": "Please ensure full body is captured"
  }
}
```

---

### 4. Heartbeat

心跳保活。

```json
{
  "success": true,
  "message": "pong"
}
```

---

## Error Codes

| Code | 说明 | 处理建议 |
|------|------|----------|
| SESSION_NOT_FOUND | 会话不存在 | 创建新会话 |
| UNAUTHORIZED | 认证失败 | 重新认证 |
| SESSION_CLOSED | 会话已关闭 | 创建新会话 |
| INVALID_FRAME | 帧数据格式错误 | 检查数据格式 |
| RATE_LIMITED | 发送频率过高 | 降低发送频率 |
| LOW_QUALITY_SCAN | 扫描质量不足 | 重新扫描 |
| PROCESSING_TIMEOUT | 处理超时 | 重试请求 |

---

## Best Practices

### 1. 连接管理
- 实现自动重连机制（指数退避）
- 建议心跳间隔：30秒
- 连接超时：60秒

### 2. 数据发送
- 批量发送帧数据（每 5-10 帧一批）
- 使用二进制格式减少带宽
- 帧间间隔建议：33ms（30fps）

### 3. 错误处理
- 所有非成功响应需要记录日志
- `LOW_QUALITY_SCAN` 应提示用户重新扫描
- 网络断开时缓存未确认的帧

---

## Message Sequence Example

```
Client                           Server
  │                                │
  │──── CONNECT ─────────────────►│
  │                                │
  │◄─── CONNECTION_ACK ───────────│
  │                                │
  │──── start_scan ───────────────►│
  │◄─── success ──────────────────│
  │                                │
  │──── [ScanFrame binary] ───────►│
  │◄─── frame_received ────────────│
  │──── [ScanFrame binary] ───────►│
  │◄─── frame_received ────────────│
  │         ...                    │
  │──── end_scan ─────────────────►│
  │◄─── processing_started ────────│
  │                                │
  │◄─── progress_update ──────────│
  │◄─── progress_update ──────────│
  │◄─── measurement_result ───────│
  │                                │
  │──── DISCONNECT ───────────────►│
```
