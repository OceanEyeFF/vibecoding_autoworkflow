---
title: "Codex Repo-local Usage Help"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Codex Repo-local Usage Help

> 目的：只保留 `agents` backend 的特有差异，回答 “global target 在哪、最小 smoke verify 怎么看、有哪些 backend 限制与命令差异”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与目标路径

- backend 名：`agents`
- repo-local target：`.agents/skills/`
- global target：`$CODEX_HOME/skills`
- 显式覆盖参数：`--agents-root`

说明：

- 如果没有 `--agents-root`，全局安装依赖 `CODEX_HOME`
- `verify --target global` 时，优先显式传 `--agents-root`

## 二、最小 smoke verify 口径

当前只建议做最小 wrapper 可读性确认：

- `Memory Side`：显式调用 `.agents/skills/` 下的 `context-routing-skill`、`knowledge-base-skill` 或 `writeback-cleanup-skill`
- `Task Interface`：显式调用 `.agents/skills/task-contract-skill`

判断标准：

- Codex 能读取对应 wrapper
- 输出仍符合固定结构

## 三、Backend 限制

- 本页不重复通用 local / global deploy 流程
- `.agents/skills/` 是 repo-local deploy target，不是 source of truth
- 变更仍应先改 `product/`，再通过 deploy 同步到 target

## 四、命令差异

全局安装或复验时，`agents` backend 的差异只有 target root 参数：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root ~/.codex/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root ~/.codex/skills
```
