---
title: "Claude Repo-local Usage Help"
status: active
updated: 2026-05-02
owner: aw-kernel
last_verified: 2026-05-02
---
# Claude Repo-local Usage Help

> 目的：只保留 `claude` backend 的 runtime 侧差异，回答 “常见 skill root 在哪、最小 smoke verify 怎么做、当前仓库支持边界是什么”。当前仓库的 `adapter_deploy.py` 已提供受控的 `--backend claude` full skill payload lane。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [aw-installer Public Quickstart Prompts](../deploy/aw-installer-public-quickstart-prompts.md)
- [aw-installer External Trial Feedback Contract](../deploy/aw-installer-external-trial-feedback.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)
- [Claude Post-Deploy Behavior Tests](../testing/claude-post-deploy-behavior-tests.md)

## 一、Backend 标识与常见路径

- backend 名：`claude`
- 常见 repo-local runtime root：`.claude/skills/`
- 常见 user-home runtime root：`~/.claude/skills`

说明：

- 这里描述的是 Claude 侧常见 runtime 路径和当前受控 `adapter_deploy.py --backend claude` payload lane
- 当前仓库的 `claude` backend 准入完整 Harness skill set；target dirs 使用 `.claude/skills/<skill-name>/`，旧 `aw-<skill-name>` 目录只作为 legacy managed cleanup 入口
- `set-harness-goal-skill/scripts/deploy_aw.py` 的 `--claude-root` 仍属于本文第五节的冷启动 helper 例外，和 adapter CLI 的受管 payload install 是两条入口
- 完整 smoke / 冷启动步骤见 [Claude Post-Deploy Behavior Tests](../testing/claude-post-deploy-behavior-tests.md)

## 二、最小 trial smoke verify 口径

`claude` 当前是 Claude Code 适配 lane，不是 `agents` 外部试用主路径。当前 adapter CLI 可安装完整受管 Harness skill set，也可继续使用第五节的冷启动 helper。完整 Codex/Claude trial prompt 入口仍以 [aw-installer Public Quickstart Prompts](../deploy/aw-installer-public-quickstart-prompts.md) 为准。

建议做法：

- 显式调用 `.claude/skills/` 下的一个 repo-local skill entry
- 选一个你当前在用、且输出结构稳定的 skill 做最小读取确认
- 只确认 “skill entry 能被 Claude 读取，输出结构仍符合对应 skill 的固定契约”

判断标准：

- Claude 能读取对应 skill entry
- 输出仍符合固定结构
- 这一步是 backend runtime 可读性确认，不替代 source 与 target 对齐检查

## 三、和其他 backend 的区别

- `claude` 承接受控的完整 Harness skill payload 与 runtime skill entry 可读性 trial smoke；`agents` 当前仍是 deploy verify 与 Codex Harness manual run 主路径
- `claude` 的常见 user-home runtime 路径是 `~/.claude/skills`，不依赖 `CODEX_HOME` 或 XDG 推导
- 当前仓库提供 `claude` backend 的受控 deploy adapter CLI；如果未来改变完整 skill set 的 payload 边界、target 命名或验证矩阵，必须以新的 worktrack 更新本页和 deploy 文档
- Claude Code 试用反馈仍走 [aw-installer External Trial Feedback Contract](../deploy/aw-installer-external-trial-feedback.md)、[trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 或 [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)，并标明它是 compatibility trial lane

## 四、当前限制

- 不要把 `adapter_deploy.py --backend claude` 写成 `agents` 主路径替代品；它是 Claude Code skill payload 适配 lane
- 这页只承接 Claude 的 runtime 路径、受控 compatibility payload 与 smoke verify 差异

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
- 这只覆盖 `set-harness-goal-skill` 的冷启动 helper 场景；adapter CLI 的 `--backend claude` 是另一条受管 payload install 路径，并覆盖完整 Harness skill set
- 临时 repo 中的 operator-facing 测试步骤见 [Claude Post-Deploy Behavior Tests](../testing/claude-post-deploy-behavior-tests.md)
