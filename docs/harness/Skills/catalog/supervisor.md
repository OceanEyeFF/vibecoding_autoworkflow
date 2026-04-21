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
- 只有在 `Harness Control State` 显式授予 `post_contract_autonomy: delegated-minimal` 时，才允许在 `contract-boundary` 后自动开启一段同 goal 的最小 follow-up worktrack
- 在连续无状态增量的 handback rounds 上，应优先返回 `stable-handback`，而不是无限重跑同一观察链
- `stable-handback` 一旦成立，应把 runtime 保持在 `awaiting-handoff`，直到检测到明确 unlock signal，而不是后续 rounds 自行回到 executable flow

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
- `autonomous_continuation_used`
- `stable_handback_detected`
- `handback_state`
- `handback_lock_active`
- `unlock_signal_detected`

兼容说明：

- `recommended_next_action`
- `needs_approval`
- `approval_to_apply`

这些旧字段仍可保留为兼容投影，但不再应成为新的 canonical 读口。

说明：

- 这是当前唯一已经落地的 Harness canonical skill
- 其余 repo/worktrack skills 目前仍停留在 catalog target 层
- `contract-boundary` 后是否允许再开一段最小 bounded slice，不应靠 human 每轮重复写长 prompt，而应由 control-state 中的 `Continuation Authority` 策略位控制
- bare `继续工作` 不应天然清除 handback lock；没有新批准、没有新状态增量、没有新 control-state policy 时，supervisor 应稳定停在 handback / `awaiting-handoff`
