# aw-kernel Agents 使用指南

## 目的
为 Claude Code 提供可闭环交付的专用 Agents（单任务专家）与配套规范（版本管理、工具纪律、证据化输出）。

## Agent 列表（aw-kernel）
- **ship**：功能交付闭环（实现与交付串联）
- **review**：结构/架构分析（输出可复核的结构化结论）
- **logs**：日志分析与诊断
- **clean**：清理与重构建议
- **clarify**：需求澄清与 DoD/验收细化
- **knowledge-researcher**：资料检索与知识沉淀

> 命名策略：高频任务用简短命名（ship/review/logs/clean/clarify），专业领域保留完整命名（knowledge-researcher）

> 归档内容在仓库 `archive/` 目录，不属于主线。

## 快速使用
1) **全局安装**：运行本仓库 `Claude/scripts/install-global.(sh|ps1)` 安装到 `~/.claude/agents/aw-kernel/` 与 `~/.claude/skills/aw-kernel/`。
2) **启动 Claude Code**：在目标仓库根目录启动 Claude Code，按任务选择 Agent 或 Skill（推荐以 `/autodev` 作为工作流入口）。

## Skills（推荐入口）
- Skill 目录：`~/.claude/skills/aw-kernel/<skill>/SKILL.md`（本仓库源目录为 `Claude/skills/aw-kernel/`）
- `/autodev` 负责工作流编排；必要时才委派专用 Agent

## 可选：.autoworkflow 工具链
- 若你需要“可复现的 Gate 命令 + 跨会话状态落盘 + 日志隔离”，参考 [TOOLCHAIN.md](TOOLCHAIN.md)
- 若不启用工具链：仅使用 TodoWrite 追踪会话内状态（跨会话不持久）

## 约定
- 输出语言：中文优先，必要时双语注释。
- No Evidence, No Output：无证据不得宣称“已通过/已验证”。
- 不提交 `.autoworkflow/*`（如使用该目录）；可加入 `.git/info/exclude`。

## 版本管理规范（强制）

本项目所有 Agent、Skill 和基础设施文档必须遵循版本管理规范。

详见：[VERSIONING.md](VERSIONING.md)

### 核心要求

| 要求 | 说明 |
|------|------|
| **版本号** | 遵循语义化版本 (SemVer): `MAJOR.MINOR.PATCH` |
| **元数据** | 所有文件必须包含 `version`、`created`、`updated` 字段 |
| **变更日志** | 所有变更必须记录在 [CHANGELOG.md](CHANGELOG.md) |

### Agent/Skill 文件头部格式

```yaml
---
name: agent-name
version: 1.0.0
created: 2026-01-06
updated: 2026-01-08
description: |
  功能描述...
model: sonnet
tools: Read, Grep, Glob, Bash, TodoWrite
---
```

### 版本号变更规则

| 变更类型 | 版本变化 | 示例 |
|---------|----------|------|
| Bug 修复 | PATCH +1 | 1.0.0 → 1.0.1 |
| 新增功能（兼容） | MINOR +1 | 1.0.1 → 1.1.0 |
| 不兼容变更 | MAJOR +1 | 1.1.0 → 2.0.0 |

### 修改文件时的检查清单

- [ ] 更新 `updated` 日期
- [ ] 根据变更类型决定是否更新 `version`
- [ ] 更新 CHANGELOG.md 的 `[Unreleased]` 部分

## 工具纪律（强制）

适用范围：所有允许使用 tools 的 Agents（如 `Read/Grep/Glob/Bash`）。

- **先查证后输出**：结论必须有可追溯证据（文件路径/命令输出/日志行）；没有证据就明确“不确定”，并列出最小补充信息清单。
- **先调用再回答**：能用工具确认的内容，必须先调用工具再回答；禁止凭空补全。
- **标准步骤**：意图拆解 → 工具调用 → 限制输出边界 → 提纯信息 → 限制噪声 → 生成输出（结论 + 证据 + 下一步动作）。
- **长上下文**：对跨多轮、长日志、长 diff 的工作，把中间状态写入临时文件（优先 `.autoworkflow/state.md`，或 `.autoworkflow/tmp/<agent>-notes.md`），对话中只保留摘要与引用，避免上下文丢失。

## 状态管理双轨制

本项目采用**双轨制状态管理**，明确区分会话内和跨会话的状态追踪职责：

### 1. TodoWrite（Claude Code 原生工具）

**用途**：**会话内**状态追踪

**职责**：
- 追踪当前对话中的任务进度（pending/in_progress/completed）
- 实时反馈工作流阶段（Phase 1/2/3/4）
- 展示当前正在执行的操作

**特点**：
- Claude Code UI 原生集成，用户可见
- 状态存储在 Claude Code 内部，不持久化到文件系统
- 会话结束后状态不保留

**使用场景**：
- `/autodev` Skill 的 Phase 流程追踪
- Agent 内部任务拆解与进度管理
- 实时向用户展示工作进度

