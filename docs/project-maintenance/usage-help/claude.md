---
title: "Claude Repo-local Usage Help"
status: active
updated: 2026-04-12
owner: aw-kernel
last_verified: 2026-04-12
---
# Claude Repo-local Usage Help

> 目的：把 `claude` backend 在当前仓库的 repo-local 使用帮助收成一页，并按 `Memory Side` 与 `Task Interface` 分节说明。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Memory Side 层级边界](../../deployable-skills/memory-side/layer-boundary.md)
- [Task Contract 基线](../../deployable-skills/task-interface/task-contract.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)

## 一、共用 deploy 入口

本地挂载：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
```

全局安装：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --dry-run
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
```

共用原则：

- `.claude/skills/` 是 repo-local deploy target，不是 source of truth
- adapter 源码只改 `product/`
- Claude 侧优先稳定读取顺序和输出结构，不先扩复杂编排

## 二、Memory Side

源码与真相落点：

- canonical docs：`docs/deployable-skills/memory-side/`
- canonical skills：`product/memory-side/skills/`
- adapter 源码：`product/memory-side/adapters/claude/`

最小 smoke verify：

- 显式调用 `.claude/skills/` 下的 `context-routing-skill`、`knowledge-base-skill` 或 `writeback-cleanup-skill`
- 只确认 Claude 能读取 wrapper，且输出仍符合固定格式

## 三、Task Interface

源码与真相落点：

- canonical docs：`docs/deployable-skills/task-interface/`
- canonical skills：`product/task-interface/skills/`
- adapter 源码：`product/task-interface/adapters/claude/`

最小 smoke verify：

- 显式调用 `.claude/skills/task-contract-skill`
- 只确认 Claude 能读取 wrapper，且输出仍符合固定 `Task Contract` 结构
