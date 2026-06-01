# REST API Specification: 3D 人体测量服务

**Version**: 1.0.0 | **Base Path**: `/api/v1`

## Authentication

所有 API 请求需要通过 `Authorization` 头传递 API Key：

```
Authorization: Bearer <api_key>
```

或通过 `X-API-Key` 头：

```
X-API-Key: <api_key>
```

---

## Endpoints

### Health Check

#### GET /health

健康检查接口。

**Response 200**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-05-26T12:00:00Z"
}
```

---

### Measurement Operations

#### GET /measurements

查询用户的历史测量记录。

**Query Parameters**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| user_id | UUID | 是 | 用户 ID |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页数量，默认 20，最大 100 |
| start_date | ISO8601 | 否 | 开始日期过滤 |
| end_date | ISO8601 | 否 | 结束日期过滤 |

**Response 200**:
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "session_id": "550e8400-e29b-41d4-a716-446655440001",
      "session_type": "realtime",
      "status": "completed",
      "created_at": "2026-05-26T10:30:00Z",
      "metrics_summary": {
        "height": 175.5,
        "chest_circumference": 92.3
      }
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

#### GET /measurements/{measurement_id}

获取特定测量详情。

**Path Parameters**:
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| measurement_id | UUID | 是 | 测量记录 ID |

**Response 200**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "completed",
  "privacy_processed": true,
  "created_at": "2026-05-26T10:30:00Z",
  "completed_at": "2026-05-26T10:30:15Z",
  "metrics": [
    {
      "type": "height",
      "value": 175.5,
      "unit": "cm",
      "confidence": 0.95
    },
    {
      "type": "chest_circumference",
      "value": 92.3,
      "unit": "cm",
      "confidence": 0.88
    }
  ],
  "metadata": {
    "processing_time_ms": 1250,
    "algorithm_version": "2.1.0"
  }
}
```

**Response 404**:
```json
{
  "error": "not_found",
  "message": "Measurement not found"
}
```

---

#### DELETE /measurements/{measurement_id}

删除测量记录（GDPR 删除权）。

**Response 204**: No Content

**Response 404**:
```json
{
  "error": "not_found",
  "message": "Measurement not found"
}
```

---

### Scan Session Operations

#### POST /sessions

创建新的扫描会话。

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "session_type": "realtime",
  "device_info": {
    "device_id": "CAM-001",
    "device_type": "depth_camera_v2"
  }
}
```

**Response 201**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "session_type": "realtime",
  "status": "pending",
  "websocket_url": "wss://api.example.com/ws/scan/550e8400-e29b-41d4-a716-446655440001",
  "created_at": "2026-05-26T10:00:00Z"
}
```

---

#### GET /sessions/{session_id}

获取会话状态。

**Response 200**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "session_type": "realtime",
  "status": "scanning",
  "started_at": "2026-05-26T10:05:00Z",
  "device_info": {
    "device_id": "CAM-001",
    "device_type": "depth_camera_v2"
  }
}
```

---

#### POST /sessions/{session_id}/complete

标记会话完成（对于实时扫描）。

**Response 200**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "processing",
  "message": "Session marked complete, processing started",
  "estimated_completion_seconds": 15
}
```

---

### File Upload

#### POST /upload/glb

上传 glTF/glb 格式的 3D 模型文件进行离线处理。

**Request**: `multipart/form-data`

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| file | binary | 是 | glTF/glb 文件，最大 100MB |
| user_id | UUID | 是 | 用户 ID |
| session_id | UUID | 是 | 关联会话 ID |

**Response 202**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "queued",
  "message": "File uploaded successfully, processing started",
  "estimated_completion_seconds": 30
}
```

**Response 413**:
```json
{
  "error": "file_too_large",
  "message": "File size exceeds 100MB limit",
  "max_size_mb": 100
}
```

---

#### GET /upload/{task_id}/status

查询文件处理任务状态。

**Response 200**:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "completed",
  "progress_percent": 100,
  "measurement_id": "550e8400-e29b-41d4-a716-446655440000",
  "completed_at": "2026-05-26T10:35:00Z"
}
```

---

## Error Responses

所有错误遵循统一格式：

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {
    "field": "Additional error details"
  },
  "request_id": "req-abc123"
}
```

### Error Codes

| HTTP Status | Error Code | 说明 |
|-------------|-----------|------|
| 400 | invalid_request | 请求格式错误 |
| 401 | unauthorized | 认证失败 |
| 403 | forbidden | 无权限访问 |
| 404 | not_found | 资源不存在 |
| 409 | conflict | 资源冲突 |
| 413 | file_too_large | 文件过大 |
| 422 | validation_error | 数据验证失败 |
| 429 | rate_limited | 请求过于频繁 |
| 500 | internal_error | 服务器内部错误 |
| 503 | service_unavailable | 服务不可用 |
