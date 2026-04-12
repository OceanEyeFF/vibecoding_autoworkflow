---
title: "OpenCode Repo-local Usage Help"
status: active
updated: 2026-04-12
owner: aw-kernel
last_verified: 2026-04-12
---
# OpenCode Repo-local Usage Help

> 目的：把 `opencode` backend 在当前仓库的 repo-local 使用帮助收成一页，并按 `Memory Side` 与 `Task Interface` 分节说明。

先建立通用边界，再读本页：

- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Skill Deployment 维护流](../runbooks/skill-deployment-maintenance.md)

## 一、共用 deploy 入口

本地挂载：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

全局安装：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --dry-run
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```

共用原则：

- `.opencode/skills/` 是 repo-local deploy target，不是 source of truth
- adapter 源码只改 `product/`
- 当前只把 `sync verify` 写成稳定维护动作，不夸大 runtime smoke

## 二、Memory Side

源码与真相落点：

- canonical docs：`docs/knowledge/memory-side/`
- canonical skills：`product/memory-side/skills/`
- adapter 源码：`product/memory-side/adapters/opencode/`

当前边界：

- 只确认 deploy sync 成立
- 不把 OpenCode 写成已经具备稳定 `Memory Side` smoke verify 口径

## 三、Task Interface

源码与真相落点：

- canonical docs：`docs/knowledge/task-interface/`
- canonical skills：`product/task-interface/skills/`
- adapter 源码：`product/task-interface/adapters/opencode/`

当前边界：

- 只确认 deploy sync 成立
- 不把 OpenCode 写成已经具备稳定 `task-contract-skill` smoke verify 口径
