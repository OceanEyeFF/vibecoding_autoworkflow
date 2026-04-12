---
title: "Codex Repo-local Usage Help"
status: active
updated: 2026-04-12
owner: aw-kernel
last_verified: 2026-04-12
---
# Codex Repo-local Usage Help

> 目的：把 `agents` backend 在当前仓库的 repo-local 使用帮助收成一页，并按 `Memory Side` 与 `Task Interface` 分节说明。

先建立通用边界，再读本页：

- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Skill Deployment 维护流](../runbooks/skill-deployment-maintenance.md)

## 一、共用 deploy 入口

本地挂载：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

全局安装：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --dry-run
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root ~/.codex/skills
```

共用原则：

- `.agents/skills/` 是 repo-local deploy target，不是 source of truth
- adapter 源码只改 `product/`
- smoke verify 只做最小可用性确认，不扩成研究评测

## 二、Memory Side

源码与真相落点：

- canonical docs：`docs/knowledge/memory-side/`
- canonical skills：`product/memory-side/skills/`
- adapter 源码：`product/memory-side/adapters/agents/`

最小 smoke verify：

- 显式调用 `.agents/skills/` 下的 `context-routing-skill`、`knowledge-base-skill` 或 `writeback-cleanup-skill`
- 只确认 backend 能读取 wrapper，且输出仍符合固定格式

## 三、Task Interface

源码与真相落点：

- canonical docs：`docs/knowledge/task-interface/`
- canonical skills：`product/task-interface/skills/`
- adapter 源码：`product/task-interface/adapters/agents/`

最小 smoke verify：

- 显式调用 `.agents/skills/task-contract-skill`
- 只确认 backend 能读取 wrapper，且输出仍符合固定 `Task Contract` 结构
