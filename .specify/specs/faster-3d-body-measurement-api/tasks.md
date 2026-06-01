# Tasks: FastAPI 3D 人体测量数据服务

**Input**: Design documents from `.specify/specs/faster-3d-body-measurement-api/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend directory structure per plan.md at backend/src/
- [ ] T002 Create __init__.py files for all Python packages
- [ ] T003 Create requirements.txt with dependencies: fastapi, uvicorn, websockets, celery, redis, influxdb-client, minio, opentelemetry-api, opentelemetry-sdk, protobuf, pydantic, python-jose, python-multipart
- [ ] T004 [P] Create protos/measurement.proto with ScanFrame, MeasurementResult, WSCommand, WSResponse messages
- [ ] T005 Create Dockerfile for backend service
- [ ] T006 Create docker-compose.yml with services: redis, influxdb, minio
- [ ] T007 Create nginx/conf.d/api.conf with rate limiting and WebSocket support

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 [P] Implement Pydantic models in backend/src/models/__init__.py
- [ ] T009 [P] Implement User model in backend/src/models/user.py with consent fields
- [ ] T010 [P] Implement Measurement model in backend/src/models/measurement.py
- [ ] T011 [P] Implement ScanSession model in backend/src/models/session.py
- [ ] T012 [P] Implement MeasurementMetric model in backend/src/models/metric.py
- [ ] T013 Create config.py with environment variable loading (API_KEY, REDIS_URL, INFLUXDB_URL, MINIO_*)
- [ ] T014 [P] Implement OpenTelemetry tracing setup in backend/src/observability/tracing.py
- [ ] T015 [P] Implement Prometheus metrics in backend/src/observability/metrics.py
- [ ] T016 Create base exception classes in backend/src/exceptions.py
- [ ] T017 [P] Implement API Key authentication in backend/src/security/auth.py
- [ ] T018 [P] Implement privacy/anonymization in backend/src/security/privacy.py (3D data irreversibility)
- [ ] T019 Create storage clients: backend/src/storage/__init__.py, influxdb.py, minio.py
- [ ] T020 Create dependency injection in backend/src/api/deps.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - 实时3D扫描与测量 (Priority: P1) MVP

**Goal**: WebSocket接收实时摄像头数据流，REST API返回测量结果，3D计算不阻塞消息循环

**Independent Test**: 模拟摄像头流并验证测量结果API返回完整数据

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement WebSocket Connection Manager in backend/src/websocket/manager.py
- [ ] T022 [P] [US1] Implement WebSocket Protocol Handler in backend/src/websocket/protocol.py
- [ ] T023 [P] [US1] Implement ScanFrame message handler in backend/src/websocket/handler.py
- [ ] T024 [US1] Implement Protobuf serialization utilities in backend/src/websocket/serializer.py
- [ ] T025 [US1] Implement WebSocket endpoint at /ws/scan/{session_id} in backend/src/api/routes/websocket.py
- [ ] T026 [US1] Implement Celery tasks architecture in backend/src/worker/tasks.py
- [ ] T027 [US1] Implement ProcessPoolExecutor isolation for 3D processing in backend/src/worker/processor.py
- [ ] T028 [US1] Implement measurement calculation logic stub in backend/src/worker/processor.py
- [ ] T029 [US1] Implement POST /api/v1/sessions endpoint in backend/src/api/routes/sessions.py
- [ ] T030 [US1] Implement GET /api/v1/measurements/{id} endpoint in backend/src/api/routes/measurements.py
- [ ] T031 [US1] Implement connection heartbeat mechanism in WebSocket manager
- [ ] T032 [US1] Add Trace ID propagation from WebSocket to Celery task (ProcessPoolExecutor isolation)
- [ ] T033 [US1] Add WebSocket error handling (disconnect, reconnection hints)
- [ ] T034 [US1] Add session state machine (pending → scanning → processing → completed)

**Checkpoint**: Real-time scanning should be functional - WebSocket receives data, processing happens in isolation, results available via REST API

---

## Phase 4: User Story 2 - 离线文件批量处理 (Priority: P2)

**Goal**: 上传glTF/FBX格式文件，系统自动解析并返回测量数据

**Independent Test**: 上传测试文件并验证处理结果

### Implementation for User Story 2

- [ ] T035 [P] [US2] Implement glTF/glb file parser utility in backend/src/utils/file_parser.py
- [ ] T036 [P] [US2] Implement file validation (size, format) in backend/src/api/routes/upload.py
- [ ] T037 [US2] Implement POST /api/v1/upload/glb endpoint with MinIO upload in backend/src/api/routes/upload.py
- [ ] T038 [US2] Implement file processing Celery task in backend/src/worker/tasks.py
- [ ] T039 [US2] Implement GET /api/v1/upload/{task_id}/status endpoint in backend/src/api/routes/upload.py
- [ ] T040 [US2] Implement progress tracking for offline processing in backend/src/worker/processor.py
- [ ] T041 [US2] Add file size limit enforcement (100MB) in upload endpoint
- [ ] T042 [US2] Add file format error handling with friendly messages

**Checkpoint**: File upload and processing should work independently of real-time scanning

---

## Phase 5: User Story 3 - 测量数据历史查询 (Priority: P3)

**Goal**: 查询用户历史测量记录，支持趋势分析

**Independent Test**: 查询历史API返回分页列表和趋势数据

### Implementation for User Story 3

- [ ] T043 [P] [US3] Implement GET /api/v1/measurements endpoint with pagination in backend/src/api/routes/measurements.py
- [ ] T044 [P] [US3] Implement date range filtering in measurements query
- [ ] T045 [US3] Implement measurement trend analysis in backend/src/services/analytics.py
- [ ] T046 [US3] Implement InfluxDB query for time-series measurement data
- [ ] T047 [US3] Add metrics summary field to measurement list response

**Checkpoint**: Historical query should work independently of scanning/upload features

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Implement Tail-based Sampling in backend/src/observability/tracing.py
- [ ] T049 [P] Implement GDPR consent management in backend/src/security/consent.py
- [ ] T050 [P] Add InfluxDB retention policy configuration
- [ ] T051 Implement data retention: auto-delete raw point cloud after 7 days
- [ ] T052 Implement measurement data deletion endpoint (DELETE /api/v1/measurements/{id})
- [ ] T053 Add comprehensive logging across all modules
- [ ] T054 [P] Implement API rate limiting in nginx/nginx.conf
- [ ] T055 Implement health check endpoint GET /health
- [ ] T056 Add API documentation with OpenAPI/Swagger
- [ ] T057 Validate quickstart.md scenarios work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase | Depends On | Blocking |
|-------|------------|----------|
| Setup (Phase 1) | None | - |
| Foundational (Phase 2) | Setup | ALL user stories |
| User Story 1 (Phase 3) | Foundational | - |
| User Story 2 (Phase 4) | Foundational | - |
| User Story 3 (Phase 5) | Foundational | - |
| Polish (Phase 6) | User Stories | - |

### User Story Dependencies

- **US1 (P1)**: Depends only on Foundational - no dependencies on US2/US3
- **US2 (P2)**: Depends only on Foundational - no dependencies on US1/US3
- **US3 (P3)**: Depends only on Foundational - no dependencies on US1/US2

### Within Each User Story

1. Models → Services → Endpoints
2. Core implementation before integration
3. Story complete before moving to next priority

---

## Parallel Opportunities

### Phase 2 (Foundational) - Tasks marked [P] can run in parallel:
- T008, T009, T010, T011, T012 (Pydantic models)
- T014, T015, T017, T018 (Observability & Security)

### Phase 3 (US1) - Tasks marked [P] can run in parallel:
- T021, T022, T023 (WebSocket components)
- T029, T030 (REST endpoints)

### Phase 4 (US2) - Tasks marked [P] can run in parallel:
- T035, T036 (File handling)
- T037, T038 (Upload + Processing)

### Phase 5 (US3) - Tasks marked [P] can run in parallel:
- T043, T044 (List query + filtering)

---

## Implementation Strategy

### MVP First (US1 Only)

```
1. Phase 1: Setup
2. Phase 2: Foundational (CRITICAL)
3. Phase 3: User Story 1
4. STOP and VALIDATE: Test real-time scanning independently
5. Deploy/demo if ready
```

### Incremental Delivery

```
1. Setup + Foundational → Foundation ready
2. US1 → Test independently → Deploy (MVP)
3. US2 → Test independently → Deploy
4. US3 → Test independently → Deploy
```

---

## Task Summary

| Phase | Task Count | User Story |
|-------|------------|------------|
| Phase 1: Setup | 7 | - |
| Phase 2: Foundational | 13 | - |
| Phase 3: US1 | 14 | 实时3D扫描 |
| Phase 4: US2 | 8 | 离线文件处理 |
| Phase 5: US3 | 5 | 历史查询 |
| Phase 6: Polish | 10 | - |
| **Total** | **57** | |

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- US1 is the MVP - focus there first for fastest value delivery
