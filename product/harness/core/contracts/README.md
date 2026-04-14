# Harness Core Contracts

这里承接 Harness core 的正式 contract 载体。

当前 extracted source：

- [execution-contract.template.md](./execution-contract.template.md)
- [harness-contract.template.json](./harness-contract.template.json)
- [task-planning-contract.template.md](./task-planning-contract.template.md)

当前回收映射：

| legacy asset | 处理方式 | 目标责任 |
|---|---|---|
| `execution-contract-template` | `split` | execution/worktrack contract scaffold |
| `harness-contract-shape` | `split` | harness contract JSON shape、workflow metadata、scope fields |
| `task-planning-contract` | `split` | task inventory、dependency graph、batch guidance 的 contract 片段 |

迁移约束：

- deploy source 仍保持在 `product/harness-operations/skills/*/prompt.md`
- 本目录承接的是稳定 contract 形状，不是完整 workflow 编排
