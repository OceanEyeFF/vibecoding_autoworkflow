---
title: "Repo Discovery Input"
status: active
updated: 2026-04-25
owner: aw-kernel
last_verified: 2026-04-25
---
# Repo Discovery Input

`Repo Discovery Input` 是 Existing Code Project Adoption 模式下的只读事实输入，用来记录 Harness 初始化前对既有代码库的观察结果。

它的运行落位是 `.aw/repo/discovery-input.md`。

## Purpose

这个 artifact 只承接“当前看见了什么”：

- 现有目录、模块、入口、构建与测试线索
- 已存在的文档、约定、配置、脚本和治理提示
- 当前分支、基线、未提交变更和已知风险
- 从代码、文档或用户说明中直接可追溯的事实
- 待用户确认的问题和不确定点

它不承接“项目应该变成什么”。长期目标、成功标准和系统不变量只能进入 `goal-charter.md`，并且必须经过用户确认。

## Non-Authority

`discovery-input.md` 不是 goal truth，也不是 Harness 控制状态。

因此：

- 不得把推测性的产品愿景写成已确认目标
- 不得把现有实现倒推成用户同意的长期方向
- 不得替代 `goal-charter.md`
- 不得替代 `repo/snapshot-status.md`
- 不得直接驱动 worktrack 拆分
- 不得作为覆盖用户目标的依据

如果 discovery 与后续用户确认冲突，以用户确认后的 `goal-charter.md` 为准；如果 discovery 与后续观测冲突，以刷新后的 `repo/snapshot-status.md` 为准。

## Relationship To Other Repo Artifacts

### `goal-charter.md`

`discovery-input.md` 可以作为 `set-harness-goal-skill` 起草 goal charter 的事实依据，但只能提供候选信息。`goal-charter.md` 是用户确认后的长期目标 truth。

### `repo/snapshot-status.md`

`discovery-input.md` 是初始化前的采集输入。`repo/snapshot-status.md` 是 Harness 初始化后的 repo 慢变量观测面，可以引用 discovery 作为来源，但应按当前确认状态重写、归纳或纠正。

### `control-state.md`

`control-state.md` 只记录 Harness supervisor 当前控制状态。它可以在 `Linked Formal Documents` 或 `Notes` 中链接 `.aw/repo/discovery-input.md` 作为 adoption 证据，但不得把 discovery 字段提升为控制指令。

## Minimum Shape

`discovery-input.md` 最少应包含：

- metadata
- adoption mode
- source materials
- repository facts
- architecture and module inventory
- build, test, and runtime signals
- governance and documentation signals
- risks and unknowns
- candidate goal signals
- confirmation questions
- downstream mapping notes

`candidate goal signals` 只能写可追溯候选项，不能写成已批准目标。
