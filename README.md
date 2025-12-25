# Trae-Agents-Prompt (Claude Code + Codex Baseline)

这个仓库当前的主线目标：沉淀一套 **可闭环交付** 的中枢 Agent + repo-local 工具链，用于 Claude Code / Codex（可选兼容其他宿主）。

核心原则：**任何需求输入（对话/文档/链接）先打磨成可验证 DoD，再进入实现；以“测试全绿”为唯一门禁。**

## 目录结构

- Claude Code Agents：`.claude/agents/`
  - 中枢：`.claude/agents/feature-shipper.md`
  - 专项：`code-analyzer` / `code-debug-expert` / `requirement-refiner` 等
- Codex Skills：`codex-skills/`
  - 中枢：`codex-skills/feature-shipper/`
  - 可选日志：`codex-skills/feedback-logger/`
- 归档（非主线维护）：`archive/`

更详细的映射见：`INDEX.md`。

## 使用教程（普通 Repo / 全局）

### A) 普通 Repo 使用（推荐：repo-local）

目标：在任意项目根目录生成 `.autoworkflow/`，并始终用 `.autoworkflow/tools/*` 作为统一入口（Windows/WSL/Ubuntu 都能跑）。

#### 1) 初始化 `.autoworkflow/`

两种方式任选其一：

- 方式 1（最常用）：进入目标项目根目录再执行
  - Windows：`python <path-to>/codex-skills/feature-shipper/scripts/autoworkflow.py init`
  - WSL/Ubuntu：同上
- 方式 2（不切目录）：显式指定 `--root`
  - Windows：`python <path-to>/codex-skills/feature-shipper/scripts/autoworkflow.py --root <repo-root> init`
  - WSL/Ubuntu：同上

初始化会生成：

- `.autoworkflow/tools/aw.ps1` / `.autoworkflow/tools/aw.sh`（统一入口）
- `.autoworkflow/tools/gate.ps1` / `.autoworkflow/tools/gate.sh`（本地门禁）
- `.autoworkflow/state.md` / `.autoworkflow/spec.md`（默认不提交）
- `.autoworkflow/model-policy.json`（默认不提交，用于模型推荐）

如果你更新了本仓库里的脚本/模板，想把目标项目里的 `.autoworkflow/tools/*` 同步刷新，可以重新跑 init 并加 `--force` 覆盖：

- Windows：`python <path-to>/codex-skills/feature-shipper/scripts/autoworkflow.py --root <repo-root> init --force`

#### 2) 先跑 doctor（把“跑不起来”尽早暴露）

（在目标项目根目录执行）

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 doctor --write --update-state`
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh doctor --write --update-state`

#### 3) 配置 gate（定义“测试全绿”）

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 set-gate --create --build "..." --test "..."`
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh set-gate --create --build "..." --test "..."`

如果命令包含复杂引号/分号（PowerShell 很常见），建议直接编辑 `.autoworkflow/gate.env`，避免转义地狱。

#### 4) 打磨 spec → 跑 gate

- 先打磨：填 `.autoworkflow/spec.md`（范围/非目标/验收标准/gate 命令）
- 再门禁：
  - Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 gate`
  - WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh gate`

`gate` 会把最近一次结果追加到 `.autoworkflow/state.md`（失败时附带 highlights + tail）。

#### 5) 智能选模型（推荐 + 需要时升级）

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 recommend-model --intent doctor|debug`
- WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh recommend-model --intent doctor|debug`

注意：是否能“自动切换模型”取决于宿主工具；这里提供的是可落地的“推荐+升级”策略（默认中等，遇到复杂 gate 失败再升级）。

#### 6) 保持 repo 干净（可选）

默认 `.autoworkflow/*` 都建议不提交。若你不希望它出现在 `git status` 里，可把目录加入本地 exclude（不会影响团队、不会提交）：

- Windows：`Add-Content .git/info/exclude ".autoworkflow/"`
- WSL/Ubuntu：`echo ".autoworkflow/" >> .git/info/exclude`

### B) 全局使用（可选：安装到 Codex Skills）

如果你希望在任何地方都能直接使用 `<CODEX_HOME>/skills/...` 的路径（不需要手动写 `<path-to>`），可以把本仓库的 `codex-skills/*` 安装到 `$CODEX_HOME/skills/`（复制或软链接均可）。

安装后，你可以在任意 repo 里执行（示例）：

- Windows：`python (Join-Path $env:CODEX_HOME 'skills/feature-shipper/scripts/autoworkflow.py') --root <repo-root> init`
- WSL/Ubuntu：`python "$CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py" --root <repo-root> init`

初始化完成后仍然推荐用 repo-local 的 `.autoworkflow/tools/aw.*` 作为日常入口。

## Claude Code 接入（在目标项目里使用中枢 Agent）

Claude Code 的 agent 发现通常依赖项目内的 `.claude/agents/`。推荐做法是把中枢 agent 复制/软链到目标项目：

- 复制：把本仓库的 `.claude/agents/feature-shipper.md` 放到目标项目的 `.claude/agents/feature-shipper.md`
- 可选：按需把 `code-debug-expert` / `requirement-refiner` 等专项 agent 一起复制过去

然后在 Claude Code 里选择 `feature-shipper`，它会强制先打磨 spec/DoD，再按 gate（测试全绿）闭环推进。

## 可选：后台轻量日志（改进测试时很有用）

在目标项目里初始化 feedback logger 后，可后台 watch `.autoworkflow/*` 的变化并写入 `.autoworkflow/logs/feedback.jsonl`：

（在目标项目根目录执行，或用 `--root <repo-root>`）

- Windows：`python <path-to>/codex-skills/feedback-logger/scripts/feedback.py init`
- WSL/Ubuntu：同上

启动后台 watch：

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 start`
- WSL/Ubuntu：`bash .autoworkflow/tools/fb.sh start`

停止后台 watch：

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 stop`
- WSL/Ubuntu：`bash .autoworkflow/tools/fb.sh stop`

手工记录关键想法（假设/结论/TODO）：

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 log --message "..." --tag hypothesis`

包裹某条命令并记录失败高亮 + tail（很适合收集 flaky / 编译失败关键信息）：

- Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 wrap --tag gate powershell -Command "..."` 

## 归档说明

- 历史 Trae 模板已归档到：`archive/Trae-agents/`
- 游戏叙事相关 Claude agent 归档到：`archive/claude-agents/`

感谢您使用 Trae-Agents-Prompt 仓库！如有任何问题或建议，请随时提交 Issue 或 Pull Request。
