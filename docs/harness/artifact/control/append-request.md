---
title: "Append Request"
status: active
updated: 2026-04-25
owner: aw-kernel
last_verified: 2026-04-25
---
# Append Request

管理外部追加请求（append-feature / append-design）的分类与路由，将其归入 goal change、new worktrack、scope expansion、design-only 或 design-then-implementation，而不是直接执行追加内容。

最少应包含：原始请求与 mode、分类结果与理由、对 Goal Charter 和活跃 worktrack 的影响、下一路由与 scope、suggested node type（如适用）、设计/实现阶段边界（如适用）、权限边界与审批原因、最小缺失信息、approval_required、continuation_ready、continuation_blockers。

字段一致性：approval_required: true 时 continuation_ready 必须为 false（除非已含明确授权）且 continuation_blockers 必须列出待审批项；分类置信度 low 或缺失信息阻塞分类/路由/授权时 continuation_ready 必须为 false；只有 approval_required: false 且无阻塞性缺失信息时才能为 true。

硬约束：Append Request 不是 worktrack contract 或 goal change request；不授权执行，只表达分类与路由；分类结果为 goal change 或 scope expansion 时必须显式暴露审批边界。
