---
title: "控制平面与执行平面"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# 控制平面与执行平面

> 目的：固定 Harness 属于控制平面，而不是执行平面。

## 一、控制平面

Harness 负责：

- 决定下一步做什么
- 决定需要哪些证据
- 决定当前状态能否继续推进
- 在失败时安排恢复动作

## 二、执行平面

执行平面负责：

- 实际编码
- 实际 review
- 实际测试
- 实际合并、回滚、清理

## 三、约束

- 执行器可以是 human developer、coding agent、review agent 或 automation
- 执行器是被 Harness 调度的对象，不等于 Harness 本体
- `dispatch-subtask`、`execute-via-agent` 这类动作属于控制平面语言；它们不应被写成 “Harness 自己做工作”
