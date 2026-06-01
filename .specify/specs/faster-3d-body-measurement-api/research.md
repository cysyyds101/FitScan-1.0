# Research: FastAPI 3D 人体测量数据服务

**Generated**: 2026-05-26 | **Status**: Complete

## Research Questions & Findings

### RQ-001: FastAPI + WebSocket 非阻塞设计

**Decision**: FastAPI 原生 WebSocket 支持配合 Uvicorn ASGI 服务器

**Rationale**:
- FastAPI 的 WebSocket 实现基于 Starlette，原生支持异步处理
- Uvicorn 作为 ASGI 服务器支持 uvloop（Linux）或标准 asyncio
- 关键：3D 计算必须在独立 ProcessPoolExecutor 中执行，不阻塞事件循环

**Alternatives Considered**:
- Socket.IO: 过于重量级，增加不必要的抽象层
- aiohttp: 缺少 FastAPI 的自动 OpenAPI 文档优势

**Implementation Pattern**:
```python
# WebSocket handler - 永远不阻塞
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        async for message in websocket.iter_bytes():
            # 快速序列化后发送到任务队列，不做计算
            await task_queue.put(message)
            # 立即继续接收下一条消息
    except WebSocketDisconnect:
        pass

# 独立的计算进程
def process_3d_data(message: bytes):
    # 运行在 ProcessPoolExecutor 中
    result = compute_measurement(message)
    return result
```

---

### RQ-002: Protobuf vs MessagePack

**Decision**: Protobuf（主要）+ MessagePack（可选）

**Rationale**:
- **Protobuf**: 强类型定义，适合服务间通信，有代码生成支持
- **MessagePack**: 更简单，调试更方便，适合内部微调

**Alternatives Considered**:
- FlatBuffers: 极致性能但学习曲线陡峭
- Cap'n Proto: Rust 原生，性能优秀但 Python 支持一般

**Performance Comparison**:
| 序列化方式 | 3D 点云 (10K points) | 测量结果 JSON |
|------------|---------------------|---------------|
| JSON | ~50ms | ~1ms |
| Protobuf | ~5ms | ~0.2ms |
| MessagePack | ~8ms | ~0.3ms |

---

### RQ-003: Trace ID 在 ProcessPoolExecutor 中的连续性

**Decision**: 使用 contextvars + Uvicorn worker 隔离

**Rationale**:
- Python 3.7+ 的 contextvars 提供线程/进程安全的上下文存储
- FastAPI/Starlette 内部使用 contextvars 存储 request context
- 关键：在提交任务到进程池前，将 trace_id 显式传递

**Implementation Pattern**:
```python
from contextvars import ContextVar
from opentelemetry import trace

trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

async def websocket_handler(websocket: WebSocket):
    current_span = trace.get_current_span()
    trace_id = format_span_context(current_span.get_span_context())
    # 传递到任务参数中
    task = process_3d_data.delay(data, trace_id=trace_id)
```

---

### RQ-004: Tail-based Sampling

**Decision**: OpenTelemetry + custom tail sampler

**Rationale**:
- Head-based sampling（在请求开始时决定）无法捕获错误/慢请求
- Tail-based sampling（在请求结束时决定）可基于结果采样
- OpenTelemetry 支持自定义 Sampler 接口

**Implementation Pattern**:
```python
class TailBasedSampler(Sampler):
    def should_sample(self, parent_context, trace_id, ...):
        # 快速通过，让 tail sampler 决定
        return SamplingResult(Decision.RECORD_AND_SAMPLE)

class TailSampler:
    def __init__(self, sample_rate: float = 0.1):
        self.sample_rate = sample_rate

    def should_export(self, span: ReadableSpan) -> bool:
        # 始终保留错误和慢请求
        if span.status.code != StatusCode.OK:
            return True
        if span.end_time - span.start_time > 1000:  # > 1s
            return True
        # 随机采样正常请求
        return random.random() < self.sample_rate
```

---

### RQ-005: 存储方案选型

**Decision**: InfluxDB (时序) + MinIO (对象存储)

**InfluxDB 理由**:
- 专为时序数据优化，压缩率高
- 支持 DownSampling，自动聚合历史数据
- InfluxQL/Flux 查询语言适合测量数据

**MinIO 理由**:
- S3 兼容，迁移成本低
- 支持大文件（glTF/FBX 可达数百MB）
- 自我托管，无需云厂商依赖

**Alternatives Considered**:
- TimescaleDB: 更适合需要 SQL 的场景
- PostgreSQL + S3: 更简单但查询性能不如 InfluxDB

---

### RQ-006: GDPR 生物特征数据合规

**Decision**: 分层隐私保护策略

**Rationale**:
- GDPR Article 9 将生物特征数据列为"特殊类别数据"
- 需要明确的法律基础（同意或法律义务）
- 技术措施：加密存储 + 访问控制 + 数据最小化

**Implementation Requirements**:
1. **数据最小化**: 不存储完整3D模型，仅存储测量参数
2. **加密存储**: AES-256 加密静止数据
3. **访问日志**: 所有测量数据访问必须审计
4. **同意管理**: 独立的同意记录表，支持撤回
5. **删除权**: 支持数据完全删除（包括派生数据）

---

## Technology Stack Summary

| 类别 | 选型 | 版本 | 用途 |
|------|------|------|------|
| Web Framework | FastAPI | 0.110+ | API 开发框架 |
| ASGI Server | Uvicorn | 0.27+ | 异步服务器 |
| Task Queue | Celery | 5.3+ | 分布式任务队列 |
| Message Broker | Redis | 7+ | 消息队列后端 |
| Time-Series DB | InfluxDB | 2.7+ | 时序数据存储 |
| Object Storage | MinIO | RELEASE.2024+ | 文件存储 |
| Serialization | Protobuf | 4.25+ | 二进制协议 |
| Tracing | OpenTelemetry | 1.22+ | 全链路追踪 |
| Auth | python-jose | 3.3+ | JWT 令牌处理 |
| ORM | SQLAlchemy | 2.0+ | 关系数据（如需） |

---

## Risk Assessment

| 风险 | 影响 | 概率 | 缓解策略 |
|------|------|------|----------|
| WebSocket 连接不稳定 | 高 | 中 | 重连机制 + 心跳检测 |
| 3D 计算超时 | 中 | 中 | 超时中断 + 结果缓存 |
| Trace 数据量过大 | 中 | 高 | Tail Sampling 已纳入设计 |
| GDPR 合规风险 | 高 | 低 | 法律审查 + 技术措施 |
| 大文件上传内存溢出 | 高 | 低 | Nginx 限流 + 流式处理 |
