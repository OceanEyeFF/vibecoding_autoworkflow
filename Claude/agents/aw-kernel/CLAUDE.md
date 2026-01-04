# Claude Agents 指南（Trae-Agents-Prompt）

## 目的
为 Claude Code 提供可闭环交付的中枢与专用 Agent，统一遵循：先打磨 DoD/spec，测试全绿为门禁，跨平台一致。

## Agent 列表
- **feature-shipper（中枢）**：驱动“需求→DoD→实现→gate”全流程；强制先写 spec/state，再跑 gate。
- **code-analyzer**：快速梳理代码结构/架构，输出依赖与分层视图。
- **requirement-refiner**：多轮收敛模糊需求，产出可验收的 DoD/任务列表。
- **code-debug-expert**：系统化调试（假设→验证循环），提炼失败高亮。
- **system-log-analyzer**：分析日志/事故，输出时间线与根因假设。
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
- 注意：子代理默认不继承 skills；需要在 subagent YAML 中通过 `skills: skill1, skill2` 显式声明加载。
  - 例：`feature-shipper` 已声明 `skills: autoworkflow, git-workflow`

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

## 常用路径
- `.claude/agents/feature-shipper.md`（中枢）
- `.autoworkflow/tools/aw.ps1|aw.sh`（统一入口）
- `.autoworkflow/state.md`（进度与最近 gate 输出）
- `.autoworkflow/gate.env`（Build/Test/Lint/Format 命令源）

## 小贴士
- 复杂 PowerShell 引号：直接编辑 `gate.env` 更稳。
- 遇到多模块仓库，优先同步 CI 配置或 `CLAUDE.md` 中的命令，以避免偏差。
