---
title: "Observe"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Observe

`Observe` 负责采集当前状态，而不是直接下结论。

典型输入：

- repo snapshot
- branch / diff metadata
- review / test / rule-check 结果

典型输出：

- 可供 `Decide` 或 `Judge` 消费的状态描述
