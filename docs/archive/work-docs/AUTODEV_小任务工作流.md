---
title: "AUTODEV 小任务工作流"
status: archived
updated: 2026-03-17
owner: aw-kernel
last_verified: 2026-03-17
---
# AUTODEV 小任务工作流

> **版本**：v1.1 (合并版)
> **最后更新**：2026-01-16
> **维护者**：浮浮酱
> **文档级别**：L1 (选读)
> **何时读**：需要理解小任务自动化工作流设计、实施 Hooks 系统、或创建产物模板时
> **何时不读**：执行具体任务时（请读 Agent 文档或 Skill 文档）
> **阅读时长**：15-20 分钟

---

## 📖 使用指南

本文档是 `AUTODEV_小需求更稳.md` 与 `AUTODEV_实施参考.md` 的合并版，包含：

**Part 1：工作流设计**（原"小需求更稳"）
- 设计理念与目标
- 角色职责定义（2-3-1编排）
- 工作流阶段与门禁标准
- 失败回路机制

**Part 2：实施参考**（原"实施参考"）
- Hooks 系统设计
- 产物模板
- 门禁脚本示例
- 失败模式清单

---

## Part 1：工作流设计

### 0. 快速理解（10秒版）

**一句话总结**：入口规模 Gate + 需求2/实现3/交付1 + 证据型交付 = 小需求更稳

**适用范围**：单个小需求/小任务（建议 0.5～2 小时可闭环交付）

**核心理念**：
- 大任务挡在入口处（规模过大→拒绝/拆分）
- 不确定性前移量化（需求段固化为契约）
- 从"口头通过"到"证据通过"（实现段产出最小证据集）
- 职责单一（避免自证闭环）

**非目标**：不追求覆盖大项目（大任务先拆分为多个小需求）

---

### 1. 为什么需要"小需求更稳"

#### 1.1 观察到的问题

- 小需求本应更容易做好：上下文少、边界清晰、验证成本低
- 当前主要问题：**缺少可验证契约、强制门禁、证据交付、修复闭环**
- 问题后置：缺陷在后段才暴露，返工成本被放大

> 详细失败模式分析：见 `docs/knowledge/analysis/autodev-insights.md`

#### 1.2 设计目标（面向"稳"）

| 目标 | 手段 | 效果 |
|------|------|------|
| **把大任务挡在入口** | 规模 Gate（SizeScore） | 过大→拒绝/拆分，不进默认路径 |
| **把不确定性前移** | 需求契约（约束/验收/验证方法） | 实现前固化可验证标准 |
| **从口头到证据** | 最小证据集（三件套） | 可复现、可审计 |
| **职责单一** | 2-3-1 角色编排 | 避免"自产自证自宣称" |

#### 1.3 非目标（避免过度设计）

- ❌ 不追求覆盖所有大项目形态（大任务→拆分后多轮小需求）
- ❌ 不追求增加无限 Agent（以最少角色达到可审计与可复现）
- ❌ 不追求多里程碑规划（规模过大由入口 Gate 拆分解决）

---

### 2. 工作流结构

```
用户请求
    ↓
G0 规模Gate (Size Check)
    ├─ 超限 → 拒绝/拆分指引/LLM辅助分解
    └─ 通过 → Phase 1
         ↓
Phase 1: 需求分析（Spec Owner）
    输出: Requirement Contract
    ↓
G1 门禁: DoD 检查 (Requirement Verifier)
    ├─ 失败 → Level 2 回路（需求重构）
    └─ 通过 → Phase 2
         ↓
Phase 2: 任务规划（Dev Planner）
    输出: Task Plan
    ↓
G2 门禁: 计划检查 (Requirement Verifier)
    ├─ 失败 → Level 2 回路
    └─ 通过 → 创建检查点（可选） → Phase 3
         ↓
Phase 3: 实现（Dev Implementer）
    输出: Code + Tests + Evidence
    ↓
G3 门禁: 测试+Lint+Format
    ├─ 失败 → Level 1 回路（任务级迭代）
    │         ├─ 连续失败 → Level 2 回路（计划重构）
    │         └─ 严重失败 → Level 3 回路（需求重审）
    └─ 通过 → Phase 4
         ↓
Phase 4: 交付（Deliverer）
    输出: 最小证据集（运行日志 + 覆盖报告 + 变更摘要）
```

