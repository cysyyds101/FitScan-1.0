# GitHub Issues - FitScan 3D 人体测量服务

> 导入说明：将以下内容复制到 GitHub Issues 页面，或使用 GitHub CLI (`gh issue create`) 批量创建

## Epic Issues (Large Features)

### Issue #1: [Epic] 3D 人体测量服务后端
**Labels**: epic, backend

```markdown
## Epic: 3D 人体测量服务后端

构建基于 FastAPI 的 3D 人体测量数据后端服务

### 技术栈
- Python 3.11+ / FastAPI
- WebSocket 实时流处理
- Celery + Redis 任务队列
- InfluxDB + MinIO 存储
- OpenTelemetry 全链路追踪

### User Stories
- US1: 实时3D扫描与测量 (P1 - MVP)
- US2: 离线文件批量处理 (P2)
- US3: 测量数据历史查询 (P3)

### 参考文档
- Spec: .specify/specs/faster-3d-body-measurement-api/spec.md
- Plan: .specify/specs/faster-3d-body-measurement-api/plan.md
```

---

## Milestone: Phase 1 - Setup

### Issue #2: T001 项目结构初始化
**Labels**: phase-1, backend
**Milestone**: Phase 1: Setup

```markdown
## T001: 项目结构初始化

**文件路径**: backend/src/

### 任务描述
按照 plan.md 创建 backend 目录结构，包括：
- backend/src/api/routes/
- backend/src/websocket/
- backend/src/worker/
- backend/src/storage/
- backend/src/models/
- backend/src/security/
- backend/src/observability/
- backend/tests/

### 验收标准
- 所有目录已创建
- 目录结构符合 plan.md 规划
```

### Issue #3: T002 Python 包初始化
**Labels**: phase-1, backend
**Milestone**: Phase 1: Setup

```markdown
## T002: Python 包初始化

**文件路径**: backend/src/

### 任务描述
为所有 Python 包创建 __init__.py 文件：
- backend/src/__init__.py
- backend/src/api/__init__.py
- backend/src/api/routes/__init__.py
- backend/src/websocket/__init__.py
- backend/src/worker/__init__.py
- backend/src/storage/__init__.py
- backend/src/models/__init__.py
- backend/src/security/__init__.py
- backend/src/observability/__init__.py
- backend/tests/__init__.py

### 验收标准
- 所有 __init__.py 文件存在
- 包结构正确
```

### Issue #4: T003 依赖配置
**Labels**: phase-1, backend
**Milestone**: Phase 1: Setup

```markdown
## T003: 依赖配置

**文件路径**: backend/requirements.txt

### 任务描述
创建 requirements.txt，包含：
- fastapi>=0.110.0
- uvicorn>=0.27.0
- websockets>=12.0
- celery>=5.3.0
- redis>=5.0.0
- influxdb-client>=1.40.0
- minio>=7.0.0
- opentelemetry-api>=1.22.0
- opentelemetry-sdk>=1.22.0
- protobuf>=4.25.0
- pydantic>=2.0.0
- python-jose>=3.3.0
- python-multipart>=0.0.6

### 验收标准
- requirements.txt 存在
- 依赖版本兼容
```

### Issue #5: T004 Protobuf 定义
**Labels**: phase-1, backend
**Milestone**: Phase 1: Setup

```markdown
## T004: Protobuf 消息定义

**文件路径**: backend/protos/measurement.proto

### 任务描述
创建 Protobuf 定义文件，包含：
- ScanFrame: 实时扫描帧数据
- PointCloudData: 点云数据
- CameraMetadata: 摄像头元数据
- MeasurementResult: 测量结果
- Metric: 单个测量指标
- WSCommand: WebSocket 命令
- WSResponse: WebSocket 响应

### 验收标准
- .proto 文件符合规范
- 可用 protoc 编译
```

### Issue #6: T005 Dockerfile
**Labels**: phase-1, backend
**Milestone**: Phase 1: Setup

```markdown
## T005: Docker 配置

**文件路径**: backend/Dockerfile

### 任务描述
创建 FastAPI 应用的 Dockerfile：
- 基于 python:3.11-slim
- 安装系统依赖
- 复制并安装 Python 依赖
- 生成 Protobuf 代码
- 暴露端口 8000
- 启动命令

### 验收标准
- Docker 镜像可构建
- 容器可正常启动
```

