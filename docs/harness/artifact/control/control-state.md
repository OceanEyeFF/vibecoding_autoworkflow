---
title: "Harness Control State"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---
# Harness Control State

保存控制面当前处于哪个模式，而不是保存业务真相。最少应包含当前控制级别、活跃 worktrack、baseline branch、下一动作和关联正式文档路径；不应替代 Repo Snapshot/Status 或 Worktrack Contract。

Harness 每轮启动时必须先读取既有 `.aw/control-state.md` 并恢复控制配置，再进入 Scope / Function 状态估计。这个启动前置读取称为 control config hydration，最少覆盖 `Linked Formal Documents`、`Approval Boundary`、`Continuation Authority`、`Handback Guard`、`Baseline Traceability` 与 `Autonomy Ledger`。缺失字段只能按本文默认值降级解释，并在本轮状态估计中记录 `config_hydration_gaps`；缺失不得被解释为扩大权限、放宽审批或启用更多自动性。

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

程序员授予的长期权限、自动性或分派策略变更必须写回本 artifact 对应配置段，不能只停留在对话记忆里。一次性审批只对当前 worktrack、当前 gate 或当前 destructive action 生效，应写入本轮 evidence / handoff，不得改变长期默认值。只有当用户明确表达持久授权或更改默认策略时，才允许更新 `post_contract_autonomy`、`max_auto_new_worktracks`、`stop_after_autonomous_slice`、`subagent_dispatch_mode`、`subagent_dispatch_mode_override_scope` 或其他长期 authority 字段；如果字段语义或默认值改变，必须同步更新初始化模板和 canonical skill 说明。

仅 Continuation Authority 还不够。如果 control-state 不能把 handback/re-entry 边界持久化到下一轮独立对话，后续”继续工作”可能被误读成 fresh handoff，错误地允许新建 worktrack。因此还应保存最小 Handback Guard / Autonomy Ledger：

- `handoff_state`: `none` / `awaiting-handoff` / `autonomous-slice-active`
- `last_stop_reason`
- `last_handback_signature`
- `handback_reaffirmed_rounds`
- `autonomy_budget_remaining`
- `autonomous_worktracks_opened`

这些字段属于 control memory，不替代 Repo Snapshot/Status、Worktrack Contract 或 Gate Evidence。

此外还应保存 Baseline Traceability，用于 WorktrackScope 关闭后快速定位已验证基线：`last_verified_checkpoint`、`latest_observed_checkpoint`、`last_doc_catch_up_checkpoint`、`checkpoint_type`、`checkpoint_ref`、`verified_at`、`if_no_commit_reason`、`alternative_traceability`。其中 `latest_observed_checkpoint` 与 `last_doc_catch_up_checkpoint` 是 git hash 幂等性锚点，分别记录上次 `repo-refresh-skill` 和 `doc-catch-up-worker-skill` 执行时的 HEAD hash，供 harness-skill 启动时对比跳过重复刷新。空值或缺失表示该锚点尚未建立，必须执行完整状态估计；不得把空值解释为“当前基线无需刷新”。这些字段属于 traceability metadata，不替代 Repo Snapshot/Status。

补充约束：post_contract_autonomy: manual-only 时"继续工作"只能 handback 不得自动开新 worktrack；delegated-minimal 时也只能在 current-goal-only 内消费一次 autonomy budget。WorktrackScope 关闭后即使返回 RepoScope 也不得自动清空 handoff_state。awaiting-handoff 且无新 programmer 决策时只允许复核同一 handback 边界。delegated-minimal 下只有 awaiting-handoff 且 budget > 0 时才能切新 bounded slice，开启后立即消费预算。autonomous slice 结束后应再次 handback，不得默认无限链式续跑。stop_after_autonomous_slice: yes 时 slice 结束后重新写回 awaiting-handoff。stable-handback 是 runtime verdict，control-state 应持久化的是 last_handback_signature 与 reaffirm 计数。
