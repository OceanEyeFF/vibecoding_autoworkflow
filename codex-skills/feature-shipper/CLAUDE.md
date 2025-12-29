# Codex Skill：feature-shipper（中枢工作流）

## 能力概述
- 初始化 `.autoworkflow/`（工具入口、模板、model-policy）
- 卸载 `.autoworkflow/`（项目级清理）
- doctor：诊断环境与项目信号（写入 `doctor.md` / `state.md`）
- auto-gate：自动推导 Build/Test/Lint/Format，写入 `gate.env`
- gate：跨平台本地门禁（测试全绿）
- recommend-model：基于信号与意图的模型档位推荐

## CLI 入口
`python scripts/autoworkflow.py <subcommand> [--root <repo>]`

子命令：
- `init [--force]`
- `uninstall [--yes] [--remove-exclude]`
- `doctor [--write] [--update-state]`
- `set-gate --build ... --test ... [--lint ...] [--format-check ...] [--create]`
- `auto-gate [--overwrite] [--dry-run]`（新增）
- `gate [--build ... --test ... --lint ... --format-check ...]`
- `recommend-model [--intent doctor|debug|...]`

PowerShell / Bash 包装：`.autoworkflow/tools/aw.ps1`、`aw.sh`

## 全局懒人模式
一键安装并注入别名：
- Windows：`powershell -ExecutionPolicy Bypass -File codex-skills/feature-shipper/scripts/install-codex-global.ps1`
- WSL/Ubuntu/Mac：`bash codex-skills/feature-shipper/scripts/install-codex-global.sh`
  - 选项：`--force` 覆盖；`--dry-run` 仅查看；`--no-profile` 不写 profile；`--codex-home <path>` 自定义 Codex 目录。
（如需同步 Claude Code assets：运行 `install-claude-global.ps1/.sh`；或用兼容旧入口 `install-global.ps1/.sh` 同时安装。）
  - 追加别名：`aw-init` / `aw-auto` / `aw-gate` / `aw-doctor` / `aw-uninstall`

最少步骤（全局）：
1) `aw-init`
2) `aw-auto`
3) `aw-gate`

## auto-gate 逻辑
优先级：`CLAUDE.md` 中的 Build/Test/Lint/Format 行 ＞ 结构启发式  
支持类型：Node（npm/pnpm/yarn）、Poetry/Python、Go、Cargo(Rust)、Java(Maven/Gradle)、.NET  
写入 `.autoworkflow/gate.env`，保留已有值；`--overwrite` 可覆盖；`--dry-run` 仅打印。

## 文件与产物
- `.autoworkflow/tools/gate.ps1|gate.sh`：本地 gate 入口
- `.autoworkflow/gate.env`：命令源（BUILD_CMD/TEST_CMD/LINT_CMD/FORMAT_CHECK_CMD）
- `.autoworkflow/state.md`：最近 gate/doctor 结果（含失败高亮）
- `.autoworkflow/spec.md`：需求/验收标准模板
- `.autoworkflow/model-policy.json`：模型档位策略

## 推荐使用路径
1) `init` → `doctor --write --update-state`
2) `auto-gate`（若必要再 `set-gate` 微调）
3) `gate`（失败看 state.md 的 highlights/tail）
4) 需要模型建议时 `recommend-model --intent debug`

## 跨平台注意
- 所有命令均提供 `.ps1` / `.sh` 等价实现；Windows 默认 PowerShell，WSL/Ubuntu 用 Bash。
- 建议将 `.autoworkflow/` 加入 `.git/info/exclude`，保持 repo 干净（默认不提交）。

## 版本控制提示
- 模板与脚本更新后，可在目标仓库重跑 `init --force` 以覆盖 `.autoworkflow/tools/*`。
- 不要提交 `gate.env` / `state.md` / `doctor.md` / `model-policy.json`（已在默认 .gitignore）。
