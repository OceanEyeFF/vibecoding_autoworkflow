---
title: "Context Entry 模板"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Context Entry 模板

> 目的：给 `Context Routing` 提供固定输出骨架，只回答“这轮任务开始前该读什么、不该先读什么”。

## 一、固定字段

- `task`
- `goal`
- `must_read`
- `optional_read`
- `do_not_read_yet`
- `code_entrypoints`
- `constraints`
- `handoff_notes`

## 二、模板

```md
# Context Entry

## task

- [一句话任务定义]

## goal

- [这份 route card 只服务的当前目标]

## must_read

1. [必须先读的文档或目录]
2. [必须先读的文档或目录]

## optional_read

- [只有在需要时再读的入口]

## do_not_read_yet

- [当前先不要读的目录、历史文档或运行态]

## code_entrypoints

- [相关代码入口]

## constraints

- [限读范围、禁止越界点或已知边界]

## handoff_notes

- [给执行层的简短说明]
```
