# Harness

`docs/harness/` 是当前仓库的 Harness-first 文档主线，负责承接 Harness doctrine、scope、artifact、skills catalog 与 workflow families。

## 当前分层

- [foundations/README.md](./foundations/README.md)：指导思想与运行协议主文档
- [scope/README.md](./scope/README.md)：`RepoScope`、`WorktrackScope` 与状态闭环
- [artifact/README.md](./artifact/README.md)：Harness 依赖的正式对象
- [design/README.md](./design/README.md)：Harness 设计方案与变更分析入口
- [catalog/README.md](./catalog/README.md)：`Codex` 语境下直接可消费的 Harness skill catalog
- [workflow-families/README.md](./workflow-families/README.md)：可复用 workflow family 与 policy profile

## 当前主张

- `Harness` 升为一级认知与文档域
- 当前不再保留旧的 `function/` 与 `governance/` 噪声拆分；相关层将在后续按新 ontology 重做
- `memory-side`、`task-interface` 与 `docs/harness/adjacent-systems/` 已退役；已批准输入收束进 Worktrack artifact，路由与写回规则由 `AGENTS.md` 和项目维护治理承接
- 在 `Codex` 语境下，Harness 直接以 skills catalog 表达，不再维持一层独立的 `function -> skill` 转译目录
- Harness executable source 进入 [../../product/harness/README.md](../../product/harness/README.md)，但 doctrine 仍以上游文档真相为准

## 迁移边界

- [../../product/harness/README.md](../../product/harness/README.md) 作为干净重建的 executable root，只承接实现层，不承接 ontology 正文
- 当前仓库中的 Harness 主线以 `docs/harness/` 为准；如果需要可执行 skill source，应优先落到 `product/harness/`

建议阅读顺序由 [AGENTS.md](../../AGENTS.md) 统一定义。
