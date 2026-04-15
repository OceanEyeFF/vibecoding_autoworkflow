# Harness

`docs/harness/` 是当前仓库的 Harness-first 文档主线，负责承接 Harness doctrine、scope、artifact、skills、adjacent systems 与 workflow families。

## 当前分层

- [foundations/README.md](./foundations/README.md)：指导思想与运行协议主文档
- [scope/README.md](./scope/README.md)：`RepoScope`、`WorktrackScope` 与状态闭环
- [artifact/README.md](./artifact/README.md)：Harness 依赖的正式对象
- [Skills/README.md](./Skills/README.md)：`Codex` 语境下直接可消费的 Harness skill catalog
- [adjacent-systems/README.md](./adjacent-systems/README.md)：`Task Interface` 与 `Memory Side` 的相邻系统入口
- [workflow-families/README.md](./workflow-families/README.md)：可复用 workflow family 与 policy profile

## 当前主张

- `Harness` 升为一级认知与文档域
- 当前不再保留旧的 `function/` 与 `governance/` 噪声拆分；相关层将在后续按新 ontology 重做
- `memory-side` 与 `task-interface` 不再被表述为 Harness 本体，而是 Harness 的 adjacent systems
- 在 `Codex` 语境下，Harness 直接以 skills catalog 表达，不再维持一层独立的 `function -> skill` 转译目录
- Harness executable source 进入 [../../product/harness/README.md](../../product/harness/README.md)，但 doctrine 仍以上游文档真相为准

## 迁移边界

- [../../product/harness/README.md](../../product/harness/README.md) 作为干净重建的 executable root，只承接实现层，不承接 ontology 正文
- `memory-side` 与 `task-interface` 当前只保留在 `docs/harness/adjacent-systems/` 的合同层，不再保留独立的 `product/` 源码根
- 当前仓库中的 Harness 主线以 `docs/harness/` 为准；如果需要可执行 skill source，应优先落到 `product/harness/` 或对应 adjacent systems

建议阅读顺序由 [AGENTS.md](../../AGENTS.md) 统一定义。
