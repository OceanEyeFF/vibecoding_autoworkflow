# WSL 使用指南（适用于已有代码仓库，尚未接入本工作流）

假设：你在 Windows + WSL 环境，已有一个代码仓库，但还没接入本项目的自动化工作流/Agent。目标：在 WSL 内完成初始化、运行 gate、并可在 Claude Code / Codex 中对话闭环。

## 0. 前置条件
- Windows 10/11 已启用 WSL（Ubuntu 推荐），`wsl` 命令可用。
- WSL 中已安装 Python 3.10+、Git。
- Git 行尾建议：`git config --global core.autocrlf input`，避免 CRLF 影响。

## 1. 推荐：全局安装（一次即可，多项目复用）

在 **WSL** 终端（任意目录）执行全局安装脚本，会把 skills 安装到 `$CODEX_HOME/skills`，并可选写入别名 `aw-init/aw-auto/aw-doctor/aw-gate/aw-uninstall`：

```bash
# 在本工具仓库执行（或替换为你的实际路径）
bash codex-skills/feature-shipper/scripts/install-global.sh
```

> 提示：如果不想改 `~/.bashrc`，加 `--no-profile`；想先预览加 `--dry-run`。
> 默认也会把 Claude Code 的 agents/skills/commands 安装到 `$CLAUDE_HOME`（默认 `~/.claude`），因此你应能在 `~/.claude/agents/` 看到 `feature-shipper.md`，并在 `~/.claude/commands/autoworkflow/` 看到命令入口。
> 如果你不想安装到 `~/.claude`，加 `--no-claude`。
> 安装后请重开终端，或执行 `source ~/.bashrc` 让别名生效。

## 2. 在目标项目初始化（WSL）

进入你要接入的“目标项目根目录”，执行：

```bash
aw-init
aw-auto          # 或 aw-auto --codex 让 Codex 辅助推导
aw-doctor
aw-gate
```

生成的 `.autoworkflow/gate.env` 中至少要有 `TEST_CMD`（你的项目测试命令）；`gate` 绿即通过。

> 若你使用 Claude Code：全局安装默认已写入 `~/.claude/agents` 与 `~/.claude/skills`，通常不需要再同步到目标项目。
> 如果你的 Claude Code 没有读取全局 agents/skills，再把它们复制/软链到目标项目根的 `.claude/agents/`、`.claude/skills/`（你可以认为这不算“污染”）。

## 3. 备选：项目内安装（repo-local）

适用：你无法/不想做全局安装，或希望把工具链随仓库分发。

在 **WSL** 终端进入目标项目根目录，复制/同步本仓库中的工作流资源：
- `.autoworkflow/`（含 `tools/aw.sh`、`gate.sh`、模板、state/spec 等）
- `codex-skills/feature-shipper/`（工具脚本与 SKILL）
- （可选）`.claude/agents/` 与 `.claude/skills/`（用于 Claude Code Agent）

然后初始化并运行：

```bash
python codex-skills/feature-shipper/scripts/autoworkflow.py --root . init
python .autoworkflow/tools/autoworkflow.py --root . auto-gate   # 或 set-gate --test "<你的测试命令>"
bash .autoworkflow/tools/aw.sh doctor --write --update-state
bash .autoworkflow/tools/aw.sh gate
```

## 4. 卸载/清理

卸载“某个目标项目”的工作流（删除 `.autoworkflow/`）：

```bash
aw-uninstall          # 交互确认
aw-uninstall --yes    # 无人值守
```

如你之前写过 `.git/info/exclude`，可同时清理：

```bash
aw-uninstall --remove-exclude
```

卸载全局安装（移除 `$CODEX_HOME/skills/*` 并清理 profile 别名块）：

```bash
bash codex-skills/feature-shipper/scripts/uninstall-global.sh
```
> 默认也会清理安装到 `$CLAUDE_HOME` 的 Claude assets（基于 manifest：`$CLAUDE_HOME/.autoworkflow-installed.txt`）；如需跳过，加 `--no-claude`。

## 5. 配置远端鉴权（push/PR）
- 在 WSL Shell 设置环境变量，或写入不入库的 `.autoworkflow/secret.env`：
```bash
export GITEE_TOKEN=xxxx    # 或 GITHUB_TOKEN=xxxx
echo "GITEE_TOKEN=xxxx" > .autoworkflow/secret.env
```

## 6. 一键 PR 闭环（可选）
```bash
python .autoworkflow/tools/autoworkflow.py --root . \
  git pr create --push --set-upstream --wait-ci \
  --base develop --bootstrap-base-from origin/master
```
- 自动：若远端无 develop，会从 origin/master 引导创建。
- CI 状态会在命令尾汇总。

## 7. 在 Codex CLI 中对话闭环（WSL）
```bash
codex --full-auto -C .
```
- 开场提示 Codex 先读 `codex-skills/feature-shipper/SKILL.md`。
- 它会按 spec/DoD → plan → gate → 修复 → 再 gate，直到绿。

## 8. 在 Claude Code 中全自动（无需手敲命令）
1) 确保全局安装已完成（应能在 `~/.claude/agents/` 看到 `feature-shipper.md`）。  
2) 打开 Claude Code（在目标仓库根运行 `claude`），选择 Agent `feature-shipper`。  
3) 对话描述需求；Agent 会自动跑 spec/DoD → plan → gate → 调试。  
4) 若已配置 token，可在对话中让它执行 push + PR + 等待 CI。

如果 Claude Code UI 看不到 Agents（但你能用 commands），用命令显式调用：
```bash
/autoworkflow:feature-shipper <需求/任务描述>
```

## 9. 常见问题
- **WSL 不可用**：`wsl --install`，重启终端后再跑 gate。
- **缺 token**：设置环境变量或 `.autoworkflow/secret.env` 后重开终端再跑 PR 命令。
- **base 分支缺失**：使用 `--bootstrap-base-from origin/master`。
- **.autoworkflow 被忽略**：需要提交工具改动时用 `git add -f .autoworkflow/...`。

> 始终以 `gate` 结果为唯一“完成”标准；保持 gate 绿色。
