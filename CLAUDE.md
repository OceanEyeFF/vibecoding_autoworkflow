# Trae-Agents-Prompt — Claude/Codex 全局说明

## 项目愿景
沉淀一套“可闭环交付”的中枢 Agent 与 repo-local 工具链：需求澄清 → 计划 → 实现 → 测试 → 交付；以“测试全绿”为唯一门禁，兼容 Claude Code 与 Codex（也可接入其他宿主）。

## 核心组成
- Claude Agents：`.claude/agents/feature-shipper.md`（中枢）及若干专用 agent。
- Claude Skills：`.claude/skills/`（Claude Code 官方形态的可复用能力包；供 subagents 通过 `skills:` 加载，如 `autoworkflow` / `git-workflow`）。
- Codex Skills：`codex-skills/feature-shipper`（核心工具链）与 `codex-skills/feedback-logger`（可选后台日志）。
- Repo-local 工作目录：`.autoworkflow/`（init / doctor / gate / state / spec / model-policy）。

## 最快上手（全局懒人 3 步）
1) 全局一键安装（可选）：  
   - 仅安装 Codex skills：  
     - Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/install-codex-global.ps1`  
     - WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/install-codex-global.sh`  
     （复制 skills → `$CODEX_HOME/skills/`，并注入别名 `aw-init/aw-auto/aw-gate/aw-doctor`）
   - 仅安装 Claude Code assets：  
     - Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/install-claude-global.ps1`  
     - WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/install-claude-global.sh`
   - 兼容旧入口（同时安装）：  
     - Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/install-global.ps1`  
     - WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/install-global.sh`
2) 在目标仓库根：`aw-init`（生成 `.autoworkflow/*`）
3) 自动生成 gate 并跑：`aw-auto` → `aw-gate`

> 不改 profile 时，可用绝对路径：`python $CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py --root <repo> auto-gate`

## 普通（repo-local）使用
1) 初始化：`python codex-skills/feature-shipper/scripts/autoworkflow.py --root <repo> init`
2) Doctor：`aw.ps1 doctor --write --update-state` 或 `aw.sh doctor --write --update-state`
3) 自动生成 gate：`autoworkflow.py auto-gate`（或 `aw-auto`）  
   - 优先解析 `CLAUDE.md` 中 Build/Test/Lint/Format 行  
   - 再按项目类型启发式：Node、Poetry/Python、Go、Cargo、Java、.NET  
   - 写入 `.autoworkflow/gate.env`（保留已有值，`--overwrite` 可覆盖）
4) 手动微调（如需）：`set-gate --build ... --test ...` 或直接编辑 `gate.env`
5) 执行 gate：`aw.ps1 gate` / `aw.sh gate`

## Claude Code 集成指引
- 在目标项目放置 `.claude/agents/feature-shipper.md`（可加 code-analyzer / code-debug-expert / requirement-refiner 等），在 Claude Code 中选择对应 subagent。  
- 同步本仓库的 `.claude/skills/` 到目标项目（至少 `autoworkflow` 与 `git-workflow`），并确保 subagent YAML 已通过 `skills:` 显式声明（子代理默认不继承 skills）。  
- subagent 会强制先打磨 spec/DoD，再坚持 gate（测试全绿）闭环推进。

## 目录速览
- `.claude/agents/`：Claude Agents 定义文件
- `.claude/skills/`：Claude Skills（官方技能目录）
- `codex-skills/feature-shipper/`：核心 skill，含 `scripts/autoworkflow.py`、aw/gate 模板
- `codex-skills/feedback-logger/`：可选后台日志
- `.spec-workflow/`：规范/任务模板（非主线）
- `archive/`：历史存档

## 维护准则
- 先文档（DoD/spec）后实现；测试全绿为交付门禁。
- 跨平台等价：所有入口同时提供 `.ps1` 与 `.sh`。
- 默认不提交 `.autoworkflow/*`；可加入 `.git/info/exclude` 保持工作区干净。

## 常用命令速查
- init：`python .../autoworkflow.py init`
- doctor：`aw.ps1 doctor --write --update-state` / `aw.sh doctor --write --update-state`
- auto-gate：`aw-auto` 或 `python .../autoworkflow.py auto-gate`
- gate：`aw-gate` / `aw.ps1 gate` / `aw.sh gate`
- recommend-model：`aw.ps1 recommend-model --intent doctor|debug`（或 `aw.sh ...`）

## 贡献
- 欢迎 Issue / PR。主线维护范围：`.claude/agents/`、`codex-skills/`、`.spec-workflow/`。
- 归档内容位于 `archive/`，不再主动更新。旗舰厅。
