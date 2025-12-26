# Trae-Agents-Prompt（Claude Code + Codex Baseline）

本仓库提供一套 **可闭环交付** 的中枢 Agent 与 repo‑local 工具链，覆盖“需求澄清 → 计划 → 实现 → 测试 → 交付”全流程，兼容 Claude Code 与 Codex（也可接入其他宿主）。

## 目录结构
- Claude Code Agents：`.claude/agents/`
  - 中枢：`feature-shipper.md`
  - 可选：`code-analyzer` / `code-debug-expert` / `requirement-refiner` 等
- Codex Skills：`codex-skills/`
  - 中枢：`feature-shipper/`
  - 可选日志：`feedback-logger/`
- 归档（非主线维护）：`archive/`

更详细的映射见 `INDEX.md`。

## 使用教程（A：普通 repo，本地优先）

目标：在目标仓库根生成 `.autoworkflow/`，并始终用其中的 `tools/*` 作为统一入口（Windows / WSL / Ubuntu 均可）。

1) 初始化  
   - Windows：`python <path-to>/codex-skills/feature-shipper/scripts/autoworkflow.py init`  
   - WSL/Ubuntu：`python <path-to>/codex-skills/feature-shipper/scripts/autoworkflow.py --root <repo-root> init`
   - 如需同步新版模板：追加 `--force`

2) Doctor 先行（尽早暴露“跑不起来”问题）  
   - Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 doctor --write --update-state`  
   - WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh doctor --write --update-state`

2.5) 懒人自动生成 gate（免手写命令）  
   - 仓库根执行：`python .autoworkflow/tools/autoworkflow.py auto-gate`  
   - 或已做全局安装：`aw-auto`  
   - 逻辑：优先解析 `CLAUDE.md` 中的 Build/Test/Lint/Format 行；再根据常见项目类型（Node、Poetry/Python、Go、Cargo、Java、.NET）推导；写入 `.autoworkflow/gate.env`，保留已有值（除非 `--overwrite`）。

3) （可选）手动设定 gate  
   - Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 set-gate --create --build "..." --test "..."`  
   - WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh set-gate --create --build "..." --test "..."`
   - 复杂引号建议直接编辑 `.autoworkflow/gate.env`

4) 跑 gate（测试全绿为唯一门禁）  
   - Windows：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 gate`  
   - WSL/Ubuntu：`bash .autoworkflow/tools/aw.sh gate`

5) 模型推荐（可选）  
   - `powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/aw.ps1 recommend-model --intent doctor|debug`  
   - `bash .autoworkflow/tools/aw.sh recommend-model --intent doctor|debug`

6) 保持 repo 干净（可选）  
   - 将 `.autoworkflow/` 加入本地 exclude（不影响团队，不提交）：  
     - Windows：`Add-Content .git/info/exclude ".autoworkflow/"`  
     - WSL/Ubuntu：`echo ".autoworkflow/" >> .git/info/exclude`

## 使用教程（B：全局懒人模式，推荐给非专业用户）

一键安装 + 别名注入：
- Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/install-global.ps1`
- WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/install-global.sh`
  - 选项：`--force` 覆盖已有技能；`--dry-run` 仅查看不写入；`--no-profile` 不改 profile。
  - 默认复制 `codex-skills/*` 到 `$CODEX_HOME/skills/`（默认 `~/.codex/skills`），并向 profile 追加别名：`aw-init` / `aw-auto` / `aw-gate` / `aw-doctor`。

全局开箱 3 步：
1) 仓库根：`aw-init`
2) 自动生成 gate：`aw-auto`
3) 一键跑 gate：`aw-gate`

不想改 profile：使用绝对路径，例如  
`python $CODEX_HOME/skills/feature-shipper/scripts/autoworkflow.py --root <repo> auto-gate`

**卸载/回滚（对称清理）**
- Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/uninstall-global.ps1`
- WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/uninstall-global.sh`
  - 选项：`--force` 无确认删除；`--dry-run` 仅查看；`--no-profile` 不改 profile。
  - 作用：移除 `$CODEX_HOME/skills/feature-shipper`、`feedback-logger`，并删除 profile 中的 `# codex autoworkflow aliases` 段（若存在）。

## Claude Code 接入（在目标项目里使用中枢 Agent）

推荐将 `.claude/agents/feature-shipper.md` 复制/软链到目标项目的 `.claude/agents/`，按需附带 `code-debug-expert` / `requirement-refiner` 等。然后在 Claude Code 里选择 `feature-shipper`，它会强制先打磨 spec / DoD，再坚持 gate（测试全绿）闭环推进。

## 可选：后台轻量日志（改进测试时有用）

在目标项目初始化 feedback logger 后，可监听 `.autoworkflow/*` 变化写入 `.autoworkflow/logs/feedback.jsonl`：
- Windows：`python <path-to>/codex-skills/feedback-logger/scripts/feedback.py init`
- Start/Stop：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 start|stop`

手工记录关键想法：`powershell -ExecutionPolicy Bypass -File .autoworkflow/tools/fb.ps1 log --message "..." --tag hypothesis`

## 致谢

感谢使用 Trae-Agents-Prompt！如有问题或建议，欢迎提交 Issue / PR。
