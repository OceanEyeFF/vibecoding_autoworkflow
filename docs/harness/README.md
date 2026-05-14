# Harness

`docs/harness/` 是当前仓库的 Harness-first 文档主线，承接 Harness doctrine、runtime protocol、scope、artifact contracts、skill inventory、workflow family policy 与设计分析。

## 当前分层

- [foundations/README.md](./foundations/README.md)：指导思想与运行协议主文档，承接 doctrine、runtime protocol 和跨 skill 公共约束
- [scope/README.md](./scope/README.md)：`RepoScope`、`WorktrackScope` 与状态闭环
- [artifact/README.md](./artifact/README.md)：Harness 依赖的正式对象与 artifact contract
  - [artifact/control/node-type-registry.md](./artifact/control/node-type-registry.md)：Node Type Registry，定义所有 Worktrack 节点类型的默认规则，是 Goal Charter、Worktrack Contract 和 gate-skill 的统一引用上游
  - [artifact/control/milestone.md](./artifact/control/milestone.md)：Milestone Artifact，RepoScope 下的聚合对象 / 控制条件 / progress counter，不创建第三 Scope
  - [artifact/worktrack/dispatch-packet.md](./artifact/worktrack/dispatch-packet.md)：Dispatch Packet Schema，统一 `schedule-worktrack-skill -> dispatch-skills -> SubAgent` 链路的 Task Brief / Info Packet / Result 三层字段定义
- [catalog/README.md](./catalog/README.md)：`Codex` 语境下直接可消费的 Harness skill inventory，只记录 skill 入口、职责摘要、控制层级、状态和 canonical executable source
  - [catalog/milestone-status-skill.md](./catalog/milestone-status-skill.md)：Milestone Status Skill，独立 Milestone 分析器，RepoScope 下的聚合观测/验收分析器
  - [catalog/skill-impact-matrix.md](./catalog/skill-impact-matrix.md)：Skill Impact Matrix，历史同步分析，当前留在 catalog 下仅作为待迁移清单；目标承接位见 [catalog/README.md](./catalog/README.md)
- [workflow-families/README.md](./workflow-families/README.md)：可复用 workflow family、route pattern 与 policy profile

## 阅读边界

- 查 Harness 为什么这样运行、运行时怎样停顿/交接/继续：读 `foundations/`
- 查运行时对象字段、证据、队列、control state 或 milestone/worktrack 合同：读 `artifact/`
- 查有哪些 skill、每个 skill 的职责摘要和 executable source：读 `catalog/`
- 查一组 worktrack 如何组成可复用流程或 policy profile：读 `workflow-families/`
- 查尚未升格的方案比较、影响分析或迁移设计：读 `design/`
- 查可执行 skill 源文件：读 [../../product/harness/skills/README.md](../../product/harness/skills/README.md)

`catalog/` 不承接 doctrine、runtime protocol、artifact contract、workflow policy、设计分析或 executable source。若 catalog 页面为了定位 skill 而引用这些内容，只能作为摘要和反向链接；权威正文仍在上述 owner。

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
- 在 `Codex` 语境下，Harness 直接以 skill inventory 表达，不再维持一层独立的 `function -> skill` 转译目录
- Harness executable source 进入 [../../product/harness/skills/README.md](../../product/harness/skills/README.md)，但 doctrine、runtime protocol、artifact contract 与 workflow policy 仍以上游文档真相为准

## 迁移边界

- [../../product/harness/README.md](../../product/harness/README.md) 作为干净重建的 executable root，只承接实现层，不承接 ontology 正文
- 当前仓库中的 Harness 主线以 `docs/harness/` 为准；如果需要可执行 skill source，应优先落到 [../../product/harness/skills/README.md](../../product/harness/skills/README.md)

建议阅读顺序由 [AGENTS.md](../../AGENTS.md) 统一定义。
