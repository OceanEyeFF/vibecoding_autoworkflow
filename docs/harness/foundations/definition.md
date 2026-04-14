---
title: "Harness 定义"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Harness 定义

> 目的：固定 Harness 的上位定义，避免继续把它误写成普通任务流、repo-local runtime wrapper 或直接执行器。

## 一、总定义

**Harness 是对 Repo 演进过程进行分层闭环控制的系统。**

它在 `RepoScope` 上维护长期基线与系统不变量，在 `WorktrackScope` 上约束局部状态转移，并通过 `Evidence + Gate` 判断当前状态是否允许推进为新的基线。

## 二、控制对象

Harness 直接控制的不是每一行代码，而是：

- repo 与 worktrack 的状态转移合法性
- 当前状态相对目标的偏差与风险
- 证据是否足以支持继续推进
- 失败时应进入哪条恢复路径

## 三、边界

Harness 关注：

- 目标、状态、证据、裁决与恢复
- `RepoScope` 与 `WorktrackScope` 的关系
- 可推进与不可推进的条件

Harness 不直接等于：

- coding agent
- review agent
- repo-local runtime mount
- 某个 backend 的工作流包装器