---

### 3. 角色职责定义（2-3-1 编排）

#### 角色列表

| 角色 | 阶段 | 核心职责 | 禁止事项 |
|------|------|---------|----------|
| **Spec Owner** | Phase 1 | 需求分析、DoD 固化 | 不得实现代码、不得自证 DoD |
| **Requirement Verifier** | G1/G2 | 验证需求契约与计划 | 不得修改需求/计划 |
| **Dev Planner** | Phase 2 | 任务拆解、依赖分析 | 不得实现代码 |
| **Dev Implementer** | Phase 3 | 实现代码、单元测试 | 不得修改需求/计划 |
| **Deliverer** | Phase 4 | 产出证据、归档交付 | 不得修改代码 |

#### 2-3-1 编排说明

- **2个前置角色**（Spec Owner + Requirement Verifier）：确保需求契约可验证
- **3个执行角色**（Dev Planner + Dev Implementer + Gate）：规划→实现→门禁
- **1个收尾角色**（Deliverer）：产出证据、归档交付

---

### 4. 阶段详细说明

#### Phase 1: 需求分析（Spec Owner）

**输入**：用户请求（已通过 G0 规模检查）

**输出**：Requirement Contract (YAML/JSON)
```yaml
requirement_id: req-001
summary: "功能描述（1句话）"
constraints:
  - "约束1（技术/资源/时间）"
  - "约束2"
dod:  # Definition of Done（验收标准）
  - "可验证条件1"
  - "可验证条件2"
verification_method:  # 验证方法
  - cmd: "npm test"
    expected: "所有测试通过"
  - cmd: "npm run lint"
    expected: "无 Lint 错误"
estimated_size: small  # small/medium（large应被G0拒绝）
```

**工作流**：
1. 与用户澄清需求边界（使用 AskUserQuestion）
2. 确定约束条件（技术栈、时间、资源）
3. 固化 DoD（可验证、可测试）
4. 定义验证方法（命令+期望结果）
5. 提交到 G1 门禁

---

#### G1 门禁：DoD 检查（Requirement Verifier）

**检查项**：
1. ✅ DoD 是否可验证（有明确标准）
2. ✅ 验证方法是否可执行（命令可运行）
3. ✅ 约束条件是否合理（无冲突）
4. ✅ 范围是否明确（无模糊地带）

**通过**：→ Phase 2
**失败**：→ Level 2 回路（需求重构）

---

#### Phase 2: 任务规划（Dev Planner）

**输入**：Requirement Contract（已通过 G1）

**输出**：Task Plan (YAML/JSON)
```yaml
tasks:
  - id: task-1
    description: "任务描述"
    dependencies: []
    estimated_time: "30min"
    files: ["src/foo.ts"]
    tests: ["tests/foo.test.ts"]
  - id: task-2
    description: "任务描述"
    dependencies: ["task-1"]
    estimated_time: "45min"
    files: ["src/bar.ts"]
    tests: ["tests/bar.test.ts"]
```

**工作流**：
1. 分析需求，拆解为 2-5 个可并行任务
2. 标注依赖关系
3. 预估时间（总时间应 ≤2 小时）
4. 标注文件范围
5. 提交到 G2 门禁

---

#### G2 门禁：计划检查（Requirement Verifier）

**检查项**：
1. ✅ 任务拆解是否覆盖所有 DoD
2. ✅ 依赖关系是否合理（无循环）
3. ✅ 时间预估是否在范围内
4. ✅ 文件范围是否明确

**通过**：→ 创建检查点（可选）→ Phase 3
**失败**：→ Level 2 回路（计划重构）

**检查点创建**（可选）：
- 如果项目有 Git 历史：使用 `git stash` 或轻量 `git commit` 标记 Phase 2 检查点
- 用途：失败回路时可快速恢复到计划通过状态

