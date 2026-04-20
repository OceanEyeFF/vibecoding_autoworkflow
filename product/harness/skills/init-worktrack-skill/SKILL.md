---
name: init-worktrack-skill
description: Use this skill when Harness is in WorktrackScope.initializing and needs one bounded round that sets up branch, baseline, contract, and initial plan, then hands off cleanly into bounded worktrack scheduling.
---

# Init Worktrack Skill

## Overview

Use this skill when `Harness` has already decided to open or repair a specific `Worktrack` and now needs one bounded initialization round.

This skill creates the bounded branch for the `Worktrack`, makes the baseline explicit, builds or refreshes the initial `Worktrack Contract`, seeds the first `Plan / Task Queue`, and prepares a minimal handoff packet for the next scheduling round and later execution routing.

It does not perform implementation, verification, or gate judgment itself. Its job is to leave the worktrack ready for bounded scheduling, not to decide execution ownership by itself.

## When To Use

Use this skill when the current question is not "how should this task be executed", but "is this worktrack initialized correctly":

- create the bounded branch that this `Worktrack` will run on
- pin the current baseline branch or commit reference
- translate the approved work item into a bounded `Worktrack Contract`
- expand that contract into an initial `Plan / Task Queue`
- package the minimum context the next scheduling or execution round will need
- surface whether the next route is continuation-ready or blocked by a formal stop condition

## Workflow

1. Load the current `Harness Control State` and the minimum repo/worktrack artifacts needed for initialization.
2. Determine whether this is:
   - a new `Worktrack`
   - a resumed `Worktrack` whose branch, baseline, contract, or plan needs repair
3. Create the bounded branch for this `Worktrack`.
4. If that branch cannot be created safely, return a blocked initialization result instead of silently reusing another branch.
5. Record the baseline reference that this `Worktrack` will compare against.
6. Build or refresh one `Worktrack Contract`; when useful, keep the draft aligned with `templates/contract.template.md`.
7. Seed one initial `Plan / Task Queue`.
8. Produce one fixed-format `Worktrack Initialization Result`.
9. If no formal stop condition is hit, hand off to `schedule-worktrack-skill` so the seeded queue is refreshed and one current next action is selected for this round.
10. Only hand off directly to `dispatch-skills` when an already-valid current next action is explicitly present in the active queue and no additional scheduling judgment is required.
11. If the next route is not continuation-ready, return a blocked or approval-gated initialization result instead of pretending execution started.

## Hard Constraints

- Do not start implementation, verification, or gate judgment from this skill.
- Do not treat branch setup alone as sufficient initialization; baseline, contract, and initial plan must also be explicit.
- Do not treat reuse of an already-existing implementation branch as successful worktrack initialization.
- Do not treat seeding an initial task list as equivalent to selecting the current next action for execution.
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

Use the current `Harness Control State`, the active repo/worktrack artifacts, and `templates/contract.template.md` when you need a stable contract draft shape for initialization.
