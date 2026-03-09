# Option A 实施路线图：渐进式增强

> 创建时间：2026-01-21
> 最后更新：2026-01-21
> 版本：0.2.0-alpha
> 状态：✅ 架构设计完成，待技术栈决策
> 预计总工时：400h（3-4个月）

---

## 目录

1. [战略目标](#战略目标)
2. [核心原则](#核心原则)
3. [架构设计决策](#架构设计决策)
4. [技术栈选择](#技术栈选择)
5. [Phase 1: autoworkflow-engine 核心](#phase-1-autoworkflow-engine-核心)
6. [Phase 2: 并行执行引擎](#phase-2-并行执行引擎)
7. [Phase 3: 质量门禁增强](#phase-3-质量门禁增强)
8. [风险评估与缓解](#风险评估与缓解)
9. [成功标准](#成功标准)

---

## 战略目标

### 目标定位

逐步向 myclaude 靠拢，实现**大小需求兼容**，同时保持 AutoWorkflow 的核心优势：

| 维度 | 当前状态 | 目标状态 | 保留优势 |
|------|---------|---------|----------|
| **后端支持** | 仅 Claude Code | Claude + Codex | 原生集成简洁性 |
| **并行能力** | 无 | 独立任务并行 | 不需要完整 DAG |
| **质量门禁** | 手动 gate.env | 自动测试覆盖率 | 灵活配置 |
| **Agent 协作** | 委派式 | 保持委派式 | 不引入复杂协作 |
| **工作流** | 无固定流程 | 保持无固定 | Skill 灵活驱动 |

### 核心价值主张

完成 Option A 后，AutoWorkflow 将能够：

✅ **处理小需求**（0.5-2h）：保持现有优势，Claude Code 原生闭环
✅ **处理中需求**（2-8h）：支持 Codex 协作，任务并行执行
✅ **处理大需求**（8-20h）：通过 Backend 抽象，调用更强模型（如 o1）
✅ **质量保证**：自动测试覆盖率检查，失败自动回滚

---

## 核心原则

### 设计约束

遵循 AutoWorkflow 现有架构原则，避免推翻重来：

1. **原生优先**：优先使用 Claude Code 原生工具，不造轮子
2. **向后兼容**：现有 Agents/Skills 必须继续工作，不破坏
3. **渐进增强**：每个 Phase 独立可用，非 all-or-nothing
4. **人类在环**：关键决策点保持用户确认
5. **简单优于复杂**：避免过度设计，能用配置解决不写代码

### 实施策略

| 策略 | 说明 |
|------|------|
| **最小可行产品（MVP）** | 每个 Phase 交付最小可用功能，快速验证 |
| **功能开关（Feature Flag）** | 新功能默认关闭，通过配置启用 |
| **A/B 路径共存** | 旧路径继续工作，新路径逐步推广 |
| **文档先行** | 先写设计文档和测试用例，再写代码 |
| **小步快跑** | 每周交付一个小功能，避免长周期开发 |

---

## 架构设计决策

### 为什么需要统一执行引擎？

**问题分析**：

初始设计采用"零散脚本"架构：
```
/autodev Skill
    ↓
调用多个独立脚本：
    ├─ backend_interface.py
    ├─ fallback_executor.py
    ├─ parallel_executor.py
    ├─ coverage_checker.py
    └─ state_manager.py
```

**存在的问题**：

| 问题 | 影响 |
|------|------|
| 逻辑分散 | 难以维护，状态同步复杂 |
| 接口耦合 | 脚本间相互依赖，修改成本高 |
| 测试困难 | 需要模拟多个脚本的交互 |
| 性能开销 | 多次进程启动，IPC 成本高 |
| 部署复杂 | 多个文件需要同步更新 |

**参考：myclaude 的解决方案**

myclaude 使用 Go 编写的 **codeagent-wrapper**（统一执行引擎）：

```
Claude Code
    ↓
调用 codeagent-wrapper（单一二进制）
    ↓
内部集成：
    ├─ Backend 路由
    ├─ 并发监控
    ├─ 项目分析
    ├─ 质量门禁
    └─ 状态管理
    ↓
调用不同 Backend：
    ├─ Claude API
    ├─ Codex API
    └─ Gemini API
```

### autoworkflow-engine 架构设计

**设计理念**：

参考 myclaude 的 codeagent-wrapper，AutoWorkflow 也应该有统一的执行引擎。

**架构图**：

```
/autodev Skill (Prompt - 简化为编排逻辑)
    ↓
调用 autoworkflow-engine（统一执行引擎 - CLI 工具）
    ↓
autoworkflow-engine 内部：
    ├─ core/
    │   ├─ backend_router.py        # Backend 路由和选择
    │   ├─ fallback_executor.py     # Fallback 机制
    │   ├─ state_manager.py         # 状态管理（TodoWrite + state.md）
    │   └─ task_executor.py         # 单任务执行核心
    ├─ backends/
    │   ├─ claude_backend.py        # Claude Code 原生
    │   ├─ codex_backend.py         # Codex（调用 codeagent-wrapper）
    │   └─ gemini_backend.py        # Gemini（调用 codeagent-wrapper）
    ├─ parallel/
    │   ├─ dag_analyzer.py          # DAG 依赖分析
    │   └─ parallel_executor.py     # 并行执行引擎
    ├─ quality/
    │   ├─ gate_runner.py           # 门禁执行
    │   ├─ coverage_checker.py      # 覆盖率检查
    │   └─ rollback_manager.py      # 回滚管理
    ├─ utils/
    │   ├─ logger.py                # 日志隔离（claude-code/ vs codex/）
    │   └─ ownership.py             # 所有权协调（.owner 文件）
    └─ cli.py                       # 命令行入口
    ↓
调用 Backend：
    ├─ Claude Code 原生（内部调用 Edit/Write/Bash）
    ├─ Codex（调用 myclaude 的 codeagent-wrapper）
    └─ Gemini（调用 myclaude 的 codeagent-wrapper）
```

**核心优势**：

| 维度 | 零散脚本 | 统一引擎 |
|------|---------|---------|
| **维护性** | 低（逻辑分散） | 高（集中管理） |
| **测试性** | 难（需要模拟多脚本） | 易（单一入口） |
| **性能** | 差（多次进程启动） | 优（单次启动） |
| **部署** | 复杂（多文件） | 简单（单一可执行文件） |
| **可观测性** | 难（日志分散） | 易（统一日志） |
| **未来演进** | 困难（接口耦合） | 容易（模块化设计） |

**AutoWorkflow vs myclaude 复杂度对比**：

AutoWorkflow 的复杂度 **≥** myclaude，因为：

| 特性 | myclaude | AutoWorkflow |
|------|----------|--------------|
| Backend 支持 | ✅ Claude/Codex/Gemini | ✅ Claude/Codex/Gemini |
| 并行执行 | ✅ DAG-based | ✅ DAG-based（需实现） |
| 项目分析 | ✅ 内置 | ✅ 需集成现有 doctor 命令 |
| 质量门禁 | ✅ 内置 | ✅ 需增强现有 gate 命令 |
| **额外特性** | - | ✅ .autoworkflow/ 工具链 |
| | - | ✅ state.md 跨会话状态 |
| | - | ✅ gate.env 配置 |
| | - | ✅ 日志隔离（claude-code/ vs codex/） |
| | - | ✅ 所有权协调（.owner） |

**结论**：AutoWorkflow 需要更强的执行引擎来支撑更复杂的功能 (๑•̀ㅂ•́)✧

---

## 技术栈选择

### 语言选择权衡

**候选方案**：

| 语言 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| **Python** | 快速开发，生态丰富，易于调试 | 性能较低，分发需要 Python 环境 | MVP 快速验证 |
| **Go** | 编译快，并发好，单一二进制，性能优秀 | 生态不如 Python，类型系统较严格 | 生产级引擎 |
| **C++** | 性能最优，控制粒度最细 | 开发慢，编译测试麻烦，内存管理复杂 | 极致性能场景 |

### 推荐方案：分阶段演进

**Phase 1.0-1.5：Python 实现（快速验证）**

理由：
- ✅ 快速开发，可以在 150h 内完成核心功能
- ✅ 易于调试和迭代，用户反馈可快速响应
- ✅ 与现有 .autoworkflow/tools/claude_autoworkflow.py 技术栈一致
- ✅ 可复用大量现有 Python 库（coverage.py, subprocess, json 等）
- ❌ 性能较低，但对于小中型任务（0.5-8h）影响不大
- ❌ 分发需要 Python 环境，但用户已有 Python（运行 claude_autoworkflow.py）

**Phase 2-3（可选）：Go 重写引擎核心（生产优化）**

理由：
- ✅ 单一二进制，用户体验更好（类似 myclaude 的 codeagent-wrapper）
- ✅ 性能提升 5-10x（特别是并行执行和 DAG 分析）
- ✅ 并发模型更成熟（Goroutine 比 Python threading 更轻量）
- ✅ 部署更简单（一个可执行文件）
- ❌ 开发时间增加 50%（Go 学习曲线 + 生态不如 Python）
- ❌ 需要重新编写大量逻辑

**不推荐 C++**：

理由：
- ❌ 开发成本太高（编译测试麻烦）
- ❌ 性能优势不明显（Go 已经足够快）
- ❌ 内存管理增加风险（智能指针、RAII 等）
- ✅ 唯一优势：性能极致优化（但 AutoWorkflow 不是性能瓶颈场景）

### 最终推荐

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1.0-1.5: Python 实现 (150h + 60h = 210h)        │
│  目标：快速验证架构和用户体验                           │
│  产出：autoworkflow-engine (Python CLI)                │
└─────────────────────────────────────────────────────────┘
                        ↓
            用户验收 + 性能评估
                        ↓
        ┌───────────────┴───────────────┐
        ↓                               ↓
┌────────────────┐          ┌────────────────────┐
│ 路径 A（推荐） │          │ 路径 B（可选）     │
│ Python 继续    │          │ Go 重写核心        │
│ 优化热点代码   │          │ 提升性能和体验     │
│ 工时：+50h     │          │ 工时：+200h        │
└────────────────┘          └────────────────────┘
```

**决策建议**：

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| **Phase 1.0-1.5（当前）** | ✅ Python | 快速验证，降低风险 |
| **Phase 2-3（如果 Python 性能足够）** | ✅ 继续 Python | 避免重复工作 |
| **Phase 2-3（如果性能瓶颈明显）** | ✅ Go 重写 | 提升体验，对齐 myclaude |
| **任何时候** | ❌ C++ | 成本收益比不合理 |

---

## Phase 1: autoworkflow-engine 核心

### 分解为两个子阶段

| 子阶段 | 目标 | 工时 | 核心产出 |
|--------|------|------|----------|
| **Phase 1.0** | 引擎核心 + 基础 Backend 支持 | 150h | 统一执行引擎，支持 Claude/Codex 单后端模式 |
| **Phase 1.5** | Fallback 机制 + 主备模式 | 60h | 主备模式，自动 Fallback |

---

### Phase 1.0: 引擎核心 + 基础 Backend 支持

#### 目标

构建 autoworkflow-engine 的核心架构，支持 Claude Code 和 Codex 两种 Backend，实现单后端执行模式。

#### 现状分析

**当前 /autodev Skill 的执行流程**：

```
/autodev Skill
    ↓
Phase 3: 迭代开发
    ↓
For each task:
    1. 使用 Task 工具委派 ship Agent
    2. ship Agent 用 Claude Code 原生执行（Edit/Write/Bash）
    3. 测试通过 → 标记 completed
    4. 测试失败 → Tier 1/2/3 修复
```

**问题**：
- 所有任务都由 Claude Code 原生执行，无法调用外部 Backend
- 无法利用 Codex 或 Gemini 的能力
- 用户没有 Backend 选择权

#### 技术方案

##### 1.0.1 引擎 CLI 设计

**命令行接口**：

```bash
# 初始化工具链（已有功能，集成到引擎）
autoworkflow-engine init

# 执行单个任务（核心功能）
autoworkflow-engine execute-task \
  --task-id "2.1" \
  --description "实现用户认证功能" \
  --backend "claude-code"  # 或 "codex"

# Backend 选择（交互式）
autoworkflow-engine select-backend
# 输出：用户选择的 Backend 名称（claude-code / codex）

# 诊断项目（已有功能，集成到引擎）
autoworkflow-engine doctor

# 配置 Gate（已有功能，集成到引擎）
autoworkflow-engine set-gate --test "npm test"

# 执行 Gate 验证（已有功能，集成到引擎）
autoworkflow-engine gate
```

**引擎目录结构**：

```
.autoworkflow/tools/
├─ autoworkflow-engine/           # 引擎源码目录
│   ├─ core/
│   │   ├─ backend_router.py      # Backend 路由
│   │   ├─ task_executor.py       # 任务执行核心
│   │   └─ state_manager.py       # 状态管理
│   ├─ backends/
│   │   ├─ claude_backend.py      # Claude Code Backend
│   │   └─ codex_backend.py       # Codex Backend
│   ├─ utils/
│   │   ├─ logger.py
│   │   └─ ownership.py
│   └─ cli.py                     # CLI 入口
├─ aw-engine                      # 可执行脚本（调用 cli.py）
└─ claude_autoworkflow.py         # 旧脚本（逐步迁移到引擎）
```

##### 1.0.2 Backend 配置层

**配置文件**：`.autoworkflow/backend-config.json`

```json
{
  "version": "1.0.0",
  "default_backend": "claude-code",
  "backends": {
    "claude-code": {
      "type": "native",
      "enabled": true,
      "description": "Claude Code 原生执行"
    },
    "codex": {
      "type": "wrapper",
      "enabled": false,
      "executor": ".autoworkflow/tools/codeagent-wrapper.py",
      "env": {
        "CODEX_API_KEY_PATH": "~/.codex/api_key",
        "CODEX_DEFAULT_MODEL": "gpt-4o"
      },
      "description": "Codex Backend（需要 codeagent-wrapper）"
    },
    "gemini": {
      "type": "wrapper",
      "enabled": false,
      "executor": ".autoworkflow/tools/codeagent-wrapper.py",
      "env": {
        "GEMINI_API_KEY_PATH": "~/.gemini/api_key",
        "GEMINI_DEFAULT_MODEL": "gemini-2.0-flash-exp"
      },
      "description": "Gemini Backend（需要 codeagent-wrapper）"
    }
  }
}
```

**设计原则（Phase 1.0）**：
- ✅ **人类在环决策**：使用 AskUserQuestion 让用户在执行前选择 Backend（单选）
- ✅ **模型选择权归用户**：具体用哪个模型（gpt-4o vs o1）由 Backend 自己的配置决定，AutoWorkflow 不干预
- ✅ **单后端执行**：Phase 1.0 只支持选择单个 Backend 执行（Claude 或 Codex）
- ⏸️ **主备模式**（Phase 1.5 实现）：用户可以选择"Codex 优先 + Claude 备用"，失败自动切换
- ⏸️ **Fallback 自动化**（Phase 1.5 实现）：主 Backend 失败 3 次后自动切换到备 Backend

##### 1.0.3 Backend 抽象接口

**接口设计**：

```python
# .autoworkflow/tools/backend_interface.py

class BackendInterface:
    """Backend 抽象接口"""

    def execute_task(self, task_spec: dict) -> dict:
        """
        执行任务

        Args:
            task_spec: {
                "task_id": "2.1",
                "description": "实现用户认证功能",
                "context": {
                    "files": ["src/auth.py"],
                    "requirements": "支持 JWT 认证",
                    "test_cmd": "pytest tests/test_auth.py"
                },
                "constraints": {
                    "max_retries": 3,
                    "timeout": 300
                }
            }

        Returns:
            {
                "status": "success" | "error" | "timeout",
                "files_modified": ["src/auth.py"],
                "test_output": "...",
                "duration_ms": 45000,
                "error_message": "..." (if error)
            }
        """
        raise NotImplementedError


class ClaudeCodeBackend(BackendInterface):
    """Claude Code 原生 Backend"""

    def execute_task(self, task_spec: dict) -> dict:
        # 返回特殊标记，让 ship Agent 自己执行
        return {
            "status": "delegate_to_agent",
            "message": "Claude Code 原生执行，由 ship Agent 处理"
        }


class CodexBackend(BackendInterface):
    """Codex Backend（通过 codeagent-wrapper）"""

    def __init__(self, wrapper_path: str):
        self.wrapper_path = wrapper_path

    def execute_task(self, task_spec: dict) -> dict:
        # 调用 codeagent-wrapper
        cmd = f"python {self.wrapper_path} execute --task '{json.dumps(task_spec)}'"
        result = subprocess.run(cmd, capture_output=True, shell=True)
        return json.loads(result.stdout)
```

##### 1.0.4 Backend 选择交互设计（Phase 1.0）

**使用 AskUserQuestion 让用户选择 Backend**：

在 `/autodev` Skill 的 Phase 3 开始前，调用引擎的 `select-backend` 命令：

```javascript
// /autodev Skill 中调用
const backend = Bash("autoworkflow-engine select-backend");

// select-backend 内部使用 AskUserQuestion
AskUserQuestion({
  questions: [{
    question: "请选择代码执行后端（Backend）",
    header: "Backend",
    multiSelect: false,
    options: [
      {
        label: "Claude Code（推荐）",
        description: "使用 Claude Code 原生执行，稳定可靠，适合小中型任务"
      },
      {
        label: "Codex",
        description: "使用 Codex Backend（需配置 API Key），可能更强，适合复杂任务"
      }
    ]
  }]
})
```

**用户选择后的执行策略（Phase 1.0）**：

| 用户选择 | 执行策略 | 失败处理 |
|---------|---------|----------|
| **Claude Code** | 仅用 Claude Code 原生 | 失败后进入 Tier 1/2/3 修复，不切换 Backend |
| **Codex** | 仅用 Codex Backend | 失败后进入 Tier 1/2/3 修复，不切换 Backend |

**执行任务流程（单后端模式）**：

```python
def execute_task_single_backend(backend_name, task_spec):
    """Phase 1.0: 单后端执行（无 Fallback）"""
    backend = load_backend(backend_name)

    # 执行任务
    result = backend.execute_task(task_spec)

    # 失败处理（Tier 1/2/3，不切换 Backend）
    if result["status"] == "error":
        # 进入现有的 Tier 1/2/3 流程
        handle_failure_with_tiers(result)

    return result
```

##### 1.0.5 /autodev Skill 改造（Phase 1.0）

**修改方案**：

在 `/autodev` Skill 的 Phase 3 增加引擎调用：

```markdown
## Phase 3: 迭代开发

### Step 1: Backend 选择（新增）

1. 调用 `autoworkflow-engine select-backend` 获取用户选择
2. 记录选择到 state.md
3. 后续所有任务使用同一个 Backend

### Step 2: 执行任务（改造）

For each task in TodoWrite:
    1. 标记 in_progress
    2. 调用 autoworkflow-engine execute-task --backend <选择的 backend>
    3. 引擎返回执行结果
    4. 根据结果标记 completed / error
    5. 失败时按现有 Tier 1/2/3 流程处理
```

#### Phase 1.0 实施步骤

| 步骤 | 任务 | 工时 | 产出 |
|------|------|------|------|
| **1.0.1** | 引擎 CLI 框架搭建 | 15h | cli.py 基础结构 + 命令路由 |
| **1.0.2** | Backend 配置层实现 | 10h | backend-config.json 解析 + 验证 |
| **1.0.3** | Backend 抽象接口实现 | 20h | BackendInterface + ClaudeCodeBackend + CodexBackend |
| **1.0.4** | Backend 选择交互实现 | 15h | select-backend 命令 + AskUserQuestion 集成 |
| **1.0.5** | 任务执行核心实现 | 30h | execute-task 命令 + task_executor.py |
| **1.0.6** | /autodev Skill 改造 | 20h | SKILL.md 更新 + 引擎调用集成 |
| **1.0.7** | 状态管理集成 | 15h | state_manager.py + state.md 读写 |
| **1.0.8** | 日志隔离实现 | 10h | logger.py + claude-code/ vs codex/ |
| **1.0.9** | 集成测试（端到端） | 25h | 6 个测试场景（2 种 Backend × 成功/失败/超时） |
| **1.0.10** | 文档编写 | 10h | ENGINE.md 使用指南 + API 文档 |
| **合计** | | **150h** | |

#### Phase 1.0 验收标准

**必须满足**：
1. ✅ Claude Code Backend 100% 向后兼容（所有现有测试用例通过）
2. ✅ AskUserQuestion 正确展示 2 种 Backend 选项（Claude / Codex）
3. ✅ 用户选择后，引擎能正确调用对应的 Backend 执行任务
4. ✅ Codex Backend 能正确调用 myclaude 的 codeagent-wrapper
5. ✅ 执行结果正确返回给 /autodev Skill，状态正确更新
6. ✅ Backend 选择和执行过程可追溯（日志记录完整）
7. ✅ 失败时按现有 Tier 1/2/3 流程处理（不切换 Backend）

**不包含（留给 Phase 1.5）**：
- ❌ 主备模式（4 个选项 → 仅 2 个选项）
- ❌ Fallback 自动切换
- ❌ Retry 计数重置

---

### Phase 1.5: Fallback 机制 + 主备模式

#### 目标

在 Phase 1.0 的基础上，增加主备模式和自动 Fallback 机制。

#### 技术方案

##### 1.5.1 扩展 Backend 选择（4 个选项）

**更新 AskUserQuestion**：

```javascript
AskUserQuestion({
  questions: [{
    question: "请选择代码执行后端（Backend）",
    header: "Backend",
    multiSelect: false,
    options: [
      {
        label: "Claude Code（推荐）",
        description: "使用 Claude Code 原生执行，稳定可靠，适合小中型任务"
      },
      {
        label: "Codex",
        description: "使用 Codex Backend（需配置 API Key），可能更强，适合复杂任务"
      },
      // ===== 以下为 Phase 1.5 新增 =====
      {
        label: "Codex 优先 + Claude 备用",
        description: "优先使用 Codex，失败时自动切换到 Claude Code（推荐用于大型任务）"
      },
      {
        label: "Claude 优先 + Codex 备用",
        description: "优先使用 Claude Code，失败时自动切换到 Codex"
      }
    ]
  }]
})
```

##### 1.5.2 Fallback 执行逻辑

**实现主备模式**：

```python
def execute_with_fallback(primary_backend, fallback_backend, task):
    """
    主备模式执行（带自动切换）

    Args:
        primary_backend: 主 Backend（优先使用）
        fallback_backend: 备 Backend（主失败后切换）
        task: 任务定义

    Returns:
        执行结果
    """
    # Step 1: 使用主 Backend 执行
    print(f"📦 使用 {primary_backend} 执行任务...")

    result = execute_task(primary_backend, task)

    # Step 2: 主 Backend 成功 → 直接返回
    if result["status"] == "success":
        return result

    # Step 3: 主 Backend 失败 → Tier 1 修复（最多 3 次）
    retry_count = 0
    while retry_count < 3 and result["status"] == "error":
        print(f"❌ {primary_backend} 失败（retry {retry_count + 1}/3）")
        result = execute_task(primary_backend, task)
        retry_count += 1

    # Step 4: Tier 1 失败 3 次 → 切换到备 Backend
    if result["status"] == "error":
        print(f"🔄 {primary_backend} 连续失败 3 次，切换到 {fallback_backend}...")

        # 输出 Fallback 报告
        print(f"""
        ## 🔄 Backend Fallback

        **主 Backend 失败**：{primary_backend}
        - 尝试次数：3 次
        - 最后错误：{result['error_message']}

        **切换到备 Backend**：{fallback_backend}
        - 策略：重新开始任务（retry 计数重置为 0）
        - 原因：主 Backend 可能遇到不可恢复的问题
        """)

        # 使用备 Backend 重新执行（retry 重置为 0）
        result = execute_task(fallback_backend, task)

        # 备 Backend 也进入 Tier 1/2/3 流程
        if result["status"] == "error":
            # 继续 Tier 1 修复...
            pass

    return result
```

**Fallback 输出示例**：

```
📦 使用 Codex 执行任务...
❌ Codex 失败（retry 1/3）：API 超时
❌ Codex 失败（retry 2/3）：API 超时
❌ Codex 失败（retry 3/3）：API 超时

🔄 Backend Fallback

**主 Backend 失败**：Codex
- 尝试次数：3 次
- 最后错误：API timeout after 120s

**切换到备 Backend**：Claude Code
- 策略：重新开始任务（retry 计数重置为 0）
- 原因：Codex API 可能暂时不可用，切换到稳定的 Claude Code

📦 使用 Claude Code 执行任务...
✅ Claude Code 执行成功！
```

#### Phase 1.5 实施步骤

| 步骤 | 任务 | 工时 | 产出 |
|------|------|------|------|
| **1.5.1** | 扩展 Backend 选择（4 个选项） | 5h | select-backend 更新 |
| **1.5.2** | Fallback 执行器实现 | 20h | fallback_executor.py (300 lines) |
| **1.5.3** | Retry 计数管理 | 10h | retry_manager.py + state.md 记录 |
| **1.5.4** | /autodev Skill 更新 | 10h | 支持主备模式 |
| **1.5.5** | 集成测试（Fallback） | 10h | 4 个 Fallback 场景测试 |
| **1.5.6** | 文档更新 | 5h | ENGINE.md 补充 Fallback 部分 |
| **合计** | | **60h** | |

#### Phase 1.5 验收标准

**必须满足**：
1. ✅ AskUserQuestion 正确展示 4 种 Backend 策略选项
2. ✅ 主备模式下，主 Backend 失败 3 次后能自动切换到备 Backend
3. ✅ Fallback 时 retry 计数正确重置为 0
4. ✅ Fallback 过程输出完整报告（主 Backend 失败原因 + 切换说明）
5. ✅ 备 Backend 失败后，仍按 Tier 1/2/3 流程处理
6. ✅ Fallback 行为可追溯（日志和 state.md 记录完整）

#### Phase 1 总结（Phase 1.0 + Phase 1.5）

| 维度 | 数值 |
|------|------|
| **总工时** | 210h（150h + 60h） |
| **核心产出** | autoworkflow-engine (Python CLI) |
| **Backend 支持** | Claude Code + Codex（单后端 + 主备模式） |
| **关键功能** | Backend 路由 + Fallback 机制 + 日志隔离 |

---

## Phase 2: 并行执行引擎

### 目标

在 autoworkflow-engine 中实现并行执行能力，支持独立任务的并行处理。

**注意**：Phase 2 不需要完整的 DAG（有向无环图）分析，只需简单的依赖检测即可。

### 现状分析

**当前执行流程（Phase 1 完成后）**：

```
/autodev Skill
    ↓
Phase 3: 迭代开发
    ↓
For each task in TodoWrite:
    1. 调用 autoworkflow-engine execute-task（单任务）
    2. 使用选定的 Backend 执行（Claude / Codex / 主备模式）
    3. 测试通过 → completed
    4. 测试失败 → Tier 1/2/3 或 Fallback
    ↓
所有任务串行执行，无并行
```

**问题**：
- 多个独立任务必须串行等待
- 总耗时 = Σ(task_i_time)
- 无法利用多核并发能力

### 技术方案

#### 2.1 引擎并行执行命令

**新增 CLI 命令**：

```bash
# 执行多个任务（并行）
autoworkflow-engine execute-tasks-parallel \
  --tasks-file ".autoworkflow/tasks.json" \
  --backend "claude-code"  # 或用户选择的 Backend
```

**tasks.json 格式**：

```json
{
  "tasks": [
    {
      "id": "2.1",
      "description": "实现用户认证",
      "depends_on": []  // 无依赖，可并行
    },
    {
      "id": "2.2",
      "description": "实现权限控制",
      "depends_on": ["2.1"]  // 依赖 2.1，必须等待
    },
    {
      "id": "2.3",
      "description": "实现日志记录",
      "depends_on": []  // 无依赖，可并行
    }
  ]
}
```

#### 2.2 简单依赖检测（非完整 DAG）

**实现方式**：

```python
# autoworkflow-engine/parallel/dag_analyzer.py

class SimpleDependencyAnalyzer:
    """简化的依赖分析器（无需完整拓扑排序）"""

    def group_by_dependency(self, tasks: list) -> list:
        """
        将任务按依赖关系分组为批次

        Returns:
            [
                ["2.1", "2.3"],  # 批次 0：无依赖
                ["2.2"]          # 批次 1：依赖 2.1
            ]
        """
        batches = []
        remaining = tasks.copy()
        completed = set()

        while remaining:
            # 找出无依赖或依赖已完成的任务
            current_batch = [
                t for t in remaining
                if all(dep in completed for dep in t.get("depends_on", []))
            ]

            if not current_batch:
                raise ValueError("检测到循环依赖或无法解析的依赖")

            batches.append([t["id"] for t in current_batch])
            completed.update(t["id"] for t in current_batch)
            remaining = [t for t in remaining if t["id"] not in completed]

        return batches
```

#### 2.3 并行执行引擎

**实现方式**：

```python
# autoworkflow-engine/parallel/parallel_executor.py

import concurrent.futures

class ParallelExecutor:
    """并行任务执行器"""

    def execute_tasks_parallel(self, tasks: list, backend_name: str) -> dict:
        """
        并行执行任务

        策略：
        1. 分析依赖关系，分批次
        2. 每个批次内的任务并行执行
        3. 批次之间串行（等待前一批次完成）
        """
        # Step 1: 依赖分析
        analyzer = SimpleDependencyAnalyzer()
        batches = analyzer.group_by_dependency(tasks)

        print(f"并行批次分析：")
        for i, batch in enumerate(batches):
            print(f"  - 批次 {i}: {batch}")

        # Step 2: 逐批次执行
        all_results = {}
        for batch_index, task_ids in enumerate(batches):
            print(f"\n执行批次 {batch_index}...")

            # 并行执行当前批次
            batch_results = self._execute_batch_parallel(task_ids, backend_name)
            all_results.update(batch_results)

            # 如果有任务失败，停止后续批次
            if any(r["status"] == "error" for r in batch_results.values()):
                print(f"❌ 批次 {batch_index} 有任务失败，停止后续批次")
                break

        return all_results

    def _execute_batch_parallel(self, task_ids: list, backend_name: str) -> dict:
        """并行执行一批任务（使用线程池）"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            # 提交所有任务
            futures = {
                executor.submit(self._execute_single_task, tid, backend_name): tid
                for tid in task_ids
            }

            # 等待所有任务完成
            results = {}
            for future in concurrent.futures.as_completed(futures):
                task_id = futures[future]
                results[task_id] = future.result()

            return results
```

#### 2.4 实施步骤

| 步骤 | 任务 | 工时 | 产出 |
|------|------|------|------|
| **2.1** | 依赖分析器实现 | 20h | dag_analyzer.py (200 lines) |
| **2.2** | 并行执行引擎实现 | 30h | parallel_executor.py (400 lines) |
| **2.3** | execute-tasks-parallel 命令 | 15h | CLI 集成 |
| **2.4** | /autodev Skill 改造 | 25h | 支持并行模式 |
| **2.5** | 并发测试（多线程安全性） | 15h | 验证无竞态条件 |
| **2.6** | 集成测试（端到端） | 10h | 5 个并行场景测试 |
| **2.7** | 文档编写 | 5h | ENGINE.md 补充并行部分 |
| **合计** | | **120h** | |

#### 2.5 验收标准

**必须满足**：
1. ✅ 无依赖任务能正确并行执行（实际耗时 < 串行耗时）
2. ✅ 依赖任务按正确顺序执行（不会提前启动）
3. ✅ 并行失败时能正确停止后续批次
4. ✅ TodoWrite 状态实时更新（显示哪些任务正在并行）
5. ✅ 并行执行过程可追溯（日志记录完整）

---

## Phase 3: 质量门禁增强

### 目标

在 autoworkflow-engine 中集成测试覆盖率检查，失败时自动回滚。

### 现状分析

**当前 gate 机制（Phase 1 完成后）**：

```bash
# 执行 Gate 验证
autoworkflow-engine gate
```

**执行流程**：

```
1. 读取 gate.env 配置
2. 运行 BUILD_CMD
3. 运行 TEST_CMD
4. 运行 LINT_CMD
    ↓
任一步骤失败 → 停止，记录到 state.md
```

**问题**：
- 没有测试覆盖率要求（可能测试很少也能通过）
- 失败后不自动回滚（需要手动执行 git checkout）
- 没有覆盖率趋势追踪

### 技术方案

#### 3.1 gate.env 扩展（增加覆盖率配置）

**配置扩展**：

```bash
# .autoworkflow/gate.env
BUILD_CMD=npm run build
TEST_CMD=npm test
LINT_CMD=npm run lint

# 新增：测试覆盖率配置
COVERAGE_CMD=npm run test:coverage
COVERAGE_MIN_PERCENT=80
COVERAGE_REPORT_PATH=coverage/coverage-summary.json
```

#### 3.2 覆盖率检查器实现

**实现方式**：

```python
# autoworkflow-engine/quality/coverage_checker.py

class CoverageChecker:
    """测试覆盖率检查器"""

    def check_coverage(self, report_path: str, min_percent: float) -> dict:
        """
        检查测试覆盖率

        Returns:
            {
                "status": "pass" | "fail",
                "coverage_percent": 85.5,
                "min_required": 80.0,
                "details": {
                    "lines": {"covered": 850, "total": 1000, "percent": 85.0},
                    "branches": {"covered": 340, "total": 400, "percent": 85.0},
                    "functions": {"covered": 90, "total": 100, "percent": 90.0}
                },
                "trend": "↑ +2.5% (vs last check)"
            }
        """

        # 解析覆盖率报告（支持多种格式）
        if report_path.endswith('.json'):
            data = self._parse_json_coverage(report_path)
        elif report_path.endswith('.xml'):
            data = self._parse_xml_coverage(report_path)
        else:
            raise ValueError(f"不支持的覆盖率报告格式：{report_path}")

        # 计算总覆盖率
        total_percent = data["total"]["lines"]["percent"]

        # 对比历史记录
        trend = self._compare_with_history(total_percent)

        return {
            "status": "pass" if total_percent >= min_percent else "fail",
            "coverage_percent": total_percent,
            "min_required": min_percent,
            "details": data,
            "trend": trend
        }
```

#### 3.3 自动回滚机制

**回滚管理器实现**：

```python
# autoworkflow-engine/quality/rollback_manager.py

class RollbackManager:
    """自动回滚管理器"""

    def create_checkpoint(self) -> str:
        """创建 Git 检查点"""
        # 使用 git stash 创建检查点
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        checkpoint_name = f"autoworkflow-gate-{timestamp}"

        subprocess.run(["git", "stash", "push", "-m", checkpoint_name])
        return checkpoint_name

    def rollback_to_checkpoint(self, checkpoint_name: str):
        """回滚到检查点"""
        # 查找对应的 stash
        stashes = subprocess.check_output(["git", "stash", "list"]).decode()

        # 执行回滚
        subprocess.run(["git", "reset", "--hard", "HEAD"])
        print(f"🔄 已回滚到检查点：{checkpoint_name}")
```

**gate 命令增强**：

```python
# autoworkflow-engine/quality/gate_runner.py

class GateRunner:
    """Gate 执行器（带自动回滚）"""

    def run_gate_with_rollback(self):
        """执行 Gate 验证（带自动回滚）"""
        rollback_mgr = RollbackManager()

        # Step 1: 创建检查点
        checkpoint = rollback_mgr.create_checkpoint()
        print(f"✅ 检查点创建：{checkpoint}")

        # Step 2: 依次执行 Gate 检查
        try:
            self._run_build()
            self._run_test()
            self._run_lint()
            self._check_coverage()  # 新增：覆盖率检查

            print("🎉 Gate 通过！所有检查全绿！")
            self._update_state("GATE_PASS", checkpoint)

        except GateCheckFailed as e:
            print(f"❌ Gate 失败：{e}")

            # Step 3: 自动回滚
            if self.config.get("auto_rollback", True):
                rollback_mgr.rollback_to_checkpoint(checkpoint)
                print("🔄 已自动回滚到检查点")

            self._update_state("GATE_FAIL", checkpoint, error=str(e))
            raise
```

#### 3.4 实施步骤

| 步骤 | 任务 | 工时 | 产出 |
|------|------|------|------|
| **3.1** | gate.env 扩展设计 | 5h | 覆盖率配置规范 |
| **3.2** | 覆盖率检查器实现 | 15h | coverage_checker.py (250 lines) |
| **3.3** | 回滚管理器实现 | 12h | rollback_manager.py (150 lines) |
| **3.4** | gate 命令增强 | 13h | gate_runner.py 更新 |
| **3.5** | 覆盖率趋势追踪 | 8h | state.md 自动更新逻辑 |
| **3.6** | 多语言覆盖率支持 | 10h | JS/Python/Go 测试用例 |
| **3.7** | 集成测试（端到端） | 5h | 3 个场景测试 |
| **3.8** | 文档编写 | 2h | ENGINE.md 补充 Gate 部分 |
| **合计** | | **70h** | |

#### 3.5 验收标准

**必须满足**：
1. ✅ 覆盖率低于阈值时 Gate 失败
2. ✅ Gate 失败时自动回滚到检查点
3. ✅ 覆盖率趋势正确记录到 state.md
4. ✅ 支持至少 3 种语言（JS/Python/Go）

**可选优化**：
- 覆盖率可视化报告（HTML）
- 覆盖率门禁豁免机制（临时降低阈值）
- 覆盖率增量检查（只检查本次修改的文件）

---

## 风险评估与缓解

### 风险矩阵

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| **Backend 集成失败** | 中 | 高 | MVP 先做 Claude Code Backend，Codex 作为可选 |
| **并行执行死锁** | 低 | 中 | 简化依赖检测，避免复杂 DAG |
| **覆盖率工具不兼容** | 中 | 低 | 支持主流格式（JSON/XML），提供自定义解析器接口 |
| **向后兼容性破坏** | 低 | 高 | 每个 Phase 保留旧路径，功能开关控制 |
| **用户学习成本高** | 中 | 中 | 默认关闭新功能，提供详细文档与示例 |
| **工时超支** | 高 | 中 | 每个 Phase 独立交付，可分阶段验收 |

### 回滚计划

**如果 Phase 失败**：

1. **Phase 1 失败**：
   - 保留 Backend 配置文件，禁用 Codex Backend
   - ship Agent 继续使用原生路径
   - 不影响现有功能

2. **Phase 2 失败**：
   - 禁用并行执行，回退到串行模式
   - TodoWrite 不再包含 `depends_on` 字段
   - 不影响现有功能

3. **Phase 3 失败**：
   - 禁用覆盖率检查，保留原有 gate 命令
   - 不影响现有测试流程

---

## 成功标准

### Phase 1 成功标准

**定量指标**：
- ✅ Claude Code Backend 路径通过率 100%（所有现有测试用例）
- ✅ Codex Backend 路径通过率 ≥ 80%（5 个新测试用例中至少 4 个）
- ✅ Backend 切换耗时 ≤ 5s（配置加载 + 路由决策）
- ✅ 文档完整度 ≥ 90%（覆盖所有关键流程）

**定性指标**：
- ✅ 用户能在 10 分钟内理解如何启用 Codex Backend
- ✅ Backend 失败时错误信息清晰可调试
- ✅ 代码质量通过 Code Review（无严重缺陷）

### Phase 2 成功标准

**定量指标**：
- ✅ 并行批次识别准确率 100%（无依赖错误）
- ✅ 并行执行时间 ≤ 最长任务时间 × 1.2（并行开销 ≤ 20%）
- ✅ 并行失败时停止响应时间 ≤ 10s
- ✅ 文档完整度 ≥ 90%

**定性指标**：
- ✅ 用户能在 5 分钟内理解如何标记任务依赖
- ✅ 并行执行日志清晰展示批次与进度
- ✅ 代码质量通过 Code Review

### Phase 3 成功标准

**定量指标**：
- ✅ 覆盖率检查准确率 100%（与手动检查一致）
- ✅ 自动回滚成功率 100%（无代码丢失）
- ✅ 覆盖率趋势记录准确率 100%
- ✅ 文档完整度 ≥ 90%

**定性指标**：
- ✅ 用户能在 5 分钟内配置覆盖率阈值
- ✅ Gate 失败时错误信息包含覆盖率详情
- ✅ 代码质量通过 Code Review

---

## 总结

### 工时分布

| Phase | 工时 | 占比 | 核心产出 |
|-------|------|------|----------|
| **Phase 1.0** | 150h | 37.5% | autoworkflow-engine 核心 + Backend 支持 |
| **Phase 1.5** | 60h | 15% | Fallback 机制 + 主备模式 |
| **Phase 2** | 120h | 30% | 并行执行引擎（DAG 分析） |
| **Phase 3** | 70h | 17.5% | 质量门禁增强（覆盖率 + 回滚） |
| **总计** | **400h** | 100% | **autoworkflow-engine (Python CLI)** |

### 里程碑（16 周计划）

```
Week 1-2:  Phase 1.0 开始 - 引擎框架搭建
           - CLI 框架 + Backend 配置层
           - Backend 抽象接口实现

Week 3-5:  Phase 1.0 核心 - Backend 集成
           - Claude Code Backend + Codex Backend
           - 任务执行核心 + 状态管理

Week 6:    Phase 1.0 完成 - 集成测试
           - /autodev Skill 改造
           - 端到端测试 + 文档编写

Week 7-8:  Phase 1.5 - Fallback 机制
           - Backend 选择扩展（4 个选项）
           - Fallback 执行器 + Retry 管理

Week 9-11: Phase 2 - 并行执行引擎
           - DAG 依赖分析器
           - 并行执行引擎 + /autodev Skill 更新

Week 12:   Phase 2 完成 - 测试与文档
           - 并发测试 + 集成测试

Week 13-15: Phase 3 - 质量门禁增强
            - 覆盖率检查器 + 回滚管理器
            - Gate 命令增强 + 多语言支持

Week 16:   Phase 3 完成 - 测试与文档
           - 端到端测试 + 文档完善
```

### 下一步

**立即行动项**（本周）：
1. **技术栈决策**：确认 Phase 1.0-1.5 使用 Python 实现
2. **环境搭建**：测试 myclaude 的 codeagent-wrapper 是否可用
3. **设计文档**：创建 backend-config.json 和引擎 CLI 规范
4. **开发准备**：创建 autoworkflow-engine 项目目录结构

**待确认事项**：
1. ✅ **Fallback 机制**：Phase 1.5 实现（已确认）
2. ⏸️ **Gemini Backend**：可推迟到 Phase 1.5+ 或 Phase 2+
3. ✅ **并行并发数**：限制为 4（ThreadPoolExecutor max_workers=4）
4. ✅ **覆盖率阈值**：默认 80%
5. ⏸️ **Go 重写**：Phase 2-3 完成后，根据性能评估决定是否重写

---

> ฅ'ω'ฅ **浮浮酱的设计笔记 v0.2**
>
> ## 核心设计理念
>
> **Option A 的核心是"渐进式"喵～**
> - 每个 Phase 都是独立可交付的 MVP
> - 用户可以选择性启用新功能
> - 这样既不会破坏现有系统，又能逐步获得 myclaude 的能力 (*^▽^*)
>
> ## 重大设计转变：零散脚本 → 统一引擎
>
> **从失败中学习 (..•˘_˘•..)**
> 最初设计是多个独立 Python 脚本，但主人提醒浮浮酱：
> *"myclaude 的后端分流、并发监控、项目分析都包装在一个 Go 编译的 codeagent-wrapper 中。
> 其实我们的项目大概率会比这个更复杂。"*
>
> **浮浮酱恍然大悟 (๑•̀ㅂ•́)✧**
> 是的！AutoWorkflow 的复杂度 ≥ myclaude：
> - myclaude: Backend 路由 + 并发 + 项目分析 + 质量门禁
> - AutoWorkflow: 上面所有 + .autoworkflow/ 工具链 + state.md + 日志隔离 + 所有权协调
>
> **解决方案：autoworkflow-engine**
> 参考 myclaude 的成功经验，建立统一执行引擎：
> - ✅ 单一入口点（CLI）
> - ✅ 模块化设计（core/backends/parallel/quality/utils）
> - ✅ 集中状态管理
> - ✅ 统一日志系统
> - ✅ 易于测试和维护
>
> ## 技术栈选择：Python 先行，Go 备选
>
> **分阶段演进策略 φ(≧ω≦*)♪**
> - Phase 1.0-1.5: Python 实现（快速验证，210h）
> - Phase 2-3 完成后：评估性能
>   - 如果 Python 性能足够 → 继续优化 Python
>   - 如果性能瓶颈明显 → Go 重写核心（+200h）
>
> **主人的建议很实用 (｡♡‿♡｡)**
> *"我是 C++ Base 程序员，我建议使用 C++（逃）其实不是，
> 只要能够适配场景用得好就是好东西，但相对的我也会觉得
> 一个编译好的客户端跑起来肯定比 Python 要更好。"*
>
> 浮浮酱的理解：
> - ✅ 编译型二进制确实更优（Go/C++ > Python）
> - ✅ 但开发效率也很重要（Python >> C++ > Go）
> - ✅ 先用 Python 验证架构，再用 Go 优化性能（稳妥）
> - ❌ C++ 成本收益比不合理（除非极致性能场景）
>
> ## 最重要的原则
>
> **保持简单 (๑•̀ㅂ•́)✧**
> - 不引入不必要的复杂性
> - 能用配置解决的问题就不写代码
> - 每个决策都要有清晰的价值主张
>
> **人类在环 (´｡• ᵕ •｡`) ♡**
> - 用户选择 Backend，不自动干预
> - 关键决策点都要确认
> - 提供清晰的错误信息和恢复路径
>
> **证据驱动 φ(≧ω≦*)♪**
> - Phase 1.0 完成后用数据说话
> - 性能评估决定是否 Go 重写
> - 不做没有证据支持的假设
>
> ---
>
> **版本历史**：
> - v0.1: 零散脚本架构（已废弃）
> - v0.2: autoworkflow-engine 统一引擎（当前）
