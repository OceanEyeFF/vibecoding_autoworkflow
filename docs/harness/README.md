# Harness

`docs/harness/` 是当前仓库的 Harness-first 文档主线，承接 Harness doctrine、scope、artifact、skills catalog 与 workflow families。

## 当前分层

- [foundations/README.md](./foundations/README.md)：指导思想与运行协议主文档
- [scope/README.md](./scope/README.md)：`RepoScope`、`WorktrackScope` 与状态闭环
- [artifact/README.md](./artifact/README.md)：Harness 依赖的正式对象
  - [artifact/control/node-type-registry.md](./artifact/control/node-type-registry.md)：Node Type Registry，定义所有 Worktrack 节点类型的默认规则，是 Goal Charter、Worktrack Contract 和 gate-skill 的统一引用上游
  - [artifact/control/milestone.md](./artifact/control/milestone.md)：Milestone Artifact，RepoScope 下的聚合对象 / 控制条件 / progress counter，不创建第三 Scope
  - [artifact/worktrack/dispatch-packet.md](./artifact/worktrack/dispatch-packet.md)：Dispatch Packet Schema，统一 `schedule-worktrack-skill -> dispatch-skills -> SubAgent` 链路的 Task Brief / Info Packet / Result 三层字段定义
- [catalog/README.md](./catalog/README.md)：`Codex` 语境下直接可消费的 Harness skill catalog
  - [catalog/milestone-status-skill.md](./catalog/milestone-status-skill.md)：Milestone Status Skill，独立 Milestone 分析器，RepoScope 下的聚合观测/验收分析器
  - [catalog/skill-impact-matrix.md](./catalog/skill-impact-matrix.md)：Skill Impact Matrix，Harness 合同变更对 canonical skills 的影响分析与同步追踪
- [workflow-families/README.md](./workflow-families/README.md)：可复用 workflow family 与 policy profile

## 设计文档

`docs/harness/design/` 承接尚未升格为长期 doctrine、artifact contract 或 workflow family 的 Harness 设计方案与变更分析。

当前入口：
- [design/skills-handback-improvements.md](./design/skills-handback-improvements.md)：Skills 层 handback 改进方案

升格规则：
- 已验证并需要长期承接的 doctrine，升格到 [foundations/README.md](./foundations/README.md)
- 已验证并影响正式对象结构的合同，升格到 [artifact/README.md](./artifact/README.md)
- 已验证并影响可复用流程的规则，升格到 [workflow-families/README.md](./workflow-families/README.md)

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
