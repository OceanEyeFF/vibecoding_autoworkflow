---
title: "Harness Skill Catalog / Supervisor"
status: active
updated: 2026-04-20
owner: aw-kernel
last_verified: 2026-04-20
---
# Supervisor Skill Catalog

> 目的：固定顶层 Harness supervisor skill 的职责与当前承接位。

## 当前 canonical skill

### harness-skill

职责：

- 判断当前在 `RepoScope` 还是 `WorktrackScope`
- 在当前层级内按合法状态转移连续推进，直到命中正式 stop condition
- 优先消费下游 rounds 返回的结构化 route / continuation / approval 字段，而不是从 prose 猜下一步
- 汇总已完成的局部 rounds、证据、状态和下一步建议
- 只在 authority boundary 或其他 formal stop condition 停下并向 programmer 请求批准

canonical executable source：

- [../../../../product/harness/skills/harness-skill/SKILL.md](../../../../product/harness/skills/harness-skill/SKILL.md)

固定输出：

- `Harness Turn Report`

preferred continuation fields：

- `allowed_next_routes`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_scope`
- `approval_reason`

兼容说明：

- `recommended_next_action`
- `needs_approval`
- `approval_to_apply`

这些旧字段仍可保留为兼容投影，但不再应成为新的 canonical 读口。

说明：

- 这是当前唯一已经落地的 Harness canonical skill
- 其余 repo/worktrack skills 目前仍停留在 catalog target 层
