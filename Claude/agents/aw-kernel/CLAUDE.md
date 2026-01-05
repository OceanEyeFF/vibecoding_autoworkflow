# Claude Agents 指南（Trae-Agents-Prompt）

## 目的
为 Claude Code 提供可闭环交付的中枢与专用 Agent，统一遵循：先打磨 DoD/spec，测试全绿为门禁，跨平台一致。

## Agent 列表
- **feature-shipper（中枢）**：驱动"需求→DoD→实现→gate"全流程；强制先写 spec/state，再跑 gate。
- **code-analyzer**：快速梳理代码结构/架构，输出依赖与分层视图。
- **requirement-refiner**：多轮收敛模糊需求，产出可验收的 DoD/任务列表。
- **code-debug-expert**：系统化调试（假设→验证循环），提炼失败高亮。
- **system-log-analyzer**：分析日志/事故，输出时间线与根因假设。
- **code-project-cleaner**：清理代码项目中的冗余文件，释放空间，保持目录整洁。
- 归档/可选：`archive/claude-agents/` 中的游戏相关等不在主线。

## 快速使用（Claude Code 内）
推荐（全局安装，不污染目标仓库）：
1) 运行本仓库 `install-global` 脚本（会安装到 `~/.claude/agents`、`~/.claude/skills`）。
2) 在任意目标仓库根目录先跑：`aw-init` → `aw-auto` → `aw-gate`（或用绝对路径执行 `autoworkflow.py auto-gate`）。
3) 在目标仓库根目录启动 Claude Code：`claude`，并选择 Agent `feature-shipper` 开始对话闭环。

如果 Claude Code UI 看不到 Agents，可用 Commands 显式调用（全局安装会同步到 `~/.claude/commands/autoworkflow/`）：
- 在对话里输入：`/autoworkflow:feature-shipper <需求/任务描述>`

备选（项目内安装/随仓库分发）：
- 若 Claude Code 未读取全局 agents/skills，或你希望“随仓库分发”，再把 `~/.claude/agents`、`~/.claude/skills` 复制/软链到目标仓库的 `.claude/agents/`、`.claude/skills/`。

## Skills（推荐）
- skills 目录：`.claude/skills/<skill>/SKILL.md`
- Skills 是用户可直接调用的入口（如 `/autodev`），Agents 是可被 Task 委派的专用处理器
- 推荐使用 `/autodev` Skill 作为主入口，它会在需要时通过 Task 工具委派专用 Agent

## 与 repo-local 工具的配合
- Agent 默认假设 `.autoworkflow/` 已初始化；`state.md` / `spec.md` / `gate.env` 是协作界面。
- `feature-shipper` 会要求：若无 gate，则先调用 `auto-gate` 或手动设定；失败时附带 highlights 与 tail。
- 推荐在 PR 前再次执行 `aw-gate`，保持 state 记录最新一次 gate 结果。

## 约定
- 输出语言：中文优先，必要时双语注释。
- 不提交 `.autoworkflow/*`；可加入 `.git/info/exclude`。
- 严守 DoD：无测试全绿不算完成；遇到缺失命令需先补全 gate。

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
- `.claude/agents/feature-shipper.md`（中枢）
- `.autoworkflow/tools/aw.ps1|aw.sh`（统一入口）
- `.autoworkflow/state.md`（进度与最近 gate 输出）
- `.autoworkflow/gate.env`（Build/Test/Lint/Format 命令源）

## 小贴士
- 复杂 PowerShell 引号：直接编辑 `gate.env` 更稳。
- 遇到多模块仓库，优先同步 CI 配置或 `CLAUDE.md` 中的命令，以避免偏差。
