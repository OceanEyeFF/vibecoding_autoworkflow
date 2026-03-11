# 已归档的设计基线文档

## 归档原因

本目录包含 IDEA-001 至 IDEA-004 的历史设计文档。这些设计基于以下假设：
- Agent 可以像函数一样被嵌套调用
- 存在运行时 Orchestrator 解析 JSON 命令
- 可以强制验证 Agent 输出的 Schema

经验证，这些假设与 **ClaudeCode 的实际工作流程不兼容**。

---

## 归档文档列表

### [IDEA-001: SubAgent 调用机制](./IDEA-001-subagent-call-mechanism.md)
- **原设计**：Agent 通过输出 `CALL_SUBAGENT` JSON 触发子 Agent
- **不可行原因**：
  - ClaudeCode 无运行时 Orchestrator 解析 JSON 命令
  - Agent 是独立会话，无法嵌套调用
- **可行替代方案**：
  1. 使用 Skill 作为 Orchestrator 顺序调用多个 Agent
  2. 通过 `.agent-handoff/` 目录交换结构化数据，用户手动触发
  3. 单 Agent 多阶段模式（如 feature-shipper 的 5-Phase 闭环）

### [IDEA-002: Agent 边界定义](./IDEA-002-agent-boundary-definition.md)
- **原设计**：Agent 输出 `BOUNDARY_VIOLATION` JSON 强制边界检查
- **不可行原因**：
  - 无运行时解析 JSON 命令的能力
  - 边界检查只能靠 Prompt 约束，无法技术性强制
- **可行替代方案**：
  1. 在 Prompt 中明确"我做什么/我不做什么"
  2. 遇到边界外任务时，使用 `AskUserQuestion` 工具询问用户
  3. 通过 Skill 编排明确划分职责

### [IDEA-003: 鉴权 Agent（Permission-Guard）](./IDEA-003-permission-guard-agent.md)
- **原设计**：独立的 permission-guard Agent 进行鉴权
- **不可行原因**：
  - permission-guard 无法被其他 Agent "调用"
  - 需要运行时解析 `PERMISSION_REQUEST` JSON
- **可行替代方案**：
  1. 使用 Git Hooks（pre-commit, pre-push）强制检查
  2. 在 Agent Prompt 中添加"敏感操作提示"，主动告知用户
  3. 通过 Soft Lock 机制（如 .autoworkflow/.owner）防止并发冲突

### [IDEA-004: 结构化交互协议](./IDEA-004-structured-interaction-protocol.md)
- **原设计**：所有 Agent 强制输出统一 JSON Schema
- **不可行原因**：
  - ClaudeCode 没有 Schema 验证机制
  - LLM 输出格式无法强制，只能通过 Prompt 鼓励
- **可行替代方案**：
  1. 在 Prompt 中提供详细的 JSON 示例（Examples as Constraints）
  2. 对于 Agent 间协作，使用约定的文件格式（如 .agent-handoff/*.json）
  3. 部分实现：部分 Agent（如 code-debug-expert, code-analyzer 等）采用 JSON 示例作为输出约束

---

## 设计对照表

| 原设计（归档） | 依赖假设 | 可行替代方案 | 实施状态 |
|-------------|---------|------------|---------|
| CALL_SUBAGENT JSON | 运行时调用 | Skill 编排 / 文件交换 | ✅ autodev Skill 已实现 |
| BOUNDARY_VIOLATION JSON | 运行时解析 | AskUserQuestion | ⚠️ 部分 Agent 使用 |
| permission-guard Agent | Agent 调用 Agent | Git Hooks + Prompt 提醒 | ⚠️ Soft Lock 已实现 |
| 强制 Schema 验证 | 运行时验证 | Prompt 示例引导 | ⚠️ 新 Agent 已采用 |

---

## 关键经验教训

### ❌ 不要依赖的机制
- **Agent 嵌套调用**（不是函数调用）
- **运行时解析 JSON 命令**（没有 Orchestrator）
- **强制 Schema 验证**（LLM 输出不受控）

### ✅ 应该依赖的机制
- **文件作为数据交换**（.agent-handoff/, state.md）
- **AskUserQuestion 作为决策点**（让用户参与）
- **Skill 作为工作流编排**（顺序调用多个 Agent）
- **Git Hooks 作为安全防护**（外部脚本强制检查）
- **TodoWrite 作为进度追踪**（可视化多阶段流程）

---

## 参考资料

- [当前可行的协作方案](../README.md#clauecode-兼容的协作方案)
- [IDEA-006: 强制数据访问机制](../IDEA-006-mandatory-data-access.md)（已成功实施）
- [autodev Skill 实现](../../../toolchain/skills/aw-kernel/autodev/)
- [feature-shipper Agent](../../../toolchain/agents/aw-kernel/feature-shipper.md)（5-Phase 闭环示例）

---

> **归档日期**：2026-01-04
> **归档原因**：设计不兼容 ClaudeCode 实际工作流程
> **保留价值**：作为历史参考，避免重复探索不可行方案
