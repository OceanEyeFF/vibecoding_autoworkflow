# Agents / Skills Index (Claude Code + Codex)

这个仓库的目标：提供 **Claude Code Subagents/Skills** 与 **Codex Skills** 三套可复用“自动化交付”能力。Trae 相关内容先不作为主线维护。

## 中枢（闭环交付）

- Claude Code Agent（源资产）：`Claude/agents/feature-shipper.md`（安装后：`.claude/agents/feature-shipper.md`）
- Claude Code Skill（源资产）：`Claude/skills/autoworkflow/SKILL.md`（安装后：`.claude/skills/autoworkflow/SKILL.md`）
- Claude Code Skill（源资产）：`Claude/skills/git-workflow/SKILL.md`（安装后：`.claude/skills/git-workflow/SKILL.md`）
- Codex Skill：`CodeX/codex-skills/feature-shipper/SKILL.md`

定位：把“需求 → 计划 → 实现 → 测试 → 修复迭代 → 交付”跑成闭环，直到满足验收标准。
建议在目标项目中使用统一目录 `.autoworkflow/tools/` 存放跨平台 gate 脚本（Windows/WSL/Ubuntu 分别运行对应脚本），作为“测试全绿”的本地门禁入口。

## Claude Code Skills（可复用能力包）

- `autoworkflow`（源资产）：`Claude/skills/autoworkflow/SKILL.md`（围绕 `.autoworkflow/` 的 plan/review/gate 标准化闭环）
- `git-workflow`（源资产）：`Claude/skills/git-workflow/SKILL.md`（建分支/可选本地 commit 的安全闭环）

## 可选：反馈日志（后台轻量记录）

- Codex Skill：`CodeX/codex-skills/feedback-logger/SKILL.md`

用途：在改进测试/排障时，可后台记录关键中间信息（命令、失败高亮、state/doctor 变化、手工备注），避免返工。

## 可复用的专项（Claude Code Agents）

这些可以作为中枢的“专项模式/提示参考”继续保留：

- 结构/架构分析：`Claude/agents/code-analyzer.md`
- 调试/根因定位：`Claude/agents/code-debug-expert.md`
- 需求收敛：`Claude/agents/requirement-refiner.md`
- 日志/事故分析：`Claude/agents/system-log-analyzer.md`
- 项目清理：`Claude/agents/code-project-cleaner.md`
- 阶段文档驱动交付（偏重 Playwright）：`Claude/agents/stage-development-executor.md`

非软件交付主线，但保留以支持后续游戏开发场景（已归档，不参与 Claude Code agent 发现）：

- `archive/claude-agents/game-narrative-architect.md`

## 归档：Trae 旧模板（非主线维护）

- `archive/Trae-agents/`
