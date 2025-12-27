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
1) 在目标仓库放置所需 subagent（至少 `feature-shipper.md`）到 `.claude/agents/`。
2) 同步本仓库提供的 skills 到目标仓库的 `.claude/skills/`（至少 `autoworkflow` 与 `git-workflow`）。
3) 运行 repo-local 工具链：`aw-init` → `aw-auto` → `aw-gate`（或直接 `autoworkflow.py auto-gate`）。  
4) 在 Claude Code 选择对应 subagent，按其提示先完善 spec/DoD，再按 gate 执行。

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

## 常用路径
- `.claude/agents/feature-shipper.md`（中枢）
- `.autoworkflow/tools/aw.ps1|aw.sh`（统一入口）
- `.autoworkflow/state.md`（进度与最近 gate 输出）
- `.autoworkflow/gate.env`（Build/Test/Lint/Format 命令源）

## 小贴士
- 复杂 PowerShell 引号：直接编辑 `gate.env` 更稳。
- 遇到多模块仓库，优先同步 CI 配置或 `CLAUDE.md` 中的命令，以避免偏差。
