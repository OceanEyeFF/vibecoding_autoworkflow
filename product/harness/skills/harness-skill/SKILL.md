---
name: harness-skill
description: Use this skill when you need the top-level Harness supervisor to determine the current layer, continue across legal state transitions inside that layer, and stop only when a formal stop condition is hit.
---

# Harness Skill

## Overview

Use this skill as the top-level `Harness` supervisor entry in `Codex`.

It determines the current control layer, routes work to the bounded downstream `RepoScope` or `WorktrackScope` skills that own the actual local judgment, and returns a structured handoff only when a formal stop condition is hit.

`Harness` is responsible for supervision and legal continuation, not for inventing the concrete repo action, worktrack task list, or execution task by itself.

Bounded downstream rounds are local control steps, not implicit stop signals. `Harness` should continue by consuming downstream structured outputs, especially `allowed_next_routes`, `recommended_next_route`, `continuation_ready`, `continuation_blockers`, and approval fields, until a formal stop condition is actually hit.

## When To Use

Use this skill when the task is not just "write code", but "run the current Harness control loop":

- determine whether the repo is currently in `RepoScope` or `WorktrackScope`
- operate within that current scope only
- collect the minimum evidence needed for each bounded local round
- obtain repo next-direction and worktrack next-action judgment from the downstream scope skills instead of defining those items inside `Harness`
- keep advancing while the next transition is legal and no formal stop condition is hit
- tell the programmer what happened only when approval, missing evidence, runtime gap, or another stop condition blocks safe continuation

## Workflow

1. Load the current `Harness Control State` and the minimum current-scope artifacts.
2. Determine the active layer:
   - `RepoScope`
   - `WorktrackScope`
3. If the active layer is `RepoScope`, run the repo-side judgment chain:
   - use `repo-status-skill` to refresh one bounded repo observation packet
   - use `repo-whats-next-skill` to turn that observation into one repo action plus one explicit continuation route
   - continue into `WorktrackScope` only when the downstream result keeps `recommended_repo_action` and `recommended_next_route` aligned, sets `continuation_ready: true`, and does not raise `approval_required` or `continuation_blockers`
4. If the active layer is `WorktrackScope`, run the worktrack-side continuation chain:
   - use `init-worktrack-skill` when branch, baseline, contract, or initial queue still needs initialization or repair
   - use `schedule-worktrack-skill` to read the current `Plan / Task Queue`, refresh it for this round, select one current next action, and package the bounded dispatch handoff for that action
   - use `dispatch-skills` only after the current work item has already been selected from the worktrack queue, the dispatch handoff is marked ready, and the route remains continuation-ready
5. Re-evaluate whether the next legal state transition can continue automatically by reading the downstream structured outputs instead of guessing from prose summaries.
6. Continue until one formal stop condition is hit.
7. Produce one fixed-format `Harness Turn Report`.

## Formal Stop Conditions

Stop and return control only when at least one of these conditions is true:

- `approval-gated`: a goal change, scope expansion, destructive action, or other authority boundary sets `approval_required: true`
- `evidence-gated`: required artifacts or evidence are missing, stale, or contradictory enough that safe continuation is no longer possible
- `route-blocked`: the current route hits `soft-fail`, `hard-fail`, `blocked`, or raises explicit `continuation_blockers`
- `runtime-gap`: the host runtime lacks a safe dispatch shell for the next execution carrier
- `contract-boundary`: the next action would step outside the approved repo or worktrack contract

## Hard Constraints

- Do not treat `Harness` as the direct coding executor.
- Do not let `Harness` define concrete repo actions, task-list contents, or execution tasks when the downstream scope skills are responsible for those judgments.
- Do not switch `RepoScope` and `WorktrackScope` across an unapproved authority boundary.
- A scope switch may continue without a fresh programmer handoff only when the current route has already marked that transition as continuation-ready and no formal stop condition requires approval.
- Do not dispatch from `WorktrackScope` until the current work item has been selected from the active `Plan / Task Queue`.
- Do not infer continuation from prose when a downstream result already exposes explicit route, blocker, and approval fields.
- Do not treat `recommended_next_action` as the canonical route field when `recommended_next_route` is present; keep the older field only as a compatibility projection.
- Do not mutate control state just because a next step seems obvious; surface the requested state transition first.
- Do not treat "a local skill round returned structured output" as a stop condition by itself.
- Do not claim a `SubAgent` was dispatched unless the host runtime actually delegated execution to a distinct carrier.
- Do not collapse `evidence`, `verdict`, and `next action` into one vague narrative.
- Do not read repo-local mounts as truth sources.
- Do not expand into adjacent systems unless the current round actually depends on them.

## Expected Output

When you use this skill, produce a `Harness Turn Report` with at least these sections:

- `Current Harness Layer`
- `Current State Assessment`
- `Actions Taken This Round`
- `Artifacts and Evidence Reviewed`
- `Current Verdict or Status`
- `Continuation And Route Decision`
- `Recommended Next Scope`
- `Recommended Next Action`
- `Approval Request`
- `How To Review`

Inside the result, include at least these fields or equivalents:

- `current_scope`
- `current_phase`
- `current_state`
- `actions_taken`
- `artifacts_read`
- `evidence_collected`
- `downstream_rounds_run`
- `status_or_verdict`
- `allowed_next_routes`
- `recommended_next_route`
- `recommended_next_scope`
- `recommended_next_action`
- `continuation_ready`
- `continuation_blockers`
- `continuation_decision`
- `stop_conditions_hit`
- `approval_required`
- `approval_scope`
- `approval_reason`
- `needs_approval`
- `approval_to_apply`
- `how_to_review`

## Resources

Use the current `Harness Control State`, the active `.aw/` artifacts, and bounded downstream skill outputs as the authority for this round. Prefer downstream structured outputs over local narrative summaries when deciding whether the next legal continuation is allowed.