---

#### Phase 3: 实现（Dev Implementer）

**输入**：Task Plan（已通过 G2）

**输出**：Code + Tests + Evidence

**工作流**：
1. 按 Task Plan 顺序实现代码
2. 为每个任务编写单元测试（覆盖率 ≥90%）
3. 提交到 G3 门禁

---

#### G3 门禁：测试+Lint+Format

**检查项**：
1. ✅ 所有测试通过
2. ✅ Lint 无错误
3. ✅ 代码格式化通过
4. ✅ 覆盖率 ≥90%

**通过**：→ Phase 4
**失败**：→ 失败回路
  - **Level 1 回路**（任务级迭代）：修复代码，重新提交 G3
  - **连续失败**（3次以上）：→ Level 2 回路（计划重构）
  - **严重失败**（需求理解错误）：→ Level 3 回路（需求重审）

---

#### Phase 4: 交付（Deliverer）

**输入**：通过 G3 的代码

**输出**：最小证据集（三件套）
1. **运行日志**（test/build/lint 命令输出）
2. **覆盖率报告**（coverage summary）
3. **变更摘要**（文件列表 + 关键变更说明）

**工作流**：
1. 收集 G3 门禁的运行日志
2. 生成覆盖率报告
3. 生成变更摘要（`git diff --stat` + 关键说明）
4. 归档到 `.autoworkflow/deliveries/`
5. 向用户报告交付完成

---

### 5. 失败回路机制

#### Level 1 回路：任务级迭代

**触发**：G3 失败（测试/Lint/Format 错误）

**操作**：
1. Dev Implementer 修复代码
2. 重新提交 G3
3. 最多允许 3 次迭代

**退出**：
- 成功：→ Phase 4
- 连续失败 3 次：→ Level 2 回路

---

#### Level 2 回路：计划重构

**触发**：
- G2 失败（计划不合理）
- G3 连续失败 3 次（计划有问题）

**操作**：
1. 如果有 Phase 2 检查点：恢复到检查点
2. Dev Planner 重新分析需求，重写 Task Plan
3. 提交到 G2 重新检查

**退出**：
- 成功：→ Phase 3
- 失败：→ Level 3 回路

---

#### Level 3 回路：需求重审

**触发**：
- G1 失败（需求契约不清晰）
- G3 严重失败（需求理解错误，如实现了错误功能）

**操作**：
1. Spec Owner 与用户重新澄清需求
2. 重写 Requirement Contract
3. 提交到 G1 重新检查

**退出**：
- 成功：→ Phase 2
- 失败：建议用户将任务拆分为更小的需求

---

### 6. 产物规范

所有产物存储在 `.autoworkflow/` 目录：

```
.autoworkflow/
├── requirements/        # Phase 1 产物
│   └── req-001.yaml
├── plans/              # Phase 2 产物
│   └── plan-001.yaml
├── deliveries/         # Phase 4 产物
│   ├── delivery-001-log.txt
│   ├── delivery-001-coverage.txt
│   └── delivery-001-summary.md
└── state.md            # 跨会话状态（Gate 结果、检查点）
```

---

## Part 2：实施参考

### 1. Hooks 系统设计

#### 1.1 钩子类型与用途

| 钩子类型 | 触发时机 | 典型用途 |
|---------|---------|---------|
| `PreAgentInvoke` | Agent 调用前 | 上下文注入、权限/能力检查 |
| `PostAgentInvoke` | Agent 调用后 | 结果验证、日志记录、指标更新 |
| `PreToolUse` | 工具使用前 | 参数校验、权限检查 |
| `PostToolUse` | 工具使用后 | 结果记录/缓存、变更追踪 |
| `OnError` | 错误发生时 | 错误报告、恢复建议 |
| `OnSessionStart` | 会话开始时 | 初始化、环境检查 |
| `OnSessionEnd` | 会话结束时 | 清理、归档、统计 |

#### 1.2 标准接口（建议）

