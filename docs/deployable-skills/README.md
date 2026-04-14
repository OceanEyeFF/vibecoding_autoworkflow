# Deployable Skills

`docs/deployable-skills/` 当前只保留迁移期兼容角色，不再承接 Harness 总纲主入口。

新的主线已经迁到：

- [../harness/README.md](../harness/README.md)

当前这里保留的内容主要有两类：

- 尚未完全迁入 `docs/harness/adjacent-systems/` 的已验证 adjacent-system 合同
- 迁移期需要保留的 legacy navigation 与历史资产入口

当前兼容入口：

- [harness-operations/README.md](./harness-operations/README.md)：Harness 母文档与 legacy doctrine 资产
- [memory-side/README.md](./memory-side/README.md)：`Memory Side` 的 legacy 合同入口
- [task-interface/README.md](./task-interface/README.md)：`Task Interface` 的 legacy 合同入口
- [memory-side/formats/context-routing-output-format.md](./memory-side/formats/context-routing-output-format.md)
- [memory-side/formats/writeback-cleanup-output-format.md](./memory-side/formats/writeback-cleanup-output-format.md)
- [task-interface/task-contract.md](./task-interface/task-contract.md)
- [../../AGENTS.md](../../AGENTS.md)：当前统一阅读顺序与 route contract

迁移期约束：

- 新的 Harness doctrine 与主线结构不再写回这里
- 如果旧入口仍被保留，必须显式指向 `docs/harness/` 的新主线
- 兼容入口可以保留已验证资产，但不能伪装成新的 ontology 主入口

建议阅读顺序仍由 [AGENTS.md](../../AGENTS.md) 统一定义。
