---
title: "Memory Side Skill 与 Agent 模型"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Memory Side Skill 与 Agent 模型

> 目的：定义 `Memory Side` 中合同正文、Skill 与可选调用层的关系，并说明它作为 Harness adjacent system 如何与 `Task Contract` 衔接。

`Memory Side` 当前固定 3 个 Skill：

- `knowledge-base-skill`
- `context-routing-skill`
- `writeback-cleanup-skill`

它们对应：

| Skill | 对应分区 | 核心产物 |
|---|---|---|
| `knowledge-base-skill` | `Knowledge Base` | 文档体系判断、主线入口修正 |
| `context-routing-skill` | `Context Routing` | `Route Card` |
| `writeback-cleanup-skill` | `Writeback & Cleanup` | `Writeback Card` |

衔接约束：

- `Task Contract` 是独立 adjacent system 对象
- Harness 可以消费 `Task Contract / Route Card / Writeback Card`
- 但 Harness 不应把这些对象改写成自己的 ontology 本体
