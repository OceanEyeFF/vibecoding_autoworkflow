---
title: "Harness Control State"
status: active
updated: 2026-04-23
owner: aw-kernel
last_verified: 2026-04-23
---
# Harness Control State

保存控制面当前处于哪个模式，而不是保存业务真相。

最少应包含：

- 当前控制级别
- 当前活跃 worktrack
- 当前 baseline branch
- 当前需要执行的下一动作
- 关联正式文档路径

它不应替代 `Repo Snapshot / Status` 或 `Worktrack Contract`。

如果系统支持 `contract-boundary` 之后的一次性自主续跑，还应显式保存最小 `Continuation Authority` 策略位：

- `post_contract_autonomy`
  - `delegated-minimal`
  - `manual-only`
  - 默认基线应使用 `delegated-minimal`；`manual-only` 只用于刻意观察 strict handback / 不续跑的诊断场景
- `autonomy_scope`
  - 默认只允许 `current-goal-only`
- `max_auto_new_worktracks`
  - 默认应为 `1`
  - 大于 `1` 属于显式观察 profile / runtime override，不是初始化默认值
- `stop_after_autonomous_slice`
  - 默认应为 `yes`

这些字段属于 control policy，不属于业务真相：

- 它们回答的是“在当前 repo charter 内，Harness 是否被允许代替 programmer 自动开启下一段最小 bounded slice”
- 它们不回答 repo 目标本身是什么，也不替代 `Repo Goal / Charter`
- 它们不替代具体 `Worktrack Contract`

但仅有 `Continuation Authority` policy 还不够。

如果 control-state 不能把 handback / re-entry 边界持久化到下一轮独立对话里，那么系统即使已经回到 `RepoScope`，后续 `继续工作` 仍可能被误读成 fresh handoff，进而错误地把“重新判断 repo”升级成“允许新建下一段 worktrack”。

因此，`Harness Control State` 还应显式保存最小 `Handback Guard / Autonomy Ledger`：

- `handoff_state`
  - `none`
  - `awaiting-handoff`
  - `autonomous-slice-active`
- `last_stop_reason`
- `last_handback_signature`
- `handback_reaffirmed_rounds`
- `autonomy_budget_remaining`
- `autonomous_worktracks_opened`

这些字段属于 control memory，不属于业务真相：

- 它们回答的是“当前控制器是否正停在一个尚未被 programmer 明确重新授权的 handback 边界”
- 它们回答的是“同一个 handback 边界是否已经被重复确认，因此下一轮应压缩成 `stable-handback`”
- 它们回答的是“允许的一次性自主续跑预算是否已经被消费”
- 它们不替代 `Repo Snapshot / Status`、`Worktrack Contract` 或 `Gate Evidence`

此外，`Harness Control State` 还应保存 `Baseline Traceability`，用于在 WorktrackScope 关闭后快速定位已验证基线：

- `last_verified_checkpoint`
- `checkpoint_type`
- `checkpoint_ref`
- `verified_at`
- `if_no_commit_reason`
- `alternative_traceability`

这些字段属于 traceability metadata，不属于业务真相：

- 它们回答的是"最近一次 worktrack 关闭后，repo 的已验证基线在哪里"
- 它们回答的是"如果不形成 commit，替代追溯物是什么"
- 它们不替代 `Repo Snapshot / Status` 中的详细状态描述

补充约束：

- 如果 `post_contract_autonomy: manual-only`，则 `继续工作` 在当前合同关闭后只能 handback，不得自动开新 worktrack
- 如果 `post_contract_autonomy: delegated-minimal`，也只能在 `current-goal-only` 范围内消费一次 autonomy budget
- `WorktrackScope` 关闭后即使返回了 `RepoScope`，也不得因为 scope 已回到 repo 层就自动清空 `handoff_state`
- 如果 `handoff_state: awaiting-handoff` 且没有新的 programmer 决策、约束增量或显式重新授权，则后续 `继续工作` 只允许复核同一 handback 边界，不得把当前轮当成 fresh handoff
- 如果 `post_contract_autonomy: delegated-minimal`，只有在 `handoff_state: awaiting-handoff` 且 `autonomy_budget_remaining > 0` 时，才允许自动切出一段新的 bounded slice；一旦决定开启，就应立即消费预算并更新 ledger
- autonomous slice 结束后，应再次 handback，不得在 control-state 中默认形成无限链式续跑
- 如果 `stop_after_autonomous_slice: yes`，则 autonomous slice 结束后应把 `handoff_state` 重新写回 `awaiting-handoff`
- `stable-handback` 属于 runtime verdict，不是应长期写入 control-state 的业务字段；control-state 应持久化的是可复算该 verdict 的 `last_handback_signature` 与 reaffirm 计数
