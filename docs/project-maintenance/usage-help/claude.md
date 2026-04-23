---
title: "Claude Repo-local Usage Help"
status: active
updated: 2026-04-23
owner: aw-kernel
last_verified: 2026-04-23
---
# Claude Repo-local Usage Help

> 目的：只保留 `claude` backend 的 runtime 侧差异，回答 “常见 skill root 在哪、最小 smoke verify 怎么做、当前仓库支持边界是什么”。当前仓库的 `adapter_deploy.py` 不提供 `--backend claude`。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与常见路径

- backend 名：`claude`
- 常见 repo-local runtime root：`.claude/skills/`
- 常见 user-home runtime root：`~/.claude/skills`

说明：

- 这里描述的是 Claude 侧常见 runtime 路径，不是当前仓库 `adapter_deploy.py` 的 CLI 合同
- 当前仓库的 deploy adapter 只实现 `--backend agents`；不要把旧的 `--claude-root`、`verify --target global` 命令当成现行入口

## 二、最小 smoke verify 口径

`claude` 是当前有稳定 smoke verify 口径的 backend 之一。前提是先让 `sync verify` 通过，再做最小 skill entry 可读性确认。

建议做法：

- 显式调用 `.claude/skills/` 下的一个 repo-local skill entry
- 选一个你当前在用、且输出结构稳定的 skill 做最小读取确认
- 只确认 “skill entry 能被 Claude 读取，输出结构仍符合对应 skill 的固定契约”

判断标准：

- Claude 能读取对应 skill entry
- 输出仍符合固定结构
- 这一步是 backend runtime 可读性确认，不替代 source 与 target 对齐检查

## 三、和其他 backend 的区别

- `claude` 保留 runtime skill entry 可读性 smoke verify；`agents` 当前只承接 deploy verify 与 Codex Harness manual run，不再承接 skills mock / contract smoke
- `claude` 的常见 user-home runtime 路径是 `~/.claude/skills`，不依赖 `CODEX_HOME` 或 XDG 推导
- 当前仓库不提供 `claude` backend 的 deploy adapter CLI；如果未来恢复，必须以新的真实命令面更新文档

## 四、当前限制

- 不要在当前仓库使用 `adapter_deploy.py --backend claude`
- 这页只承接 Claude 的 runtime 路径与 smoke verify 差异，不承接 deploy 命令合同
