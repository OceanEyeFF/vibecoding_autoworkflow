---
title: "Memory Side 层级边界"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Memory Side 层级边界

> 目的：把 `Memory Side` 的通用合同、业务源码、repo-local 部署结果和工具资产拆开，同时把它从 Harness 本体中分离出来。

当前至少区分四层：

1. 通用合同层
   - 定义能力模型、输入输出和边界
2. 业务源码层
   - `product/memory-side/skills/` 与 `product/memory-side/adapters/`
3. 仓库实现层
   - `docs/project-maintenance/usage-help/`
   - `toolchain/scripts/deploy/adapter_deploy.py`
4. Repo-local deploy target
   - `.agents/skills/`
   - `.claude/skills/`
   - `.opencode/skills/`

硬要求：

- deploy target 不是 source of truth
- repo-local guide 不是跨仓库通用合同
- `Memory Side` 作为 adjacent system 进入 `docs/harness/adjacent-systems/`
