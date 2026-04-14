---
title: "Harness 非目标"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Harness 非目标

> 目的：明确 Harness 不承担什么，防止控制平面与执行平面重新粘连。

Harness 不是：

- 直接执行编码的主体
- `Task Contract` 的上游真相层
- 某个 backend 的 repo-local runtime wrapper
- 只是把一组 skill 顺序串起来的 open-loop 流程图
- 可以在常规控制里随意改写目标的任务管理器

出现下面这些表述时，应默认视为边界错误：

- “Harness 自己把任务做完”
- “Harness 本体等于 memory-side”
- “Task Contract 属于 Harness 本体”
- “只要串好 workflow asset 就等于 Harness”
