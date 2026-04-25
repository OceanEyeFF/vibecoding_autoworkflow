---
title: "Append Request"
status: active
updated: 2026-04-25
owner: aw-kernel
last_verified: 2026-04-25
---
# Append Request

管理外部追加请求的分类与路由，而不是直接执行追加内容。

`Append Request` 支持两个 mode：

- `append-feature`
- `append-design`

它的作用是把追加请求归入一个明确的控制路由：

- `goal change`
- `new worktrack`
- `scope expansion`
- `design-only`
- `design-then-implementation`

最少应包含：

- 原始追加请求与 mode
- 分类结果与分类理由
- 对 `Goal Charter` 的影响
- 对活跃 worktrack 范围的影响
- 建议下一路由与下一 scope
- suggested node type（如适用）
- 设计阶段与实现阶段边界（如适用）
- 权限边界与审批原因
- 最小缺失信息
- `approval_required`
- `continuation_ready`
- `continuation_blockers`

字段一致性：

- 当 `approval_required: true` 时，`continuation_ready` 必须为 `false`，除非输入事实中已经包含该审批的明确授权
- 当 `approval_required: true` 时，`continuation_blockers` 必须列出待审批项，并能对应到审批范围和审批原因
- 当分类置信度为 low，或最小缺失信息会阻塞分类、路由或授权判断时，`continuation_ready` 必须为 `false`
- 只有 `approval_required: false` 且没有阻塞性缺失信息时，`continuation_ready` 才可以为 `true`

硬约束：

- `Append Request` 不是 worktrack contract
- `Append Request` 不是 goal change request
- `Append Request` 不授权执行，只表达分类与路由
- 如果分类结果是 `goal change` 或 `scope expansion`，必须显式暴露审批边界
