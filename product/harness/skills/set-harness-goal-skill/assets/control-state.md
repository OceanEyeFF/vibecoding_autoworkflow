# Harness Control State

> 这是 `.aw/control-state.md` 的模板来源，用来维护当前 Harness supervisor 的控制面状态，不要把业务真相写进来。

## Metadata

- updated:
- owner:

## Current Control Level

- repo_scope:
- worktrack_scope:

## Active Worktrack

- 

## Baseline Branch

- 

## Current Next Action

- 

## Linked Formal Documents

- repo_snapshot:
- repo_analysis:
- worktrack_contract:
- plan_task_queue:
- gate_evidence:

## Approval Boundary

- needs_programmer_approval:
- reason:

## Continuation Authority

> `subagent_dispatch_mode` 是使用 SubAgent 的 repo 级默认开关。`subagent_dispatch_mode_override_scope: worktrack-contract-primary` 表示默认让工作追踪内的 `runtime_dispatch_mode` 优先；只有显式改为 `global-override` 时，control-state 才压过 worktrack 合同。`auto` 默认优先委派 SubAgent；`delegated` 要求真实委派；`current-carrier` 明确关闭 SubAgent 委派。若 `auto` 不能安全委派，必须在结果中写明 `runtime fallback`、权限边界阻断或 `dispatch package unsafe`。

- post_contract_autonomy: delegated-minimal
- autonomy_scope: current-goal-only
- max_auto_new_worktracks: 1
- stop_after_autonomous_slice: yes
- subagent_dispatch_mode: auto
- subagent_dispatch_mode_override_scope: worktrack-contract-primary
- subagent_default_model:

## Handback Guard

- handoff_state: none
- last_stop_reason:
- last_handback_signature:
- handback_reaffirmed_rounds: 0

## Baseline Traceability

> 记录最近一次 worktrack 关闭后的已验证基线，供后续续跑时快速定位。
> `latest_observed_checkpoint` 与 `last_doc_catch_up_checkpoint` 是 git hash 幂等性锚点，用于避免对同一代码基线重复执行 repo-refresh 和 doc-catch-up。harness-skill 启动时通过 git rev-parse HEAD 对比这两个字段决定是否跳过重复刷新。

- last_verified_checkpoint:
- latest_observed_checkpoint:
- last_doc_catch_up_checkpoint:
- checkpoint_type:
- checkpoint_ref:
- verified_at:
- if_no_commit_reason:
- alternative_traceability:

## Autonomy Ledger

- autonomy_budget_remaining: 1
- autonomous_worktracks_opened: 0

## Notes

- returning_to_repo_scope_does_not_clear_handoff: yes
- 
