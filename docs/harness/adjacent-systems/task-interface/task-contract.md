---
title: "Task Contract 基线"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Task Contract 基线

> 目的：定义 `Task Contract` 作为 `Task Interface` 对象的职责和边界，并明确它是 Harness 的 adjacent-system 输入，而不是 Harness 本体。

## 一、对象

`Task Contract`

## 二、角色

- 位于 `discussion -> execution` 之间
- 把讨论压缩成唯一正式执行基线
- 为 Harness、`Context Routing`、执行层和 `Writeback & Cleanup` 提供同一份上游边界

## 三、它不是什么

- 不是 Harness 本体
- 不是 `Memory Side` 组件
- 不是产品功能设计
- 不是宿主运行时编排器

## 四、输入与输出

输入：

- 已收敛的用户讨论
- 当前仓库主线约束
- 必要时使用 `Context Routing` 已确定的最小入口

输出：

- 一份固定结构的 `Task Contract`
- 其中明确任务、范围、非目标、验收、依赖、风险和验证要求

## 五、当前载体

- 本文负责固定结构与字段约束
- `product/task-interface/skills/task-contract-skill/` 负责 canonical executable 载体
- Harness 可以消费这份基线，但不能把它改写成自己的 truth