### Issue #7: T006 Docker Compose
**Labels**: phase-1, backend, infrastructure
**Milestone**: Phase 1: Setup

```markdown
## T006: Docker Compose 配置

**文件路径**: docker-compose.yml

### 任务描述
创建开发环境 docker-compose.yml，包含：
- redis: Redis 消息队列
- influxdb: 时序数据库
- minio: 对象存储
- backend: FastAPI 应用（开发模式）

### 验收标准
- 所有服务可启动
- 服务间网络连通
```

### Issue #8: T007 Nginx 配置
**Labels**: phase-1, backend, infrastructure
**Milestone**: Phase 1: Setup

```markdown
## T007: Nginx 配置

**文件路径**: nginx/conf.d/api.conf

### 任务描述
创建 Nginx 配置：
- API 路由到 FastAPI
- WebSocket 支持
- 速率限制
- 上传大小限制 100MB
- SSL/TLS 配置

### 验收标准
- 配置语法正确
- 支持 WebSocket 升级
- 速率限制生效
```

---

## Milestone: Phase 2 - Foundational

### Issue #9: T008-T012 数据模型
**Labels**: phase-2, backend, models
**Milestone**: Phase 2: Foundational

```markdown
## T008-T012: Pydantic 数据模型

**文件路径**: backend/src/models/

### 任务描述
实现所有数据模型：
- T008: models/__init__.py - 模型导出
- T009: models/user.py - User 模型（含同意字段）
- T010: models/measurement.py - Measurement 模型
- T011: models/session.py - ScanSession 模型
- T012: models/metric.py - MeasurementMetric 模型

### 数据模型规范
参考: .specify/specs/faster-3d-body-measurement-api/data-model.md

### 验收标准
- 所有模型可序列化/反序列化
- 字段验证正确
- 类型注解完整
```

### Issue #10: T013 配置管理
**Labels**: phase-2, backend
**Milestone**: Phase 2: Foundational

```markdown
## T013: 配置管理

**文件路径**: backend/src/config.py

### 任务描述
实现配置加载：
- API_KEY
- REDIS_URL
- INFLUXDB_URL, INFLUXDB_ORG, INFLUXDB_BUCKET, INFLUXDB_TOKEN
- MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
- OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME

### 验收标准
- 环境变量正确加载
- 配置验证通过
- 敏感信息不泄露
```

### Issue #11: T014-T015 可观测性
**Labels**: phase-2, backend, observability
**Milestone**: Phase 2: Foundational

```markdown
## T014-T015: 可观测性基础设施

**文件路径**: backend/src/observability/

### 任务描述
- T014: observability/tracing.py - OpenTelemetry 追踪配置
- T015: observability/metrics.py - Prometheus 指标

### 验收标准
- Trace 可正常上报
- 指标可采集
- 与 Jaeger/Prometheus 集成
```

### Issue #12: T016 异常处理
**Labels**: phase-2, backend
**Milestone**: Phase 2: Foundational

```markdown
## T016: 异常处理

**文件路径**: backend/src/exceptions.py

### 任务描述
创建基础异常类：
- FitScanException (基类)
- AuthenticationError
- AuthorizationError
- NotFoundError
- ValidationError
- ProcessingError

### 验收标准
- 异常可正确抛出
- HTTP 状态码映射正确
- 错误响应格式统一
```

### Issue #13: T017-T018 安全
**Labels**: phase-2, backend, security
**Milestone**: Phase 2: Foundational

```markdown
## T017-T018: 安全基础设施

**文件路径**: backend/src/security/

### 任务描述
- T017: security/auth.py - API Key 认证
- T018: security/privacy.py - 3D 数据脱敏（不可逆处理）

### 验收标准
- 认证中间件生效
- 未授权请求被拒绝
- 数据脱敏正确实现
```

### Issue #14: T019 存储客户端
**Labels**: phase-2, backend
**Milestone**: Phase 2: Foundational

