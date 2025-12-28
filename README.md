# Trae-Agents-Prompt（Claude Code + Codex Baseline）

本仓库提供一套 **可闭环交付** 的中枢 Agent + repo-local 工具链，覆盖：需求澄清 → 计划 → 实现 → 测试 → 交付。

## TOC

- [导航](#nav)
- [全局安装 skills（推荐）](#global-install)
- [项目安装（repo-local，可选）](#quickstart)
- [Orchestrator / CI / SDK](#orchestrator)
- [Codex 交互模式（对话闭环）](#codex-chat)
- [Claude Code 接入](#claude-code)
- [反馈采集（可选）](#feedback-logger)
- [致谢](#thanks)
- [WSL 使用指南](WSL.md)

<a id="nav"></a>
## 导航

- 目录映射：`INDEX.md`
- Claude Code Agents：`.claude/agents/`（中枢：`feature-shipper.md`）
- Codex Skills：`codex-skills/`（中枢：`feature-shipper/`，可选：`feedback-logger/`）
- 归档（非主线维护）：`archive/`
- Orchestrator / Runner：
  - `agents_workflow.py`（串行跑 plan review → gate，并写 trace）
  - `agents_runner.py`（无 Agents SDK 依赖的 runner：plan review → gate）
  - `agents_sdk_runner.py`（Agents SDK + MCP 演示 runner）

<a id="global-install"></a>
## 全局安装 skills（推荐）

适合“经常在多个 repo 里启用工具链”的场景，也是 **最不污染目标项目根目录** 的用法：
- 目标项目只会新增 `.autoworkflow/`（以及你若使用 Claude Code，新增 `.claude/agents`/`.claude/skills`），不会把本仓库根部的 runner 脚本复制进去
- 全局一次安装，多项目复用，升级/回滚也更简单

安装（复制到 `$CODEX_HOME/skills/`，并可选追加别名 `aw-init/aw-auto/aw-gate/aw-doctor/aw-uninstall`；同时安装 Claude Code 的 agents/skills/commands 到 `$CLAUDE_HOME`，默认 `~/.claude`）：
- Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/install-global.ps1`
- WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/install-global.sh`
  - 选项：`--force` 覆盖；`--dry-run` 只看不写；`--no-profile` 不改 profile；`--no-claude` 跳过安装到 `~/.claude`；`--claude-home <path>` 指定 Claude 目录。
  - 默认目标：`$CODEX_HOME/skills/`（若未设置 `$CODEX_HOME`，一般为 `~/.codex/skills`）

使用（全局开箱 3 步）：
1) `aw-init`
2) `aw-auto`
3) `aw-gate`

不想改 profile：使用绝对路径，例如 `python $CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py --root <repo> auto-gate`

项目卸载（全局安装后，卸载某个目标项目里的 `.autoworkflow/`）：
- 在目标项目根执行：`aw-uninstall`

卸载/回滚（对称清理）：
- Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/uninstall-global.ps1`
- WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/uninstall-global.sh`
  - 默认会同时清理 `~/.bashrc` 的别名块、以及安装到 `$CLAUDE_HOME` 的 Claude assets（基于 manifest：`$CLAUDE_HOME/.autoworkflow-installed.txt`；可用 `--no-claude` 跳过）

<a id="quickstart"></a>
## 项目安装（repo-local，可选）

适用：你希望把工具链“随项目一起分发”（例如做成模板仓库/脚手架），或不方便做全局安装。

目标：在目标仓库根生成 `.autoworkflow/`，并用其中的 `tools/*` 作为统一入口（Windows / WSL / Ubuntu 均可）。

1) 初始化 `.autoworkflow/`
- 在目标 repo 根目录执行：`python <path-to>/codex-skills/feature-shipper/scripts/autoworkflow.py --root . init`
- 如需同步新版模板：追加 `--force`
- 如果你不在 repo 根目录执行，把 `--root .` 替换为 `--root <repo-root>`

2) Doctor（尽早暴露“跑不起来”问题）
- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 doctor --write --update-state`
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh doctor --write --update-state`

3) 生成 gate（推荐：自动推导）
- 仓库根执行：`python .autoworkflow/tools/autoworkflow.py auto-gate`
- （可选）让 Codex CLI 辅助推导：`python .autoworkflow/tools/autoworkflow.py auto-gate --codex`
- 或全局安装后：`aw-auto`
- 说明：优先解析 `CLAUDE.md` 的 Build/Test/Lint/Format；再按常见项目类型推导；写入 `.autoworkflow/gate.env`（默认保留已有值，除非 `--overwrite`）。

（可选）手动设定 gate（更可控，适合复杂项目）
- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 set-gate --create --build "..." --test "..."`
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh set-gate --create --build "..." --test "..."`
- 复杂引号建议直接编辑：`.autoworkflow/gate.env`

4) 跑 gate("测试全绿"为默认门禁)
- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 gate`（如需强制用 WSL，附 `--prefer-wsl`；WSL 失败将直接失败，不再降级）
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh gate`

（可选）模型推荐（诊断/调试时用）
- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 recommend-model --intent doctor|debug`
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh recommend-model --intent doctor|debug`

5) （可选）计划：gen / review / status
- 生成计划：`python .autoworkflow/tools/autoworkflow.py plan gen`
- 审核计划：`python .autoworkflow/tools/autoworkflow.py plan review`（score>=85 自动批准，否则打回）
- 查看状态：`python .autoworkflow/tools/autoworkflow.py plan status`
- 备注：gate 默认检查 `plan.review=approve`；需跳过可加 `--allow-unreviewed`（不推荐）。

