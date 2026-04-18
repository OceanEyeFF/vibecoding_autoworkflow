---
name: init-worktrack-skill
description: Use this skill when Harness is in WorktrackScope.initializing and needs one bounded round that sets up branch, baseline, contract, and initial plan, then hands off cleanly into the next legal worktrack action.
---

# Init Worktrack Skill

## Overview

Use this skill when `Harness` has already decided to open or repair a specific `Worktrack` and now needs one bounded initialization round.

This skill makes branch and baseline handling explicit, builds or refreshes the initial `Worktrack Contract`, seeds the first `Plan / Task Queue`, and prepares a minimal executor handoff packet for the next specialized skill or execution carrier.

It does not perform implementation, verification, or gate judgment itself, but it should leave the worktrack continuation-ready whenever the next legal action is clear.

## When To Use

Use this skill when the current question is not "how should this task be executed", but "is this worktrack initialized correctly":

- determine whether this worktrack should create a new bounded branch or reuse an existing branch with an explicit reason
- pin the current baseline branch or commit reference
- translate the approved work item into a bounded `Worktrack Contract`
- expand that contract into an initial `Plan / Task Queue`
- package the minimum context the next execution round will need
- surface whether the next route is continuation-ready or blocked by a formal stop condition

## Workflow

1. Read `references/entrypoints.md`.
2. Load the current `Harness Control State` and the minimum repo/worktrack artifacts needed for initialization.
3. Determine whether this is:
   - a new `Worktrack`
   - a resumed `Worktrack` whose branch, baseline, contract, or plan needs repair
4. Decide branch handling for this `Worktrack`:
   - create a bounded branch
   - reuse an existing bounded branch with explicit justification
5. Record the baseline reference that this `Worktrack` will compare against.
6. Build or refresh one `Worktrack Contract`.
7. Seed one initial `Plan / Task Queue`.
8. Produce one fixed-format `Worktrack Initialization Result`.
9. If the next work item is clear and no formal stop condition is hit, hand off directly to `schedule-worktrack-skill` or `dispatch-skills`.
10. If the next route is not continuation-ready, return a blocked or approval-gated initialization result instead of pretending execution started.

## Hard Constraints

- Do not start implementation, verification, or gate judgment from this skill.
- Do not treat branch setup alone as sufficient initialization; baseline, contract, and initial plan must also be explicit.
- Do not guess branch, baseline, or scope when repo state is ambiguous; return a blocked initialization result instead.
- Do not widen scope beyond the approved worktrack goal, non-goals, and current repo baseline.
- Do not silently mutate `Harness Control State` without surfacing the intended next state and required approval.
- Do not rewrite upstream `Task Contract` truth; consume it only as an input boundary when it exists.
- Do not hand the next execution carrier full-repo context when a bounded handoff packet is sufficient.
- Do not claim a fallback `SubAgent` is ready unless the host runtime can actually dispatch one.

## Expected Output

When you use this skill, produce a `Worktrack Initialization Result` with at least these sections:

- `Initialization Decision`
- `Branch and Baseline`
- `Worktrack Contract`
- `Initial Plan / Task Queue`
- `Executor Handoff Packet`
- `Stop And Return To Harness`

Inside the result, include at least these fields or equivalents:

- `worktrack_identity`
- `initialization_status`
- `branch_action`
- `branch_name_or_rule`
- `baseline_ref`
- `baseline_reason`
- `goal`
- `in_scope`
- `out_of_scope`
- `impact_modules`
- `next_state`
- `acceptance_criteria`
- `rollback_conditions`
- `initial_tasks`
- `task_order`
- `dependencies`
- `current_blockers`
- `next_action`
- `verification_requirements`
- `required_context`
- `known_risks`
- `executor_handoff_packet`
- `execution_not_started`
- `continuation_ready`
- `recommended_next_action`
- `needs_approval`
- `approval_to_apply`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded worktrack-initialization round and tells you when to pull `Repo` or adjacent-system context.