**输入**（通过环境变量或 stdin）：
```json
{
  "agent_name": "spec-owner",
  "phase": "requirement",
  "context": {
    "project_root": "/path/to/project",
    "task_id": "task-001",
    "user_request": "..."
  }
}
```

**输出**（通过 stdout）：
```json
{
  "status": "success|failure|warning",
  "message": "...",
  "data": {}
}
```

#### 1.3 门禁 Hook 示例

**G1: DoD 检查 Hook**
```bash
#!/bin/bash
# .autoworkflow/hooks/g1-dod-check.sh

REQUIREMENT_FILE=".autoworkflow/requirements/req-001.yaml"

# 检查 DoD 是否可验证
if ! grep -q "dod:" "$REQUIREMENT_FILE"; then
  echo '{"status":"failure","message":"DoD 缺失"}'
  exit 1
fi

# 检查验证方法是否存在
if ! grep -q "verification_method:" "$REQUIREMENT_FILE"; then
  echo '{"status":"failure","message":"验证方法缺失"}'
  exit 1
fi

echo '{"status":"success","message":"DoD 检查通过"}'
exit 0
```

**G3: 测试+Lint+Format Hook**
```bash
#!/bin/bash
# .autoworkflow/hooks/g3-test-lint-format.sh

# 运行测试
if ! npm test; then
  echo '{"status":"failure","message":"测试失败"}'
  exit 1
fi

# 运行 Lint
if ! npm run lint; then
  echo '{"status":"failure","message":"Lint 失败"}'
  exit 1
fi

# 检查覆盖率
COVERAGE=$(npm run coverage | grep "All files" | awk '{print $10}')
if [ "${COVERAGE%\%}" -lt 90 ]; then
  echo "{\"status\":\"failure\",\"message\":\"覆盖率不足: $COVERAGE\"}"
  exit 1
fi

echo '{"status":"success","message":"G3 门禁通过"}'
exit 0
```

---

### 2. 产物模板

#### 2.1 Requirement Contract 模板

```yaml
# .autoworkflow/requirements/req-{id}.yaml
requirement_id: req-001
summary: |
  单行功能描述

constraints:
  - "技术约束（如：必须使用现有 API）"
  - "资源约束（如：不引入新依赖）"
  - "时间约束（如：2 小时内完成）"

dod:
  - "可验证条件1（如：新增单元测试覆盖率 ≥90%）"
  - "可验证条件2（如：所有现有测试通过）"
  - "可验证条件3（如：无 Lint 错误）"

verification_method:
  - cmd: "npm test"
    expected: "All tests passed"
  - cmd: "npm run lint"
    expected: "No lint errors"
  - cmd: "npm run coverage"
    expected: "Coverage ≥ 90%"

estimated_size: small  # small/medium/large
created_at: "2026-01-16T10:00:00Z"
updated_at: "2026-01-16T10:00:00Z"
```

#### 2.2 Task Plan 模板

```yaml
# .autoworkflow/plans/plan-{id}.yaml
plan_id: plan-001
requirement_id: req-001
tasks:
  - id: task-1
    description: "实现核心功能"
    dependencies: []
    estimated_time: "30min"
    files:
      - "src/core.ts"
    tests:
      - "tests/core.test.ts"

  - id: task-2
    description: "添加集成测试"
    dependencies: ["task-1"]
    estimated_time: "20min"
    files:
      - "tests/integration.test.ts"
    tests:
      - "tests/integration.test.ts"

total_estimated_time: "50min"
created_at: "2026-01-16T11:00:00Z"
```

#### 2.3 Delivery Evidence 模板

```markdown
# .autoworkflow/deliveries/delivery-{id}-summary.md

## 交付摘要

**Requirement ID**: req-001
**Delivery Time**: 2026-01-16 12:00:00
**Status**: ✅ 成功

## 变更列表

### 新增文件
- `src/core.ts` (120 lines)
- `tests/core.test.ts` (80 lines)

### 修改文件
- `src/index.ts` (+15, -3)

## 测试结果

```
All tests passed (12/12)
Coverage: 95.3%
Lint: No errors
```

## 证据文件

- 运行日志：`delivery-001-log.txt`
- 覆盖率报告：`delivery-001-coverage.txt`
```

