---
name: schedule-worktrack-skill
description: Use this skill when Harness is in WorktrackScope and needs one bounded scheduling round that refreshes the task queue and selects the current next action without dispatching downstream execution.
---

# Schedule Worktrack Skill

## Overview

Use this skill when `Harness` already has an active `Worktrack` and needs one bounded planning round to refresh the current `Plan / Task Queue`.

This skill re-evaluates the queue against the current `Worktrack Contract`, blocker status, and available evidence, then selects one `current next action` or returns a clear `no safe next action` result.

## When To Use

Use this skill when the current question is not "who should execute this task", but "what is the right next bounded work item right now":

- refresh the queue after contract clarification, new evidence, or a blocker change
- split, reorder, defer, or mark blocked tasks inside the existing `Worktrack`
- choose the current next action that is ready to hand off
- determine whether the next step should go to `dispatch-skills`, recovery, or supervisor escalation
- package the minimum context that the next bounded round needs

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `WorktrackScope` artifacts for the current round.
3. Build one bounded `Scheduling Packet` from the current contract, queue snapshot, evidence delta, and blocker state.
4. Refresh the queue for this round only:
   - keep ready items as-is
   - reorder tasks when dependencies or evidence require it
   - split a task if the current item is too wide to dispatch safely
   - defer or block items that are not ready
5. Select one `current next action`, or return `no safe next action` with the blocking reason.
6. Produce one fixed-format `Schedule Result`.
7. If the selected route is dispatch-ready and no formal stop condition is hit, allow supervisor continuation into `dispatch-skills`.
8. Otherwise return the scheduling result as the current stop boundary.

## Scheduling Packet

If this skill is carried by a `gpt-5.4-xhigh` `SubAgent`, pass a bounded packet with at least:

- `worktrack_goal`
- `in_scope`
- `out_of_scope`
- `acceptance_criteria`
- `current_queue_snapshot`
- `dependency_status`
- `blocker_status`
- `evidence_delta`
- `planning_constraints`
- `needed_decision`

## Hard Constraints

- Do not widen scope beyond the current `Worktrack Contract`.
- Do not execute the selected next action or dispatch downstream work from this skill.
- Do not invent acceptance criteria, non-goals, or recovery policy.
- Do not mark a task done, ready, or unblocked without support from the current artifacts and evidence.
- Do not rewrite the whole queue when a bounded refresh is sufficient.
- Do not hide ambiguity; if no safe next action exists, return that explicitly.
- Do not mutate `Harness Control State` or issue a gate verdict directly from this skill.

## Expected Output

When you use this skill, produce a `Schedule Result` with at least these sections:

- `Current Worktrack Assessment`
- `Queue Refresh Decisions`
- `Current Next Action`
- `Dispatch Or Escalation Readiness`
- `Evidence Used`
- `Open Issues`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `current_worktrack_state`
- `queue_changes`
- `ready_tasks`
- `blocked_or_deferred_tasks`
- `selected_next_action`
- `selection_reason`
- `prerequisites_remaining`
- `dispatch_ready`
- `required_context_for_next_round`
- `evidence_used`
- `open_issues`
- `continuation_ready`
- `recommended_next_skill_or_route`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded scheduling round and tells you when to pull in `Task Interface` or adjacent-system context.
