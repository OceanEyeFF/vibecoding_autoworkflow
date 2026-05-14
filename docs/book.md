---
title: "Docs Book Spine"
status: active
updated: 2026-05-14
owner: aw-kernel
last_verified: 2026-05-14
---
# Docs Book Spine

`docs/book.md` 是 `docs/` 的 canonical book-style spine：它定义阅读顺序、章节边界和新增文档的放置判断。`docs/README.md` 只做入口导航；具体规则正文仍以对应章节内的承接文档为准。

Owner：`aw-kernel`。边界：只覆盖 `docs/` 的文档分层与阅读路线，不替代 `AGENTS.md` 的 agent boot 规则，不承接 `product/` 源码合同或 `toolchain/` 脚本合同。

## Chapter Order

1. [Project Maintenance](./project-maintenance/README.md)
2. [Harness](./harness/README.md)
3. Analysis
4. Ideas
5. Archive

默认阅读从 `docs/README.md` 进入本页，再按任务目标跳到最近章节入口；不要为同一主题在多个章节建立并行主线。

## Chapter Boundaries

### 1. Project Maintenance

`docs/project-maintenance/` 承接 operator-facing 项目维护：根目录分层、review/verify/gate 治理、部署 runbook、测试入口、backend usage help 和 repo onboarding。

新文档属于这里，当它回答的是“这个仓库如何维护、验证、部署、接入或使用”。涉及长期治理规则时，优先进入 `governance/`；涉及目录边界时，优先进入 `foundations/`；涉及命令运行或 smoke 时，优先进入 `testing/`。

### 2. Harness

`docs/harness/` 承接 Harness-first 主线：doctrine、runtime protocol、scope、artifact contract、skill catalog、workflow families 和设计分析。

Harness 子章节放置规则：

- `foundations/`：Harness 指导思想、运行协议、跨 skill 公共约束和执行载体选择策略。
- `scope/`：`RepoScope`、`WorktrackScope` 与状态闭环。
- `artifact/`：Harness 正式对象合同，包括 repo/worktrack/control artifact 与标准字段。
- `catalog/`：Codex 语境下的 skill catalog、控制层级映射和 skill 影响矩阵；可执行源仍归 `product/harness/skills/`。
- `workflow-families/`：可复用流程族、policy profile 和标准 worktrack 路线。
- `design/`：尚未升格为 doctrine、artifact contract 或 workflow family 的 Harness 设计方案与变更分析。

新文档属于这里，当它回答的是“Harness 如何思考、调度、记录证据、判定、交接或沉淀 workflow”。已验证并需要长期承接的设计，应升格到对应 foundations、artifact 或 workflow family 章节。

### 3. Analysis

`docs/analysis/` 承接已整理但尚未升格为主线规则的分析材料。它适合放比较、调研、问题拆解和决策输入，不应承接稳定执行规则。

如果分析结论变成项目维护规则，升格到 `project-maintenance/`；如果变成 Harness doctrine、artifact 或 workflow 规则，升格到 `harness/`。

### 4. Ideas

`docs/ideas/` 承接未承诺实施的想法、探索方向和早期方案草稿。这里的内容不能作为执行依据，也不能替代 active 文档。

当想法进入计划或实现，应迁移到 `analysis/`、`project-maintenance/`、`harness/`、`product/` 或 `toolchain/` 的真实承接位，并清理旧入口。

### 5. Archive

`docs/archive/` 承接历史保留、退役方案和不再作为当前主线的上下文。归档内容必须清楚标记它不再是执行入口。

如果归档内容仍有共享价值但已经被替代，保留指向当前主线的迁移说明；没有共享价值的 scratch 草稿不应长期留在 `docs/`。

## Placement Checklist

新增或移动文档前，按顺序判断：

1. 它是维护/治理/部署/测试/usage 吗？放 `project-maintenance/`。
2. 它是 Harness doctrine、runtime、artifact、catalog、workflow 或设计吗？放 `harness/` 的最近子章节。
3. 它只是决策输入或调研吗？放 `analysis/`，并避免写成长期规则。
4. 它只是未承诺想法吗？放 `ideas/`，并避免成为执行入口。
5. 它已被替代但仍需保留上下文吗？放 `archive/`，并指回当前主线。

新增正文文档后，同步更新最近的 `README.md` 入口；若接管了新的稳定边界，也要清理旧入口，避免双份主线。
