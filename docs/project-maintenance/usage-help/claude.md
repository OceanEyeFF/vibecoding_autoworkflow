---
title: "Claude Repo-local Usage Help"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# Claude Repo-local Usage Help

> 目的：只保留 `claude` backend 的 runtime 侧差异，回答 “常见 skill root 在哪、最小 smoke verify 怎么做、当前仓库支持边界是什么”。当前仓库的 `adapter_deploy.py` 不提供 `--backend claude`。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [aw-installer Public Quickstart Prompts](../deploy/aw-installer-public-quickstart-prompts.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)
- [Claude Harness Test Runbook](../deploy/claude-harness-test-runbook.md)

## 一、Backend 标识与常见路径

- backend 名：`claude`
- 常见 repo-local runtime root：`.claude/skills/`
- 常见 user-home runtime root：`~/.claude/skills`

说明：

- 这里描述的是 Claude 侧常见 runtime 路径，不是当前仓库 `adapter_deploy.py` 的 CLI 合同
- 当前仓库的 deploy adapter 只实现 `--backend agents`；不要把旧 adapter 的 `--claude-root`、`verify --target global` 命令当成现行入口
- `set-harness-goal-skill/scripts/deploy_aw.py` 的 `--claude-root` 只属于本文第五节的冷启动 helper 例外
- 完整 smoke / 冷启动步骤见 [Claude Harness Test Runbook](../deploy/claude-harness-test-runbook.md)

## 二、最小 trial smoke verify 口径

`claude` 当前只是 runtime compatibility trial lane，不是已实现的 deploy adapter backend。前提是先按本文第五节安装项目级冷启动 helper，再做最小 skill entry 可读性确认。

建议做法：

- 显式调用 `.claude/skills/` 下的一个 repo-local skill entry
- 选一个你当前在用、且输出结构稳定的 skill 做最小读取确认
- 只确认 “skill entry 能被 Claude 读取，输出结构仍符合对应 skill 的固定契约”

判断标准：

- Claude 能读取对应 skill entry
- 输出仍符合固定结构
- 这一步是 backend runtime 可读性确认，不替代 source 与 target 对齐检查

## 三、和其他 backend 的区别

- `claude` 仅保留 runtime skill entry 可读性 trial smoke；`agents` 当前承接 deploy verify 与 Codex Harness manual run，不再承接 skills mock / contract smoke
- `claude` 的常见 user-home runtime 路径是 `~/.claude/skills`，不依赖 `CODEX_HOME` 或 XDG 推导
- 当前仓库不提供 `claude` backend 的 deploy adapter CLI；如果未来恢复，必须以新的真实命令面更新文档

## 四、当前限制

- 不要在当前仓库使用 `adapter_deploy.py --backend claude`
- 这页只承接 Claude 的 runtime 路径与 smoke verify 差异，不承接 deploy 命令合同

## 五、当前受控例外

`set-harness-goal-skill` 自带的 `scripts/deploy_aw.py` 可以把该技能自身安装到目标 repo 的 Claude 项目级 skill 目录：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/deploy_aw.py install-claude-skill --deploy-path "$DEPLOY_PATH"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/deploy_aw.py generate --deploy-path "$DEPLOY_PATH" --install-claude-skill
```

边界：

- 目标路径是 `<deploy-path>/.claude/skills/aw-set-harness-goal-skill/`
- 默认不覆盖已有文件；需要覆盖时显式传 `--force`
- `--claude-root` 只应在 operator 明确控制的 trial 环境中使用；公开试用优先使用目标 repo 的项目级 `.claude/skills/`，不要默认写入共享或 user-home runtime root
- 目标 skill 目录 `aw-set-harness-goal-skill/` 本身不能是 symlink
- 目标 skill 目录内部已有的 symlink 文件或子目录会被拒绝，避免 copy install 写出该 skill 目录
- 如果目标 skill 目录本身不是 symlink，但经允许的 root symlink / mount 解析后就是当前运行的 skill 包，安装视为 already installed 并 no-op
- 这只覆盖 `set-harness-goal-skill` 的冷启动 helper 场景，不代表 `adapter_deploy.py` 已恢复 `claude` backend
- 临时 repo 中的 operator-facing 测试步骤见 [Claude Harness Test Runbook](../deploy/claude-harness-test-runbook.md)
