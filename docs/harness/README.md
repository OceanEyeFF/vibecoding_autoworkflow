# Harness

`docs/harness/` 是当前仓库的 Harness-first 文档主线，负责承接 Harness doctrine、scope/function/artifact/governance、adjacent systems 与 workflow families。

## 当前分层

- [foundations/README.md](./foundations/README.md)：总定义、非目标、被控变量与控制平面边界
- [scope/README.md](./scope/README.md)：`RepoScope`、`WorktrackScope` 与状态闭环
- [function/README.md](./function/README.md)：控制器在不同阶段的动作语义
- [artifact/README.md](./artifact/README.md)：Harness 依赖的正式对象
- [governance/README.md](./governance/README.md)：裁决、授权、非法转移、恢复与 closeout 规则
- [adjacent-systems/README.md](./adjacent-systems/README.md)：`Task Interface` 与 `Memory Side` 的相邻系统入口
- [workflow-families/README.md](./workflow-families/README.md)：可复用 workflow family 与 policy profile

## 当前主张

- `Harness` 升为一级认知与文档域
- 文档树按 `Scope / Function / Artifact / Governance` 组织，而不是按旧 skill 包名组织
- `memory-side` 与 `task-interface` 不再被表述为 Harness 本体，而是 Harness 的 adjacent systems
- 已验证的 legacy skills 先降级为可回收资产，再围绕 Harness 重建 ontology

## 迁移边界

- `docs/deployable-skills/` 只保留迁移期兼容导航与 legacy asset，不再新增新的主线 doctrine
- `product/memory-side/` 与 `product/task-interface/` 第一阶段继续保留独立源码根
- `product/harness-operations/` 仍保留 legacy canonical skill 与 adapter source，直到 `product/harness/` 的分层替代到位

建议阅读顺序由 [AGENTS.md](../../AGENTS.md) 统一定义。
