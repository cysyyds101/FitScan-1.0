# Data Model: 3D 人体测量服务

**Generated**: 2026-05-26 | **Status**: Draft

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    User     │──1:N──│  ScanSession    │──1:1──│   Measurement   │
│             │       │                 │        │                 │
│ - id        │       │ - id            │        │ - id            │
│ - email     │       │ - user_id       │        │ - session_id    │
│ - consent   │       │ - type          │        │ - timestamp     │
│ - created   │       │ - status        │        │ - status        │
└─────────────┘       │ - device_info   │        │ - metrics[]     │
                      │ - started_at    │        │ - raw_ref       │
                      │ - completed_at  │        └─────────────────┘
                      └─────────────────┘                │
                                                          │ N
                                                          ▼
                                                  ┌─────────────────┐
                                                  │MeasurementMetric│
                                                  │                 │
                                                  │ - type          │
                                                  │ - value         │
                                                  │ - unit          │
                                                  │ - confidence    │
                                                  └─────────────────┘
```

## Entity Definitions

### User

用户实体，包含身份验证和同意管理信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, NOT NULL | 用户唯一标识 |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 用户邮箱 |
| hashed_api_key | VARCHAR(255) | NOT NULL | API Key 哈希 |
| consent_given | BOOLEAN | NOT NULL, DEFAULT false | 是否已同意 |
| consent_timestamp | TIMESTAMP | NULLABLE | 同意时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |
| deleted_at | TIMESTAMP | NULLABLE | 软删除时间 |

**Indexes**:
- `idx_user_email` ON (email)
- `idx_user_consent` ON (consent_given)

---

### ScanSession

扫描会话，记录一次完整的扫描操作。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, NOT NULL | 会话唯一标识 |
| user_id | UUID | FK → User, NOT NULL | 关联用户 |
| session_type | ENUM | NOT NULL | 'realtime', 'offline' |
| status | ENUM | NOT NULL | 'pending', 'scanning', 'processing', 'completed', 'failed' |
| device_info | JSONB | NULLABLE | 设备信息（型号固件等） |
| started_at | TIMESTAMP | NOT NULL | 开始时间 |
| completed_at | TIMESTAMP | NULLABLE | 完成时间 |
| error_message | TEXT | NULLABLE | 错误信息（如失败） |
| metadata | JSONB | NULLABLE | 扩展元数据 |

**Indexes**:
- `idx_session_user` ON (user_id)
- `idx_session_status` ON (status)
- `idx_session_time` ON (started_at DESC)

---

### Measurement

测量记录，存储一次扫描的测量结果。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, NOT NULL | 测量唯一标识 |
| session_id | UUID | FK → ScanSession, NOT NULL | 关联会话 |
| status | ENUM | NOT NULL | 'processing', 'completed', 'error' |
| privacy_processed | BOOLEAN | NOT NULL, DEFAULT false | 是否已脱敏 |
| raw_data_ref | VARCHAR(512) | NULLABLE | MinIO 原始数据引用 |
| processed_at | TIMESTAMP | NULLABLE | 处理完成时间 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | NOT NULL | 更新时间 |

**Indexes**:
- `idx_measurement_session` ON (session_id)
- `idx_measurement_privacy` ON (privacy_processed)

---

### MeasurementMetric

测量指标，存储具体的测量数值。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | UUID | PK, NOT NULL | 指标唯一标识 |
| measurement_id | UUID | FK → Measurement, NOT NULL | 关联测量 |
| metric_type | VARCHAR(64) | NOT NULL | 指标类型（如 'chest_circumference'） |
| value | FLOAT | NOT NULL | 测量值 |
| unit | VARCHAR(16) | NOT NULL | 单位（如 'cm'） |
| confidence | FLOAT | NULLABLE | 置信度 0-1 |
| calibration_info | JSONB | NULLABLE | 校准信息 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

**Indexes**:
- `idx_metric_measurement` ON (measurement_id)
- `idx_metric_type` ON (metric_type)

**Metric Types (Initial Set)**:
- `height` - 身高
- `chest_circumference` - 胸围
- `waist_circumference` - 腰围
- `hip_circumference` - 臀围
- `arm_length` - 臂长
- `leg_length` - 腿长
- `shoulder_width` - 肩宽
- `body_weight_estimate` - 体重估算

---

## Protobuf Schema

```protobuf
syntax = "proto3";

package fitscan.measurement;

// 实时扫描帧数据
message ScanFrame {
  string session_id = 1;
  int64 frame_number = 2;
  int64 timestamp_ms = 3;
  PointCloudData point_cloud = 4;
  CameraMetadata camera_meta = 5;
}

message PointCloudData {
  repeated float vertices = 1;  // [x1,y1,z1, x2,y2,z2, ...]
  repeated int32 faces = 2;      // [i1,j1,k1, i2,j2,k2, ...]
  int32 vertex_count = 3;
  int32 face_count = 4;
}

message CameraMetadata {
  string device_id = 1;
  string device_type = 2;
  float focal_length = 3;
  repeated float distortion = 4;
}

// 测量结果
message MeasurementResult {
  string measurement_id = 1;
  string session_id = 2;
  int64 completed_at = 3;
  repeated Metric metrics = 4;
  ProcessingStatus status = 5;
}

message Metric {
  string type = 1;
  double value = 2;
  string unit = 3;
  double confidence = 4;
}

enum ProcessingStatus {
  PROCESSING = 0;
  COMPLETED = 1;
  ERROR = 2;
}

// WebSocket 命令
message WSCommand {
  string command = 1;
  map<string, string> params = 2;
}

// WebSocket 响应
message WSResponse {
  bool success = 1;
  string message = 2;
  oneof payload {
    MeasurementResult measurement = 3;
    ProcessingStatus status = 4;
  }
}
```

---

## State Machines

### ScanSession State Machine

```
                    ┌──────────────┐
                    │   pending    │
                    └──────┬───────┘
                           │ start_scan()
                           ▼
                    ┌──────────────┐
              ┌─────│  scanning   │─────┐
              │     └──────────────┘     │
  cancel()    │                          │ receive_last_frame()
  ▼            │                          ▼
  ┌──────────────┐              ┌──────────────┐
  │   cancelled  │              │  processing  │
  └──────────────┘              └──────┬───────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
              computation_success() ▼   │   ▼ computation_error()
                    ┌──────────────┐    │   ┌──────────────┐
                    │  completed   │    │   │    failed    │
                    └──────────────┘    │   └──────────────┘
                                        │
                                        ▼
                                  ┌──────────────┐
                                  │   completed  │
                                  └──────────────┘
```

---

## Validation Rules

| 实体 | 字段 | 规则 |
|------|------|------|
| MeasurementMetric | value | > 0 |
| MeasurementMetric | confidence | 0.0 - 1.0 |
| MeasurementMetric | unit | in ['cm', 'mm', 'inch', 'kg', 'lb'] |
| ScanSession | session_type | in ['realtime', 'offline'] |
| ScanSession | status | valid state transition |
| User | consent_given | must be true before measurement |

---

## Data Retention Policy

| 数据类型 | 保留期 | 清理策略 |
|----------|--------|----------|
| 原始点云 (MinIO) | 7 天 | 自动删除 |
| 测量结果 | 永久 | 用户可请求删除 |
| 同意记录 | 永久 | 法定保留 |
| 操作日志 | 1 年 | 归档后删除 |
| Trace 数据 | 30 天 | Tail Sampling 后删除 |