**示例**：
```javascript
TodoWrite({
  todos: [
    { content: "Phase 1: 分析需求", status: "completed", activeForm: "分析需求" },
    { content: "Phase 2: 设计 DoD", status: "in_progress", activeForm: "正在设计 DoD" },
    { content: "Phase 3: 实现任务", status: "pending", activeForm: "实现任务" }
  ]
})
```

---

### 2. .autoworkflow/state.md（自定义文件）

**用途**：**跨会话**状态持久化

**职责**：
- 记录 Gate 检查结果（通过/失败时间、错误摘要）
- 保存 Phase 检查点（用于回路恢复）
- 存储长上下文中间状态（避免对话上下文丢失）
- 提供外部工具（Python 脚本）读取的接口

**特点**：
- 文件系统持久化，跨会话可访问
- 可被外部脚本读取（如 `claude_autoworkflow.py`）
- 需要手动维护（通过 Write/Edit 工具）

**使用场景**：
- 记录 G1/G2/G3 门禁检查历史
- 保存 Phase 2 检查点标识（`PHASE2_CHECKPOINT`）
- 长对话中的中间分析结果
- 跨会话恢复工作进度

**示例**（state.md 结构）：
```markdown
# AutoWorkflow State

## 最近 Gate 结果
- G1 (DoD 检查): ✅ 通过 (2026-01-05 14:30)
- G2 (计划检查): ✅ 通过 (2026-01-05 14:45)
- G3 (测试): ❌ 失败 (2026-01-05 15:10)
  - 错误: TypeError: Cannot read property 'foo'
  - 文件: src/index.js:42

## 当前检查点
- Phase 2 Checkpoint: stash@{0} (autodev-checkpoint-phase2)
- Git 能力: 有历史
```

---

### 3. 职责划分总结

| 维度 | TodoWrite（会话内） | state.md（跨会话） |
|------|--------------------|--------------------|
| **存储位置** | Claude Code 内部 | 文件系统 `.autoworkflow/` |
| **持久化** | ❌ 会话结束即清空 | ✅ 永久保存 |
| **可见性** | 用户 UI 可见 | 文件可读 |
| **外部访问** | ❌ 不可访问 | ✅ 脚本可读取 |
| **用途** | 实时进度追踪 | 历史记录与恢复 |
| **更新方式** | TodoWrite 工具 | Write/Edit 工具 |
| **典型内容** | 任务列表、状态 | Gate 结果、检查点 |

---

### 4. 协同使用示例

**场景：执行 /autodev 完整流程**

1. **Phase 1**（需求分析）：
   - TodoWrite: 标记 "Phase 1: 分析需求" 为 in_progress
   - state.md: 记录 G1 门禁检查结果

2. **Phase 2**（DoD 设计）：
   - TodoWrite: 更新为 "Phase 2: 设计 DoD" in_progress
   - state.md: 记录 G2 检查结果 + Phase 2 检查点标识

3. **Phase 3**（实现任务）：
   - TodoWrite: 实时追踪子任务进度（任务 A/B/C）
   - state.md: 每次 G3 失败时记录错误信息

4. **Level 1 回路**（任务回退）：
   - TodoWrite: 标记 "Level 1 回路: 任务重构"
   - state.md: 读取检查点标识，执行回退

5. **会话结束后**：
   - TodoWrite: 状态清空
   - state.md: 保留完整历史，下次会话可恢复

---

### 5. 最佳实践

**使用 TodoWrite 的时机**：
- 启动新的 Phase 或任务时
- 任务状态变更时（开始/完成/失败）
- 需要向用户展示实时进度时

**使用 state.md 的时机**：
- Gate 检查完成后（无论通过/失败）
- 创建 Phase 检查点后
- 长对话中需要保存中间分析结果时
- 需要为下次会话保留恢复信息时

**避免混淆**：
- ❌ 不要在 state.md 中写实时任务进度（用 TodoWrite）
- ❌ 不要期望 TodoWrite 状态跨会话保留（用 state.md）
- ✅ 两者互补，各司其职

## 常用路径
- `~/.claude/agents/aw-kernel/ship.md`（已安装：功能交付 Agent）
- `~/.claude/agents/aw-kernel/review.md`（已安装：代码分析 Agent）
- `~/.claude/skills/aw-kernel/`（已安装：Skills）
- `.autoworkflow/tools/cc-aw.ps1|cc-aw.sh`（可选工具链入口）
- `.autoworkflow/state.md`（可选：进度与最近 gate 输出）
- `.autoworkflow/gate.env`（可选：Build/Test/Lint/Format 命令源）

## 小贴士
- 复杂 PowerShell 引号：直接编辑 `gate.env` 更稳。
- 遇到多模块仓库，优先同步 CI 配置或 `CLAUDE.md` 中的命令，以避免偏差。
