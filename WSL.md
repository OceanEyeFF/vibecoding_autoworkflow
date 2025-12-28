# WSL 使用指南（适用于已有代码仓库，尚未接入本工作流）

假设：你在 Windows + WSL 环境，已有一个代码仓库，但还没接入本项目的自动化工作流/Agent。目标：在 WSL 内完成初始化、运行 gate、并可在 Claude Code / Codex 中对话闭环。

## 0. 前置条件
- Windows 10/11 已启用 WSL（Ubuntu 推荐），`wsl` 命令可用。
- WSL 中已安装 Python 3.10+、Git。
- Git 行尾建议：`git config --global core.autocrlf input`，避免 CRLF 影响。

## 1. 获取工作流文件
在 **WSL** 终端进入你的项目根目录，复制/同步本仓库中的工作流资源：
- `.autoworkflow/`（含 `tools/aw.sh`、`gate.sh`、模板、state/spec 等）
- `.claude/agents/` 与 `.claude/skills/`（用于 Claude Code Agent）
- `codex-skills/feature-shipper/`（工具脚本与 SKILL）

> 可以直接从本工具仓库拷贝上述目录到目标项目根；如用子模块/软链亦可。

## 2. 初始化工作流
```bash
# 在 WSL 的项目根执行
python codex-skills/feature-shipper/scripts/autoworkflow.py --root . init
python .autoworkflow/tools/autoworkflow.py --root . auto-gate   # 或 set-gate --test "<你的测试命令>"
bash .autoworkflow/tools/aw.sh doctor --write --update-state
```
生成的 `.autoworkflow/gate.env` 中至少要有 TEST_CMD（你的项目测试命令）。

## 3. 运行 gate（WSL 优先，失败即停）
```bash
bash .autoworkflow/tools/aw.sh gate
# 或等价：
python .autoworkflow/tools/autoworkflow.py --root . gate
```
> 若 WSL 不可用，命令会直接失败；如需在 Windows 跑 gate，手动在 PowerShell 执行：
> `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 gate`

## 4. 配置远端鉴权（push/PR）
- 在 WSL Shell 设置环境变量，或写入不入库的 `.autoworkflow/secret.env`：
```bash
export GITEE_TOKEN=xxxx    # 或 GITHUB_TOKEN=xxxx
echo "GITEE_TOKEN=xxxx" > .autoworkflow/secret.env
```

## 5. 一键 PR 闭环（可选）
```bash
python .autoworkflow/tools/autoworkflow.py --root . \
  git pr create --push --set-upstream --wait-ci \
  --base develop --bootstrap-base-from origin/master
```
- 自动：若远端无 develop，会从 origin/master 引导创建。
- CI 状态会在命令尾汇总。

## 6. 在 Codex CLI 中对话闭环（WSL）
```bash
codex --full-auto -C .
```
- 开场提示 Codex 先读 `codex-skills/feature-shipper/SKILL.md`。
- 它会按 spec/DoD → plan → gate → 修复 → 再 gate，直到绿。

## 7. 在 Claude Code 中全自动（无需手敲命令）
1) 确保项目根已有步骤 1 的复制内容。  
2) 打开 Claude Code，选择 Agent `feature-shipper`。  
3) 对话描述需求；Agent 会自动跑 spec/DoD → plan → gate → 调试。  
4) 若已配置 token，可在对话中让它执行 push + PR + 等待 CI。

## 8. 常见问题
- **WSL 不可用**：`wsl --install`，重启终端后再跑 gate。
- **缺 token**：设置环境变量或 `.autoworkflow/secret.env` 后重开终端再跑 PR 命令。
- **base 分支缺失**：使用 `--bootstrap-base-from origin/master`。
- **.autoworkflow 被忽略**：需要提交工具改动时用 `git add -f .autoworkflow/...`。

> 始终以 `gate` 结果为唯一“完成”标准；保持 gate 绿色。
