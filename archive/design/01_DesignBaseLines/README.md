# Claude Code Agent 设计基线索引

> 创建时间：2024-12-31
> 最后更新：2026-01-11
> 状态：IDEA-006 已完成，IDEA-001~004 已归档

---

## 🔗 当前主线（SoT）

> 本目录是“设计基线/实现思想”的沉淀；与主线 SoT 冲突时，以根目录 SoT 为准。

- 协作基线：[`ClaudeCode协作最小共识_基准文本.md`](../../ClaudeCode协作最小共识_基准文本.md)
- 工作流结构与门禁：[`AUTODEV_小需求更稳流程设计.md`](../../AUTODEV_小需求更稳流程设计.md)
- 角色职责与产物契约：[`AUTODEV_小需求更稳_Agent全量定义.md`](../../AUTODEV_小需求更稳_Agent全量定义.md)
- 分析精华（失败模式与改进条目）：[`docs/analysis/autodev-insights.md`](../../docs/analysis/autodev-insights.md)
- 当前路线图：[`ROADMAP.md`](../../ROADMAP.md)

## 📦 归档说明

**2026-01-04 更新**：IDEA-001 至 IDEA-004 已归档至 [`archived/`](./archived/) 目录

**归档原因**：这些设计基于"运行时 Agent 调用"和"强制 Schema 验证"假设，与 ClaudeCode 实际工作流程不兼容。

**替代方案**：参见下方"[ClaudeCode 兼容的协作方案](#clauecode-兼容的协作方案)"章节。

**归档文件**：
- [IDEA-001: SubAgent 调用机制](archived/IDEA-001-subagent-call-mechanism.md)
- [IDEA-002: Agent 边界定义](archived/IDEA-002-agent-boundary-definition.md)
- [IDEA-003: 鉴权 Agent](archived/IDEA-003-permission-guard-agent.md)
- [IDEA-004: 结构化交互协议](archived/IDEA-004-structured-interaction-protocol.md)
- [归档索引](archived/README.md)（包含详细对照表和替代方案）

---

## 一、文档总览