---

### 3. 失败模式清单

> 完整分析见 `docs/knowledge/analysis/autodev-insights.md`

#### 3.1 需求阶段失败模式

| 失败模式 | 表现 | 预防措施 |
|---------|------|---------|
| **模糊需求进入实现** | DoD 不可验证 | G1 强制检查 DoD 可测试性 |
| **范围蔓延** | 实现中不断增加需求 | Phase 1 固化边界，Phase 3 禁止修改需求 |
| **验证方法缺失** | 无法确定"何时算完成" | G1 强制要求 verification_method |

#### 3.2 规划阶段失败模式

| 失败模式 | 表现 | 预防措施 |
|---------|------|---------|
| **任务拆解过粗** | 单个任务 >1 小时 | G2 检查 estimated_time |
| **依赖循环** | 任务无法并行 | G2 检查依赖图 |
| **文件范围模糊** | 不知道改哪些文件 | 强制标注 files 字段 |

#### 3.3 实现阶段失败模式

| 失败模式 | 表现 | 预防措施 |
|---------|------|---------|
| **测试不足** | 覆盖率 <90% | G3 强制检查覆盖率 |
| **连续失败不回退** | 一直在 Level 1 循环 | 3 次失败自动触发 Level 2 回路 |
| **修改需求/计划** | 实现中偷偷改需求 | 职责分离（Implementer 不能改需求） |

#### 3.4 交付阶段失败模式

| 失败模式 | 表现 | 预防措施 |
|---------|------|---------|
| **证据不足** | 无法复现/审计 | Phase 4 强制产出三件套 |
| **口头宣称** | "我测过了" | 必须有运行日志 |
| **跨会话状态丢失** | 下次会话不知道进度 | state.md 持久化状态 |

---

### 4. 工具链集成

#### 4.1 .autoworkflow 目录初始化

```bash
# 初始化 .autoworkflow 目录结构
mkdir -p .autoworkflow/{requirements,plans,deliveries,hooks,tmp}
echo "# AutoWorkflow State" > .autoworkflow/state.md
```

#### 4.2 Git 集成

```bash
# 添加到 .gitignore
echo ".autoworkflow/tmp/" >> .gitignore
echo ".autoworkflow/state.md" >> .gitignore

# 或添加到 .git/info/exclude（不提交 .autoworkflow）
echo ".autoworkflow/" >> .git/info/exclude
```

#### 4.3 CI/CD 集成

```yaml
# .github/workflows/autoworkflow-gate.yml
name: AutoWorkflow Gate

on:
  pull_request:
    paths:
      - 'src/**'
      - 'tests/**'

jobs:
  g3-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm test
      - run: npm run lint
      - run: npm run coverage
      - name: Check Coverage
        run: |
          COVERAGE=$(npm run coverage | grep "All files" | awk '{print $10}')
          if [ "${COVERAGE%\%}" -lt 90 ]; then
            echo "Coverage insufficient: $COVERAGE"
            exit 1
          fi
```

---

## 附录

### A. 术语表

| 术语 | 含义 |
|------|------|
| **DoD** | Definition of Done，验收标准 |
| **G0/G1/G2/G3** | Gate 0/1/2/3，门禁检查点 |
| **Level 1/2/3 回路** | 失败回路层级 |
| **最小证据集** | 运行日志 + 覆盖率报告 + 变更摘要 |
| **2-3-1 编排** | 2个前置 + 3个执行 + 1个收尾角色 |

### B. 参考资料

- [分析精华](../../knowledge/analysis/autodev-insights.md) - 失败模式分析与改进抓手
- [当前 Agent / Skill 入口](../../interfaces/README.md) - 当前角色与接口入口
- [设计基线](../design/01_DesignBaseLines/autodev-architecture-v2.md) - 架构设计演进

---

**版本历史**：
- v1.0 (2026-01-13): 初始版本，分为两份文档
- v1.1 (2026-01-16): 合并版本，整合设计与实施参考

**维护者**：浮浮酱 ฅ'ω'ฅ
