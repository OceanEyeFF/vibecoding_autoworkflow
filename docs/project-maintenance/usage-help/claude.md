---
title: "Claude Repo-local Usage Help"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Claude Repo-local Usage Help

> 目的：只保留 `claude` backend 的特有差异，回答 “global target 在哪、最小 smoke verify 怎么看、有哪些 backend 限制与命令差异”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与目标路径

- backend 名：`claude`
- repo-local target：`.claude/skills/`
- global target：`~/.claude/skills`
- 显式覆盖参数：`--claude-root`

说明：

- Claude 全局安装默认落到 `~/.claude/skills`
- `verify --target global` 时，优先显式传 `--claude-root`

## 二、最小 smoke verify 口径

当前只建议做最小 wrapper 可读性确认：

- `Memory Side`：显式调用 `.claude/skills/` 下的 `context-routing-skill`、`knowledge-base-skill` 或 `writeback-cleanup-skill`
- `Task Interface`：显式调用 `.claude/skills/task-contract-skill`

判断标准：

- Claude 能读取对应 wrapper
- 输出仍符合固定结构

## 三、Backend 限制

- 本页不重复通用 local / global deploy 流程
- `.claude/skills/` 是 repo-local deploy target，不是 source of truth
- 当前优先稳定读取顺序和输出结构，不先扩复杂编排

## 四、命令差异

全局安装或复验时，`claude` backend 的差异只有 target root 参数：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
```
