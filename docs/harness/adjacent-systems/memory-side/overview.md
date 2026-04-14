---
title: "Memory Side 总览"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Memory Side 总览

> 目的：作为 `Memory Side` 的上位总览，说明它作为 Harness adjacent system 的角色、边界和三类核心能力。

`Memory Side` 只包含 3 个组件：

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

它负责两件事：

- 维护仓库内的项目长期记忆
- 为单次任务提供可读取、可回写的上下文边界

当前定位约束：

- `Memory Side` 不是 Harness 本体
- Harness 可以消费它提供的长期记忆、路由与写回结果
- `Task Contract` 仍是独立 adjacent system 对象，不并入 `Memory Side`

当前阶段，如果需要更细的 partition 正文与格式，请继续参考 legacy 路径：

- [../../../deployable-skills/memory-side/README.md](../../../deployable-skills/memory-side/README.md)
