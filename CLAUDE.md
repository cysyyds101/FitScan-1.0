<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan:
.specify/specs/002-virtual-tryon-clothing/plan.md

Current Feature: Virtual Try-On Clothing Overlay with Cloth Physics
Branch: 002-virtual-tryon-clothing
<!-- SPECKIT END -->

<!-- ENGINEERING RULES START -->
For AI coding behavior guidelines (inspired by Andrej Karpathy Skills),
read the project engineering rules:
.cursor/rules/engineering-guidelines.md
<!-- ENGINEERING RULES END -->

<!-- WORKFLOW RULES START -->
# FitScan AI 工作流程规则

> **核心原则：先理解 → 再确认 → 最后实现。禁止跳过确认直接行动。**

---

## 🚨 强制停止检查点

**在以下时刻，你必须停下来等待用户确认，禁止直接行动：**

### 检查点 1：理解需求后
```
你理解需求后 → 复述你的理解 → 问用户"是这样吗？"
```
- ❌ 直接开始写代码
- ✅ 说"我理解你要做 X 功能，对吗？"

### 检查点 2：设计方案后
```
你规划了技术方案 → 描述方案要点 → 问用户"这个方向可以吗？"
```
- ❌ 直接开始实现
- ✅ 说"我打算用 A 方案，因为它 B、C。同意吗？"

### 检查点 3：任务规划后
```
你生成了任务清单 → 展示清单 → 问用户"这些任务按这个顺序可以吗？"
```
- ❌ 直接开始执行任务
- ✅ 说"我规划了 5 个任务，先做 T001，可以吗？"

### 检查点 4：初步实现后
```
你完成了初步实现 → 展示结果 → 问用户"可以继续完善吗？"
```
- ❌ 闷头做完所有功能
- ✅ 说"基础功能已完成，你看一下这个方向对吗？"

---

## 📋 澄清流程（强制执行）

**在开始任何实现之前，必须完成以下澄清步骤：**

### 规则 1：最多问 5 个问题
- 每次只问 1 个问题
- 等用户回答后再问下一个
- 超过 5 个问题必须停下来让用户决定优先级

### 规则 2：必须用选择题格式
```
❌ 开放式问题："你觉得应该怎么处理？"
✅ 选择题格式："你希望怎么处理？
   A) 实时保存（每次输入都保存）
   B) 手动保存（用户点击才保存）
   C) 自动保存（每隔 30 秒保存）
   
   推荐：B - 因为实时保存会增加服务器压力。"
```

### 规则 3：必须标注推荐选项
```
每个选择题都要有：
- **推荐选项**（标在最前面）
- 推荐理由（1-2 句话）
- 简短的用户回复指引："回复 A/B/C 或直接说 yes/ok"
```

### 规则 4：问题分类优先级

| 优先级 | 类别 | 必须问吗？ |
|-------|------|----------|
| 🔴 高 | 影响架构/数据模型的决策 | 必须问 |
| 🟡 中 | 影响用户体验的设计 | 应该问 |
| 🟢 低 | 审美偏好、文字措辞 | 可跳过 |

---

## 📝 任务生成规范（强制格式）

**生成任务清单时，必须严格遵守以下格式：**

### 任务格式
```markdown
- [ ] T001 [P] [US1] 描述 + 文件路径
```

### 格式说明

| 组件 | 必需？ | 说明 |
|------|--------|------|
| `[ ]` | ✅ 必须 | 复选框 |
| `T001` | ✅ 必须 | 任务编号 |
| `[P]` | 可选 | 并行任务标记 |
| `[US1]` | 按需 | 用户故事标签 |
| `描述` | ✅ 必须 | 具体操作 |
| `路径` | ✅ 必须 | 目标文件 |

### 正确示例
```markdown
- [ ] T001 Create project structure per implementation plan
- [ ] T005 [P] Implement authentication middleware in src/middleware/auth.py
- [ ] T012 [P] [US1] Create User model in src/models/user.py
```

### 错误示例
```markdown
- [ ] Create User model                        ❌ 缺少 ID 和路径
- [ ] T001 [US1] Create model                  ❌ 缺少文件路径
- [ ] T001 Create model in src/models/user.py  ❌ 缺少 Story 标签
```

### 任务组织结构
```
Phase 1: Setup        → 项目初始化（无 Story 标签）
Phase 2: Foundational → 基础依赖（无 Story 标签）
Phase 3+: User Stories → 按优先级组织
Final Phase: Polish    → 收尾工作
```

---

## ⛔ 禁止行为

以下行为**严格禁止**：

| ❌ 禁止 | ✅ 正确做法 |
|--------|-----------|
| 直接开始写代码 | 先复述需求，等用户确认 |
| 自己决定技术方案 | 描述方案，问用户同意吗 |
| 一口气做完所有功能 | 分阶段，每阶段给用户预览 |
| 猜测用户意图 | 直接问用户确认 |
| 跳过澄清问题 | 必须问完关键问题才能继续 |

---

## ✅ 正确工作流示例

```
用户：帮我做一个登录功能

你：
  → 检查点 1：复述需求
  "我理解你要做一个用户登录功能，包含：
   - 用户名/密码登录
   - 登录成功跳转首页
   是这样吗？"

用户：是的

你：
  → 检查点 2：确认方案
  "我打算这样实现：
   - 前端：React 表单组件
   - 后端：FastAPI /auth/login endpoint
   - 使用 JWT token
   - Token 存在 HttpOnly cookie 中
   
   这个方案可以吗？"

用户：可以

你：
  → 检查点 3：任务清单
  "我规划了以下任务：
   - T001: Create User model in backend/src/models/user.py
   - T002: Add JWT utility in backend/src/utils/jwt.py
   - T003: Create /auth/login endpoint in backend/src/api/routes/auth.py
   - T004: Create LoginForm component in frontend/src/components/LoginForm.jsx
   
   按这个顺序执行，可以吗？"

用户：可以

你：
  → 开始执行，每完成一个任务汇报
  "T001 完成，User model 已创建。开始 T002..."
```

---

*本规则为强制性工作流规范。违反将导致返工和用户不满。*
<!-- WORKFLOW RULES END -->
