# Testing Runbooks

`docs/project-maintenance/testing/` 只保存当前仓库 operator-facing 的测试执行指南。这里承接可重复运行的验证命令、registry/package smoke、以及 Codex / Claude 部署后的行为检查；deploy 合同与 source/target 映射仍在 `../deploy/`，发布治理规则在 `../governance/`。

这里适合放：

- Python 脚本、治理检查和 closeout gate 的运行方式
- `npx aw-installer` / 本地 `.tgz` package smoke 的运行方式
- Codex 部署后的 Harness 行为测试
- Claude Code 项目级 skill entry 和冷启动测试

这里不适合放：

- deploy destructive reinstall 主流程说明
- canonical skill 真相正文
- release approval package、一次性 review evidence 或历史 smoke 原始记录
- npm publish 授权或 release channel 规则

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我想运行 Python 脚本、治理检查或 closeout gate | [python-script-test-execution.md](./python-script-test-execution.md) | 固定 `PYTHONDONTWRITEBYTECODE=1 python3 ...` 口径和常用验证组合 |
| 我想验证 `npx aw-installer`、registry package 或本地 `.tgz` | [npx-command-test-execution.md](./npx-command-test-execution.md) | 覆盖 registry npx smoke、本地 package smoke、多临时 workdir 和反馈日志 |
| 我想回归 `aw-installer` CLI / TUI 全命令面 | `toolchain/scripts/test/aw_installer_cli/` 和 `toolchain/scripts/test/aw_installer_tui/` | CLI 覆盖 agents/claude 命令生命周期；TUI 通过 PTY 覆盖菜单交互、guided update 和退出路径 |
| 我想在 npm publish 前跑本地 `.tgz` package smoke | [npx-command-test-execution.md](./npx-command-test-execution.md) | 固定发布前 local package smoke 命令、临时 target 规则和最小通过证据 |
| 我想观察 Codex 部署后的 Harness 行为 | [codex-post-deploy-behavior-tests.md](./codex-post-deploy-behavior-tests.md) | 临时 repo、隔离 `.agents/skills/`、无交互 Codex 多轮观察 |
| 我想观察 Claude Code 项目级 skill entry 和冷启动 | [claude-post-deploy-behavior-tests.md](./claude-post-deploy-behavior-tests.md) | 临时 repo、`.claude/skills/` 项目级安装、Claude 非交互读取与 `.aw/` 冷启动 |

## 和 Deploy 文档的分工

- 通用 deploy 入口：看 [deploy/README.md](../deploy/README.md)
- destructive reinstall 主流程：看 [deploy-runbook.md](../deploy/deploy-runbook.md)
- source / payload / target 映射合同：看 [deploy-mapping-spec.md](../deploy/deploy-mapping-spec.md)
- release channel 规则：看 [aw-installer Release Channel Governance](../governance/aw-installer-release-channel-governance.md)
- publish 前 tuple / packlist / docs freshness / approval lock：看 [aw-installer Pre-Publish Governance](../governance/aw-installer-pre-publish-governance.md)
- payload provenance 与 update trust boundary：看 [payload-provenance-trust-boundary.md](../deploy/payload-provenance-trust-boundary.md)