```markdown
## T019: 存储客户端

**文件路径**: backend/src/storage/

### 任务描述
实现存储客户端：
- storage/__init__.py
- storage/influxdb.py - InfluxDB 时序数据客户端
- storage/minio.py - MinIO 对象存储客户端

### 验收标准
- 可写入/读取 InfluxDB
- 可上传/下载 MinIO 文件
- 连接池正常工作
```

### Issue #15: T020 依赖注入
**Labels**: phase-2, backend
**Milestone**: Phase 2: Foundational

```markdown
## T020: 依赖注入

**文件路径**: backend/src/api/deps.py

### 任务描述
创建 FastAPI 依赖注入：
- get_current_user()
- get_db()
- get_redis()
- get_influxdb()
- get_minio()

### 验收标准
- 依赖正确注入
- 单例模式正确
- 请求间隔离
```

---

## Milestone: Phase 3 - US1 实时3D扫描 (MVP)

### Issue #16: T021-T023 WebSocket 核心
**Labels**: phase-3, us1, backend, websocket
**Milestone**: Phase 3: US1 - 实时3D扫描

```markdown
## T021-T023: WebSocket 核心组件

**文件路径**: backend/src/websocket/

### 任务描述
- T021: websocket/manager.py - 连接管理器
- T022: websocket/protocol.py - 协议处理器
- T023: websocket/handler.py - 消息处理器

### 验收标准
- 支持多并发连接
- 消息正确路由
- 心跳保活正常
```

### Issue #17: T024-T025 WebSocket 端点
**Labels**: phase-3, us1, backend, websocket
**Milestone**: Phase 3: US1 - 实时3D扫描

```markdown
## T024-T025: WebSocket 端点

**文件路径**: backend/src/websocket/serializer.py, backend/src/api/routes/websocket.py

### 任务描述
- T024: websocket/serializer.py - Protobuf 序列化
- T025: api/routes/websocket.py - /ws/scan/{session_id} 端点

### 验收标准
- WebSocket 连接建立
- Protobuf 消息正确解析
- Session 验证通过
```

### Issue #18: T026-T028 计算隔离
**Labels**: phase-3, us1, backend, worker
**Milestone**: Phase 3: US1 - 实时3D扫描

```markdown
## T026-T028: 3D 计算任务

**文件路径**: backend/src/worker/

### 任务描述
- T026: worker/tasks.py - Celery 任务定义
- T027: worker/processor.py - ProcessPoolExecutor 隔离
- T028: worker/processor.py - 测量计算逻辑（stub）

### 验收标准
- 任务入队/执行正常
- 计算不阻塞 WebSocket
- Trace ID 连续传递
```

### Issue #19: T029-T030 REST 端点
**Labels**: phase-3, us1, backend, api
**Milestone**: Phase 3: US1 - 实时3D扫描

```markdown
## T029-T030: REST API 端点

**文件路径**: backend/src/api/routes/

### 任务描述
- T029: routes/sessions.py - POST /api/v1/sessions
- T030: routes/measurements.py - GET /api/v1/measurements/{id}

### 验收标准
- 端点正确响应
- 数据验证通过
- 错误处理完善
```

### Issue #20: T031-T034 US1 完善
**Labels**: phase-3, us1, backend
**Milestone**: Phase 3: US1 - 实时3D扫描

```markdown
## T031-T034: US1 完善

### 任务描述
- T031: WebSocket 心跳机制
- T032: Trace ID 传播
- T033: WebSocket 错误处理
- T034: Session 状态机

### 验收标准
- 连接稳定
- 错误友好提示
- 状态流转正确
```

---

## Milestone: Phase 4 - US2 离线文件处理

### Issue #21: T035-T036 文件解析
**Labels**: phase-4, us2, backend
**Milestone**: Phase 4: US2 - 离线文件处理

```markdown
## T035-T036: 文件解析

**文件路径**: backend/src/utils/file_parser.py, backend/src/api/routes/upload.py

### 任务描述
- T035: utils/file_parser.py - glTF/glb 解析
- T036: api/routes/upload.py - 文件验证

### 验收标准
- 支持 glTF/glb 格式
- 文件大小限制生效
- 格式错误友好提示
```

### Issue #22: T037-T039 上传端点
**Labels**: phase-4, us2, backend
**Milestone**: Phase 4: US2 - 离线文件处理

