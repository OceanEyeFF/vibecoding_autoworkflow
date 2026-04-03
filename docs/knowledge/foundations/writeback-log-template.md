---
title: "Writeback Log 模板"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Writeback Log 模板

> 目的：给 `Writeback & Cleanup` 提供固定回写骨架，只回答“本轮验证后该写回什么、清理什么”。

## 一、固定字段

- `task`
- `summary`
- `validated`
- `not_changed`
- `knowledge_updates`
- `cleanup_actions`
- `residual_risks`
- `followups`

## 二、模板

```md
# Writeback Log

## task

- [对应任务]

## summary

- [本轮确认完成的变更]

## validated

- [已执行的验证]

## not_changed

- [明确没有改动的边界]

## knowledge_updates

- [已更新或仍需更新的知识入口]

## cleanup_actions

- [已清理的旧入口、旧 prompt、旧假设或临时对象]

## residual_risks

- [仍保留的风险]

## followups

- [后续任务或人工动作]
```
