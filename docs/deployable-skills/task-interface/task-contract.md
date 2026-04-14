---
title: "Task Contract 基线"
status: superseded
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Task Contract 基线

> 本页已降级为 legacy 副本。canonical 文档已迁到 [../../harness/adjacent-systems/task-interface/task-contract.md](../../harness/adjacent-systems/task-interface/task-contract.md)。

> 目的：定义 `Task Contract` 作为 `Task Interface` 对象的职责和边界，并说明它如何被固定为可直接调用的 skill 载体，而不把它并入 `Memory Side`。

## 一、对象

`Task Contract`

## 二、角色

- 位于 `discussion -> execution` 之间
- 把讨论压缩成唯一正式执行基线
- 为 `Context Routing`、执行层和 `Writeback & Cleanup` 提供同一份上游边界

## 三、它不是什么

- 不是 `Memory Side` 组件
- 不是产品功能设计
- 不是后端服务模块
- 不是宿主运行时编排器
- 不是客户端专属调用逻辑
- 不是 repo-local execution template layer

## 四、输入与输出

输入：

- 已收敛的用户讨论
- 当前仓库主线约束
- 必要时使用 `Context Routing` 已确定的最小入口

输出：

- 一份固定结构的 `Task Contract`
- 其中明确：
  - `confirmed`
  - `pending`
  - 任务范围
  - 非目标
  - 验收
  - 依赖
  - 风险
  - 验证要求

## 五、当前最合适的载体

当前仓库中，`Task Contract` 由两类载体承载：

- `docs/deployable-skills/task-interface/task-contract.md`
- `product/task-interface/skills/task-contract-skill/`

说明：

- 本文负责固定结构与字段约束
- canonical skill package 负责把同一结构变成可直接调用的稳定能力
- 两者都属于 `Task Interface`，不属于 `Memory Side`
- Harness Operations workflows 可以消费这份基线，但不能把它改写成自己的 truth

## 六、固定输出结构

每份 `Task Contract` 至少包含下面 5 个部分：

1. `Task Contract Role`
2. `Project Baseline`
3. `Current Task Contract`
4. `Open Decisions`
5. `Downstream Consumption`

其中 `Current Task Contract` 至少包含下面字段：

- `task`
- `goal`
- `non_goals`
- `in_scope`
- `out_of_scope`
- `acceptance_criteria`
- `constraints`
- `dependencies`
- `risks`
- `verification_requirements`

## 七、不做什么

- 不直接进入编码
- 不直接分配 agents
- 不直接生成多步执行计划
- 不把 `Route Card` 或 `Writeback Card` 混入本体
- 不基于猜测补全缺失事实

## 八、当前仓库中的落点

```text
docs/deployable-skills/
  task-interface/
    task-contract.md

docs/project-maintenance/
  usage-help/  # repo-local backend usage help

product/
  task-interface/
    skills/
      task-contract-skill/
    adapters/
      agents/
      claude/
  harness-operations/
    skills/
      execution-contract-template/
      task-planning-contract/
```

## 九、判断标准

如果下面几句话成立，说明 `Task Contract` 的基线是清楚的：

- 它能稳定收束讨论，而不是复制讨论碎片
- 它能作为执行前唯一正式基线
- 它能被不同后端用同一套结构消费
- 它不会被误写成 `Memory Side` 组件或 runtime 方案

## 十、相关文档

- [根目录分层](../../project-maintenance/foundations/root-directory-layering.md)
- [task-contract-skill/SKILL.md](../../../product/task-interface/skills/task-contract-skill/SKILL.md)
- [task-contract-skill/references/entrypoints.md](../../../product/task-interface/skills/task-contract-skill/references/entrypoints.md)
- [Usage Help 总入口](../../project-maintenance/usage-help/README.md)
- [Codex Repo-local Usage Help](../../project-maintenance/usage-help/codex.md)
- [Claude Repo-local Usage Help](../../project-maintenance/usage-help/claude.md)
- [Memory Side 总览](../memory-side/overview.md)