```markdown
## T037-T039: 上传端点

**文件路径**: backend/src/api/routes/upload.py, backend/src/worker/tasks.py

### 任务描述
- T037: POST /api/v1/upload/glb
- T038: 文件处理 Celery 任务
- T039: GET /api/v1/upload/{task_id}/status

### 验收标准
- 文件上传成功
- MinIO 存储正确
- 任务状态可查询
```

### Issue #23: T040-T042 US2 完善
**Labels**: phase-4, us2, backend
**Milestone**: Phase 4: US2 - 离线文件处理

```markdown
## T040-T042: US2 完善

### 任务描述
- T040: 进度跟踪
- T041: 文件大小限制 (100MB)
- T042: 错误处理

### 验收标准
- 进度实时更新
- 限制正确执行
- 错误信息友好
```

---

## Milestone: Phase 5 - US3 历史查询

### Issue #24: T043-T044 查询端点
**Labels**: phase-5, us3, backend
**Milestone**: Phase 5: US3 - 历史查询

```markdown
## T043-T044: 查询端点

**文件路径**: backend/src/api/routes/measurements.py

### 任务描述
- T043: GET /api/v1/measurements 分页
- T044: 日期范围过滤

### 验收标准
- 分页正确
- 过滤生效
- 排序正确
```

### Issue #25: T045-T047 分析功能
**Labels**: phase-5, us3, backend
**Milestone**: Phase 5: US3 - 历史查询

```markdown
## T045-T047: 分析功能

**文件路径**: backend/src/services/analytics.py, backend/src/storage/influxdb.py

### 任务描述
- T045: 趋势分析
- T046: InfluxDB 查询
- T047: Metrics 摘要

### 验收标准
- 趋势计算正确
- 时序数据可查询
- 摘要字段完整
```

---

## Milestone: Phase 6 - Polish

### Issue #26: T048-T050 优化
**Labels**: phase-6, polish, backend
**Milestone**: Phase 6: Polish

```markdown
## T048-T050: 跨领域优化

### 任务描述
- T048: Tail-based Sampling
- T049: GDPR 同意管理
- T050: InfluxDB 保留策略

### 验收标准
- 采样正确实现
- 同意管理合规
- 策略配置生效
```

### Issue #27: T051-T053 运维
**Labels**: phase-6, polish, backend, ops
**Milestone**: Phase 6: Polish

```markdown
## T051-T053: 运维完善

### 任务描述
- T051: 原始数据 7 天删除
- T052: DELETE /api/v1/measurements/{id}
- T053: 全局日志

### 验收标准
- 定时任务正常
- 删除功能完整
- 日志可追溯
```

### Issue #28: T054-T057 上线准备
**Labels**: phase-6, polish, backend
**Milestone**: Phase 6: Polish

```markdown
## T054-T057: 上线准备

### 任务描述
- T054: Nginx 速率限制
- T055: GET /health 健康检查
- T056: OpenAPI 文档
- T057: Quickstart 验证

### 验收标准
- 限流生效
- 健康检查正确
- 文档完整
- 快速入门可用
```

---

## Labels 说明

| Label | 用途 |
|-------|------|
| epic | 大功能集 |
| backend | 后端任务 |
| frontend | 前端任务 |
| phase-1 | 阶段1：初始化 |
| phase-2 | 阶段2：基础设施 |
| phase-3 | 阶段3：US1 |
| phase-4 | 阶段4：US2 |
| phase-5 | 阶段5：US3 |
| phase-6 | 阶段6：完善 |
| us1 | 用户故事1 |
| us2 | 用户故事2 |
| us3 | 用户故事3 |
| security | 安全相关 |
| observability | 可观测性 |
| infrastructure | 基础设施 |

## 批量创建命令

使用 GitHub CLI 批量创建：

```bash
# 设置仓库
REPO="cysyyds101/FitScan-1.0"

# 创建 milestone
gh issue create --repo $REPO --title "Phase 1: Setup" --body "项目初始化" --milestone "Phase 1"
# ... (重复创建所有 milestone)

# 批量创建 issues
gh issue create --repo $REPO --title "T001: 项目结构初始化" --body "$(cat issue-t001.md)" --label "phase-1,backend" --milestone "Phase 1"
# ... (重复所有 issue)
```