6) （可选）保持工作区干净（不提交）
- Windows：`Add-Content .git/info/exclude ".autoworkflow/"`
- WSL/Ubuntu：`echo ".autoworkflow/" >> .git/info/exclude`

7) 卸载（项目级）
- 推荐（有全局安装时）：在目标项目根执行 `aw-uninstall`（需要无人值守可加 `--yes`；清理 `.git/info/exclude` 可加 `--remove-exclude`）
- 或直接执行：`python codex-skills/feature-shipper/scripts/autoworkflow.py --root . uninstall`
- 兜底（手动）：删除 `.autoworkflow/` 目录；若你曾写入 `.git/info/exclude`，把其中的 `.autoworkflow/` 行删掉即可

<a id="orchestrator"></a>
## Orchestrator / CI / SDK

- 轻量 orchestrator：`agents_workflow.py --root .`（plan review → gate，trace 写入 `.autoworkflow/trace/`）
- Runner（无 Agents SDK 依赖）：`agents_runner.py --root .`
- Agents SDK runner：`agents_sdk_runner.py`
  - `--mode mcp-smoke`：仅验证 MCP server 可启动（不需要 `OPENAI_API_KEY`）
  - `--mode local`：subprocess fallback（不需要 Agents SDK / `OPENAI_API_KEY`）
  - `--mode sdk`：多 Agent handoff 演示（需要 `OPENAI_API_KEY` + `pip install -r requirements-agents-sdk.txt`）

冷启动/端到端冒烟（不污染当前工作区）：
- Windows：`powershell -ExecutionPolicy Bypass -File ./codex-skills/feature-shipper/scripts/safe-smoke.ps1 -Root .`
- WSL/Ubuntu：`bash ./codex-skills/feature-shipper/scripts/safe-smoke.sh .`

CI 一键模板：
- `python .autoworkflow/tools/autoworkflow.py plan ci-template --provider github|gitlab`
  - GitHub：生成 `.github/workflows/aw-plan-gate.yml`（plan review → gate(dry-run) → agents_workflow(trace) → 上传 trace artifact）
  - GitLab：生成 `.gitlab-ci.yml`（同上）

<a id="codex-chat"></a>
## Codex 交互模式（对话闭环）

Codex CLI 支持交互式对话，把模型当成“执行型工程助手”在真实仓库内闭环推进（明确 DoD → 计划 → 改代码 → 跑 gate → 迭代直到通过）。

1) 启动交互会话
- 默认（使用你已配置/登录的模型提供方）：`codex --full-auto -C .`
- 特殊情况：本地模型（Ollama / LM Studio）：`codex --oss --local-provider ollama -m "qwen2.5-coder:7b" --full-auto -C .`

2) 启动后第一句话（让它按本仓库交付标准工作）
- 让 Codex 先读并遵守：`codex-skills/feature-shipper/SKILL.md`

3) 常用闭环入口
- 初始化：`python codex-skills/feature-shipper/scripts/autoworkflow.py --root . init`
- 跑 gate：`python .autoworkflow/tools/autoworkflow.py --root . gate`

> 备注：如果你在“非 git 目录/临时目录”里跑 `codex exec`，可能需要加 `--skip-git-repo-check`。

<a id="claude-code"></a>
## Claude Code 接入（在目标项目里使用中枢 Agent）

如果你已执行「全局安装」（上文），脚本默认会把 Claude Code 的 agents/skills 安装到 `~/.claude`，因此在任意目标仓库里直接启动 Claude Code 并选择 `feature-shipper` 即可（它会强制先打磨 spec / DoD，再坚持 gate 测试全绿闭环推进）。

如果你希望“随仓库分发”，或 Claude Code 未读取全局 agents/skills：
- 把 `~/.claude/agents/*.md`、`~/.claude/skills/*` 复制/软链到目标项目的 `.claude/agents/`、`.claude/skills/`（按需挑选；至少 `feature-shipper` + `autoworkflow/git-workflow`）。

如果 Claude Code UI 看不到 Agents，你也可以用 **Commands 显式调用**（全局安装会同步命令到 `~/.claude/commands/autoworkflow/`）：
- 在 Claude Code 对话里输入：`/autoworkflow:feature-shipper <需求/任务描述>`

**仅用 Claude Code 界面（不想敲 Python 命令）**
- 一次性准备：把本仓库的 `.claude/agents/`、`.claude/skills/`、`.autoworkflow/` 整目录复制到目标项目根（`gate.env` 里写上你的测试命令即可）。
- 打开 Claude Code，选择 Agent `feature-shipper`，直接对话描述需求；它会按 spec/DoD → plan → gate 全自动执行、调试、验证。
- 需要远端闭环时，只需在终端/系统里配置好 `GITEE_TOKEN`/`GITHUB_TOKEN`（或写入不入库的 `.autoworkflow/secret.env`），在对话里告知即可让它自动 push + PR + 等待 CI。

<a id="feedback-logger"></a>
## 可选：后台轻量日志（反馈采集）

在目标项目初始化 feedback logger 后，可监听 `.autoworkflow/*` 变化写入 `.autoworkflow/logs/feedback.jsonl`：
- Windows：`python <path-to>/codex-skills/feedback-logger/scripts/feedback.py init`
- Start/Stop：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 start|stop`

手工记录关键想法：
- `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 log --message "..." --tag hypothesis`

<a id="thanks"></a>
## 致谢

感谢使用 Trae-Agents-Prompt！如有问题或建议，欢迎提交 Issue / PR。
