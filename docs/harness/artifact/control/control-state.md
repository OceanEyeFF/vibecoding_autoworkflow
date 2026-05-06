---
title: "Harness Control State"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Harness Control State

保存控制面当前处于哪个模式，而不是保存业务真相。最少应包含当前控制级别、活跃 worktrack、baseline branch、下一动作和关联正式文档路径；不应替代 Repo Snapshot/Status 或 Worktrack Contract。

## Linked Formal Documents

Harness Control State 可以保存标准 artifact 路径指针（repo_snapshot、repo_analysis、worktrack_contract、plan_task_queue、gate_evidence）让 supervisor 快速定位正式对象，但这些只是路径指针而非业务真相本身。如果某 artifact 缺失或过期，Control State 不应自行补写业务内容，应通过对应 Scope 的 Observe/Decide/Init/Verify 路由刷新正式对象。

如果支持 contract-boundary 后的一次性自主续跑，还应保存最小 Continuation Authority 策略位：

- `post_contract_autonomy`: `delegated-minimal`（默认）或 `manual-only`（strict handback 诊断场景）
- `autonomy_scope`: 默认 `current-goal-only`
- `max_auto_new_worktracks`: 默认 `1`；大于 1 属于显式 override
- `stop_after_autonomous_slice`: 默认 `yes`
- `subagent_dispatch_mode`: `auto`（默认）/ `delegated` / `current-carrier`；这是 repo 级默认值，不应遮蔽 worktrack 级执行策略
- `subagent_dispatch_mode_override_scope`: 默认 `worktrack-contract-primary`；只有 `global-override` 时 control-state 才压过 worktrack contract
- `subagent_default_model`: 可选，不改变权限边界

这些字段属于 control policy，不回答 repo 目标或替代 Worktrack Contract。`subagent_dispatch_mode` 是 SubAgent 委派的 repo 级默认策略，语义必须与 worktrack 级 `runtime_dispatch_mode` 保持一致：auto 优先委派否则显式 runtime fallback；delegated 必须委派否则返回 gap/block；current-carrier 显式关闭委派。若权限边界、运行时缺口或 dispatch package unsafe 阻止委派，必须把 fallback 原因写入执行结果或 gate evidence。

仅 Continuation Authority 还不够。如果 control-state 不能把 handback/re-entry 边界持久化到下一轮独立对话，后续”继续工作”可能被误读成 fresh handoff，错误地允许新建 worktrack。因此还应保存最小 Handback Guard / Autonomy Ledger：

- `handoff_state`: `none` / `awaiting-handoff` / `autonomous-slice-active`
- `last_stop_reason`
- `last_handback_signature`
- `handback_reaffirmed_rounds`
- `autonomy_budget_remaining`
- `autonomous_worktracks_opened`

这些字段属于 control memory，不替代 Repo Snapshot/Status、Worktrack Contract 或 Gate Evidence。

此外还应保存 Baseline Traceability，用于 WorktrackScope 关闭后快速定位已验证基线：last_verified_checkpoint、checkpoint_type、checkpoint_ref、verified_at、if_no_commit_reason、alternative_traceability。这些字段属于 traceability metadata，不替代 Repo Snapshot/Status。

补充约束：post_contract_autonomy: manual-only 时"继续工作"只能 handback 不得自动开新 worktrack；delegated-minimal 时也只能在 current-goal-only 内消费一次 autonomy budget。WorktrackScope 关闭后即使返回 RepoScope 也不得自动清空 handoff_state。awaiting-handoff 且无新 programmer 决策时只允许复核同一 handback 边界。delegated-minimal 下只有 awaiting-handoff 且 budget > 0 时才能切新 bounded slice，开启后立即消费预算。autonomous slice 结束后应再次 handback，不得默认无限链式续跑。stop_after_autonomous_slice: yes 时 slice 结束后重新写回 awaiting-handoff。stable-handback 是 runtime verdict，control-state 应持久化的是 last_handback_signature 与 reaffirm 计数。
