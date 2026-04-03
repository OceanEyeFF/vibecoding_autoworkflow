---
title: "Decision Record 模板"
status: active
updated: 2026-04-03
owner: aw-kernel
last_verified: 2026-04-03
---
# Decision Record 模板

> 目的：给 `Knowledge Base` 中的决策记录提供固定格式，只回答“做了什么决策、为什么、影响什么”。

## 一、固定字段

- `decision`
- `status`
- `date`
- `owners`
- `context`
- `decision_detail`
- `consequences`
- `related_artifacts`

## 二、模板

```md
# Decision Record

## decision

- [决策标题]

## status

- [proposed | accepted | superseded]

## date

- [YYYY-MM-DD]

## owners

- [owner]

## context

- [决策前提和问题背景]

## decision_detail

- [最终决定]

## consequences

- [正向影响]
- [代价或约束]

## related_artifacts

- [相关文档、代码或 runbook]
```
