# Feature Specification: FastAPI 3D 人体测量数据服务

**Feature Branch**: `faster-3d-body-measurement-api`

**Created**: 2026-05-26

**Status**: Draft

**Input**: 基于Clarify阶段收集的架构决策

## Clarifications

### Session 2026-05-26

- Q: API通信模式选择 → A: REST API + WebSocket（非阻塞）+ 二进制序列化
- Q: 3D数据序列化格式 → A: glTF/FBX 标准格式 + 自定义测量Schema
- Q: 两个数据源的类型 → A: 摄像头实时流 + 离线文件导入
- Q: 隐私保护方案 → A: TLS + 脱敏 + 最小权限 + GDPR合规 + 3D几何不可逆处理
- Q: 可观测性方案 → A: 明确SLA + 全链路追踪 + Tail-based Sampling

## User Scenarios & Testing

### User Story 1 - 实时3D扫描与测量 (Priority: P1)

作为系统集成商，我希望通过WebSocket接收实时摄像头流数据，并在测量完成后通过REST API获取测量结果，以便在业务应用中展示用户的身体数据。

**Why this priority**: 核心功能，支撑实时扫描场景

**Independent Test**: 可通过模拟摄像头流和验证测量结果API完成独立测试

**Acceptance Scenarios**:

1. **Given** 摄像头设备已连接，**When** 开始扫描，**Then** WebSocket接收实时数据流
2. **Given** 扫描完成，**When** 调用GET /measurements/{id}，**Then** 返回完整测量结果
3. **Given** 测量计算中，**When** WebSocket持续接收帧数据，**Then** 不阻塞消息收发循环

---

### User Story 2 - 离线文件批量处理 (Priority: P2)

作为数据分析师，我希望上传glTF/FBX格式的3D人体模型文件，系统自动解析并返回测量数据，以便批量处理历史扫描数据。

**Why this priority**: 支撑批量分析和历史数据回溯

**Independent Test**: 可通过上传测试文件和验证处理结果完成独立测试

**Acceptance Scenarios**:

1. **Given** 用户已登录，**When** 上传glTF文件，**Then** 返回处理任务ID
2. **Given** 处理完成，**When** 查询任务状态，**Then** 返回测量结果
3. **Given** 文件格式错误，**When** 上传文件，**Then** 返回友好的错误提示

---

### User Story 3 - 测量数据历史查询 (Priority: P3)

作为健康管理应用，我希望查询同一用户的历史测量记录，支持趋势分析和对比，以便跟踪身体变化。

**Why this priority**: 增值功能，提升用户粘性

**Independent Test**: 可通过查询历史记录API完成独立测试

**Acceptance Scenarios**:

1. **Given** 用户有多条测量记录，**When** 查询历史，**Then** 返回分页列表
2. **Given** 用户请求趋势数据，**When** 调用分析接口，**Then** 返回变化趋势

---

### Edge Cases

- 当摄像头流中断时，系统应保持连接并显示设备离线状态
- 当测量算法计算超时（如复杂模型），应返回超时错误并允许重试
- 当上传文件超过大小限制，应拒绝并返回明确的文件大小限制信息
- 当3D数据损坏或不完整，测量服务应返回数据质量问题报告

## Requirements

### Functional Requirements

- **FR-001**: 系统必须通过REST API提供测量数据的上传、查询和管理功能
- **FR-002**: 系统必须通过WebSocket提供实时摄像头数据流接收能力
- **FR-003**: 3D算法运算必须在独立进程/线程池中执行，不阻塞WebSocket消息循环
- **FR-004**: 系统必须支持glTF和FBX格式的3D模型文件导入
- **FR-005**: 系统必须采用Protobuf/MessagePack进行实时数据传输，减少JSON开销
- **FR-006**: 系统必须对3D几何数据进行隐私脱敏处理
- **FR-007**: 系统必须实现全链路追踪（OpenTelemetry）
- **FR-008**: 系统必须实现Tail-based Sampling以控制追踪数据存储成本
- **FR-009**: 系统必须支持GDPR合规要求（生物特征数据显式同意 + 强加密存储）
- **FR-010**: 系统必须定义明确的SLA指标（实时流延迟 < Xms，离线计算 < Ys）

### Non-Functional Requirements

- **性能**: 实时流消息延迟 < 100ms P99，离线计算 < 30s P95
- **吞吐量**: 支持100+并发WebSocket连接
- **可用性**: 服务可用性 >= 99.9%
- **安全**: TLS 1.3加密，API认证与授权，最小权限原则

### Key Entities

- **Measurement**: 测量记录（ID、用户ID、时间戳、测量指标列表、原始数据引用）
- **User**: 用户（ID、授权信息、同意记录）
- **ScanSession**: 扫描会话（ID、类型[实时/离线]、状态、关联测量ID）
- **MeasurementMetric**: 测量指标（类型、值、单位、校准信息）

## Architecture

### Data Flow

```
[摄像头] ──WebSocket──> [Nginx] ──> [FastAPI接入层]
                                    │
                                    ├── [任务队列] ──> [计算层] ──> [InfluxDB/MinIO]
                                    │
                                    └── [REST API] ──> [存储层]
```

### Technology Stack

| 层级 | 技术选型 |
|------|----------|
| 接入层 | Nginx (限流) + FastAPI UploadFile |
| 计算层 | 任务队列 (Celery/ARQ) + ProcessPoolExecutor |
| 存储层 | InfluxDB (时序数据) + MinIO/S3 (文件) |
| 协议层 | Protobuf / MessagePack |
| 追踪 | OpenTelemetry + Tail Sampling |

### Security Architecture

- **传输安全**: TLS 1.3
- **数据脱敏**: 3D几何数据不可逆处理（存参数或特征向量，不存完整模型）
- **合规**: GDPR生物特征数据要求
- **访问控制**: API Key / JWT + 最小权限

## Success Criteria

### Measurable Outcomes

- **SC-001**: 实时流消息从发送到接收的端到端延迟 < 100ms P99
- **SC-002**: 离线测量处理在30秒内完成P95请求
- **SC-003**: WebSocket连接稳定性 >= 99.5%（无断流丢失）
- **SC-004**: Trace存储成本降低90%（通过Tail Sampling）
- **SC-005**: API响应时间 < 200ms P95（不含计算时间）
- **SC-006**: 系统支持100+并发实时扫描会话

## Assumptions

- 用户数据将存储在合规的云服务或私有数据中心
- 3D测量算法已封装为独立服务，本系统负责编排和结果聚合
- 摄像头设备支持标准流推送协议（WebSocket/RTMP）
- 团队熟悉Python异步编程和FastAPI框架