| 编号 | 文档 | 优先级 | 关联问题 | 状态 | 备注 |
|------|------|-------|---------|------|------|
| IDEA-001 | [SubAgent 调用机制](archived/IDEA-001-subagent-call-mechanism.md) | - | P01 | 📦 已归档 | 不兼容 ClaudeCode，见[可行方案](#clauecode-兼容的协作方案) |
| IDEA-002 | [Agent 职责边界定义](archived/IDEA-002-agent-boundary-definition.md) | - | P02 | 📦 已归档 | 不兼容 ClaudeCode，见[可行方案](#clauecode-兼容的协作方案) |
| IDEA-003 | [鉴权 Agent 设计](archived/IDEA-003-permission-guard-agent.md) | - | P03 | 📦 已归档 | 不兼容 ClaudeCode，见[可行方案](#clauecode-兼容的协作方案) |
| IDEA-004 | [结构化交互协议](archived/IDEA-004-structured-interaction-protocol.md) | - | P04 | 📦 已归档 | 不兼容 ClaudeCode，见[可行方案](#clauecode-兼容的协作方案) |
| IDEA-005 | [本地化文档缓存](./IDEA-005-localized-instruction-cache.md) | P0 | P05 | 🔴 待实施 | 可行，待评估优先级 |
| IDEA-006 | [强制数据访问机制](./IDEA-006-mandatory-data-access.md) | P0 | P06 | ✅ 已完成 | 已广泛应用于 7 个 Agent |

---

## 二、ClaudeCode 兼容的协作方案

基于对 ClaudeCode 真实能力的理解，以下是可行的 Agent 协作方式：

### ✅ 已实施的协作机制

#### 1. **Skill 工作流编排**（已有实现）
- **`autodev` Skill**：需求→任务→迭代→交付全流程
- **`autodev-worktree` Skill**：Git Worktree 并行开发管理
- **位置**：`toolchain/skills/aw-kernel/`
- **优点**：用户一个命令即可启动完整工作流
- **实施状态**：✅ 生产可用

#### 2. **单 Agent 多阶段模式**（已有实现）
- **`ship`**：5-Phase 闭环 + 3层回路机制
  - Phase 0: 需求收敛
  - Phase 1: 需求分析/项目探查
  - Phase 2: 验收标准固化
  - Phase 3: 迭代开发 + G3测试门禁
  - Phase 4: 验收交付
- **每个阶段有明确的 Gate 检查点**
- **使用 TodoWrite 工具追踪进度**
- **实施状态**：✅ 生产可用

#### 3. **强制数据访问机制**（IDEA-006，已完成）
- **No Evidence, No Output 铁律**
- **已应用于全部 7 个生产 Agent**：
  - ship
  - clarify
  - review
  - debug (已删除)
  - logs
  - clean
  - knowledge-researcher
- **详见**：[IDEA-006-implementation/](./IDEA-006-implementation/)
- **实施状态**：✅ 广泛应用

### 🎯 未来可探索的方向

#### 1. **基于文件的 Agent 切换**
- 通过 `.agent-handoff/` 目录交换结构化数据
- 用户手动触发 SubAgent 或使用脚本简化
- **可行性**：高（完全兼容 ClaudeCode）
- **实施难度**：低（只需约定文件格式）

#### 2. **基于 AskUserQuestion 的边界管理**
- Agent 遇到边界外任务时，直接询问用户选择
- 不依赖运行时解析 JSON 命令
- **可行性**：高（已有部分 Agent 使用）
- **实施难度**：低（修改 Prompt 即可）

#### 3. **基于 Git Hooks 的安全控制**
- Pre-commit/Pre-push Hooks 强制检查
- Agent 通过 Prompt 提醒用户，而非强制阻塞
- **可行性**：高（Git Hooks 是成熟机制）
- **实施难度**：中（需编写 Hook 脚本）

#### 4. **统一 JSON 输出格式**（部分可行）
- 通过 Prompt 鼓励结构化输出
- 但无法强制验证，需人工审查
- **可行性**：中（4 个新 Agent 已采用）
- **实施难度**：低（修改 Prompt 和示例）

---

## 三、优先级分布（已调整）

### P0 级（必须优先解决）

| 编号 | 核心改进点 | 预期收益 | 状态 |
|------|-----------|---------|------|
| IDEA-005 | 核心指令外置 + 刷新机制 | 避免上下文污染 | 🔴 待评估 |
| IDEA-006 | 强制先访问数据 | 阻止幻觉输出 | ✅ 已完成 |

### P1 级（已归档，不再实施）

| 编号 | 原改进点 | 归档原因 |
|------|---------|---------|
| IDEA-001 | SubAgent 可被显式调用 | 不兼容 ClaudeCode 运行时 |
| IDEA-002 | 明确职责边界 | 无法技术性强制边界检查 |
| IDEA-003 | 鉴权 Agent | Agent 无法调用 Agent |
| IDEA-004 | 统一输出 Schema | 无法强制 Schema 验证 |

---

## 四、实际实施进展与后续计划

### ✅ 已完成（2026-01-04）
- **IDEA-006**：强制数据访问机制（No Evidence, No Output）
  - 应用于全部 7 个生产 Agent
  - 包含 3 层防守架构：
    - Layer 1: Prompt 纪律（自律约束）
    - Layer 2: 结构化输出（格式约束）
    - Layer 3: Hooks 验证（外部强制）
  - 详见：[IDEA-006-implementation/](./IDEA-006-implementation/)

### 🔄 当前状态
- **Agent 协作**：基于 Skill 编排（autodev, autodev-worktree）
- **边界管理**：通过 Prompt 约束 + AskUserQuestion
- **输出格式**：4 个新 Agent 已统一 JSON 输出（debug (已删除), review, clean, logs）
- **安全控制**：Soft Lock 机制（.autoworkflow/.owner）

### 🎯 后续优先级（按需评估）

#### 优先级 1：统一所有 Agent 输出格式
- **目标**：ship 和 clarify 采用 JSON 输出
- **参考**：debug (已删除) 的实现模式
- **预期收益**：提高 Agent 间协作的可靠性
- **实施难度**：低（修改 Prompt 和示例）

#### 优先级 2：评估 IDEA-005（本地化指令缓存）
- **目标**：研究长对话中的指令遗忘问题
- **方案**：考虑模块化 Prompt 结构
- **预期收益**：降低指令遗忘率
- **实施难度**：中（需设计缓存机制）

#### 优先级 3：探索基于文件的协作协议
- **目标**：定义 `.agent-handoff/` 目录结构
- **方案**：创建标准化的输入/输出 JSON Schema
- **预期收益**：Agent 间可靠的数据交换
- **实施难度**：中（需约定协议和文件格式）

---

## 五、关键设计理念（已调整）

### 5.1 从理想到务实

```
原设计（归档）                     当前可行方案
─────────────                    ─────────────
Agent 嵌套调用          →        Skill 工作流编排
CALL_SUBAGENT JSON      →        文件交换 + 用户触发
BOUNDARY_VIOLATION JSON →        AskUserQuestion
permission-guard Agent  →        Git Hooks + Prompt 提醒
强制 Schema 验证        →        Prompt 示例引导
```

### 5.2 从建议到强制（IDEA-006 已实现）

```
当前状态                          目标状态
─────────────                    ─────────────
"建议先查证后输出"       →       ✅ "无证据 = BLOCKED"
"可以写入 state.md"      →       ✅ "必须写入 + 刷新读取"
"遵循输出格式"           →       ⚠️ "Prompt 鼓励（无强制）"
```

### 5.3 从集中到分散（IDEA-005 待评估）

```
当前状态                          目标状态
─────────────                    ─────────────
236 行 Prompt            →       🔴 50 行 Prompt + 外置指令（待评估）
每次加载完整指令         →       🔴 按需加载 + 刷新机制（待评估）
上下文易污染             →       🔴 可恢复的指令记忆（待评估）
```

---

## 六、验收标准总览（已调整）

### 最终目标（基于可行方案）

- [x] **没有证据时输出 BLOCKED**（✅ IDEA-006 已完成）
- [ ] **基于 Skill 的工作流编排**（⚠️ autodev 已有，可扩展）
- [ ] **每个 Agent 有清晰的职责边界**（⚠️ 通过 Prompt 约束，无法技术强制）
- [ ] **部分 Agent 输出统一 JSON 格式**（⚠️ 4/7 Agent 已实现）
- [ ] **长对话不会丢失核心约束**（🔴 IDEA-005 待评估）
- [ ] **基于 Git Hooks 的安全控制**（⚠️ Soft Lock 已部分实现）

### 质量指标

| 指标 | 当前 | 目标 | 状态 |
|------|-----|------|------|
| Agent 协作成功率 | 中等（基于 Skill 编排） | >90% | 🟡 改善中 |
| 幻觉输出率 | 低（IDEA-006 已实施） | <5% | 🟢 已改善 |
| 指令遗忘率 | 高（长对话） | <10% | 🔴 待改进（IDEA-005） |
| 无人值守可用性 | 部分可用（Soft Lock） | 可用（有安全保障） | 🟡 改善中 |

---

## 七、相关文件

### 问题诊断
- [分析精华（失败模式与改进条目）](../../docs/analysis/autodev-insights.md)

### 归档文档
- [归档索引](archived/README.md)
- [IDEA-001: SubAgent 调用机制](archived/IDEA-001-subagent-call-mechanism.md)（已归档）
- [IDEA-002: Agent 边界定义](archived/IDEA-002-agent-boundary-definition.md)（已归档）
- [IDEA-003: 鉴权 Agent](archived/IDEA-003-permission-guard-agent.md)（已归档）
- [IDEA-004: 结构化交互协议](archived/IDEA-004-structured-interaction-protocol.md)（已归档）

### 可行实现
- [IDEA-005: 本地化文档缓存](./IDEA-005-localized-instruction-cache.md)（可行，待评估）
- [IDEA-006: 强制数据访问机制](./IDEA-006-mandatory-data-access.md)（✅ 已完成）
- [IDEA-006 实施详情](./IDEA-006-implementation/)

### 源代码

#### 已完成 IDEA-006 改进
- ✅ `toolchain/agents/aw-kernel/ship.md` - 强制数据访问机制已实施
- ✅ `toolchain/agents/aw-kernel/clarify.md` - 强制数据访问机制已实施
- ✅ `toolchain/agents/aw-kernel/review.md` - 强制数据访问机制已实施
- ✅ `toolchain/agents/aw-kernel/debug (已删除).md` - 强制数据访问机制已实施
- ✅ `toolchain/agents/aw-kernel/logs.md` - 强制数据访问机制已实施
- ✅ `toolchain/agents/aw-kernel/clean.md` - 强制数据访问机制已实施
- ✅ `toolchain/agents/aw-kernel/knowledge-researcher.md` - 强制数据访问机制已实施

#### 可行的协作实现
- ✅ `toolchain/skills/aw-kernel/autodev/` - Skill 工作流编排
- ✅ `toolchain/skills/aw-kernel/autodev-worktree/` - Git Worktree 并行开发管理
- ✅ `toolchain/agents/aw-kernel/ship.md` - 5-Phase 闭环示例

---

## 八、实施进度总结

### ✅ 已完成（2026-01-04）
- **IDEA-006（强制数据访问机制）**
  - 所有 7 个 Agents 已全面实施"No Evidence, No Output"原则
  - 包含完整的工具纪律、自检清单、禁止模式和示例约束
  - 实际效果：显著降低幻觉输出率

### 📦 已归档（2026-01-04）
- **IDEA-001（SubAgent 调用机制）** - 不兼容 ClaudeCode
- **IDEA-002（Agent 边界定义）** - 无法技术强制
- **IDEA-003（鉴权 Agent）** - Agent 无法调用 Agent
- **IDEA-004（结构化交互协议）** - 无法强制 Schema 验证

### 🔄 当前可行方案
- **Skill 工作流编排**：autodev, autodev-worktree（已实现）
- **单 Agent 多阶段模式**：ship 5-Phase 闭环（已实现）
- **基于文件的协作**：.agent-handoff/（可探索）
- **AskUserQuestion 边界管理**：部分 Agent 已使用（可扩展）

### 🎯 待评估
- **IDEA-005（本地化指令缓存）** - 可行，待评估优先级

---

> **下一步建议**：
>
> 1. **统一 JSON 输出格式**：为 ship 和 clarify 添加 JSON 输出，参考 debug (已删除)
> 2. **评估 IDEA-005**：研究长对话中的指令遗忘问题，考虑模块化 Prompt 或外置指令
> 3. **探索文件协作**：定义 `.agent-handoff/` 协议，实现 Agent 间可靠的数据交换
>
> 优先级顺序：务实导向，先完善已有机制（JSON 输出），再探索新方向（文件协作）

---

**更新历史**：
- 2024-12-31: 初始创建
- 2026-01-04: IDEA-001~004 归档，添加可行方案章节，调整实施路线图
