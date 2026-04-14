# Harness Core Contracts

这里预留给 Harness core 的正式 contract 载体。

当前阶段：

- doctrine 与 artifact 先在 `docs/harness/` 固化
- legacy 可回收资产仍在 `product/harness-operations/skills/`

当前回收映射：

| legacy asset | 处理方式 | 目标责任 |
|---|---|---|
| `execution-contract-template` | `split` | execution/worktrack contract scaffold |
| `harness-contract-shape` | `split` | harness contract JSON shape、workflow metadata、scope fields |
| `task-planning-contract` | `split` | task inventory、dependency graph、batch guidance 的 contract 片段 |

本目录承接的是“稳定 contract 形状”，不是完整 workflow 编排。
