---
name: dispatch-skills
description: Use this skill when Harness is in WorktrackScope and needs one bounded dispatch round that selects a specialized skill or execution carrier without widening scope.
---

# Dispatch Skills

## Overview

Use this skill when `Harness` already has a current `Worktrack` action and needs to bind that action to the right execution carrier for one bounded round.

This skill consumes one already-selected current work item, packages it as a bounded task together with its current acceptance boundary, selects the most appropriate specialized skill when one clearly fits, and falls back to a general task-completion execution carrier when no specialized skill is a clean match.

If the host runtime provides a real subagent dispatch shell, that fallback carrier may be a delegated `SubAgent`. If the host runtime does not provide one, the same bounded task/info contract must still be executed in the current carrier and explicitly reported as runtime fallback rather than fake subagent dispatch.

## When To Use

Use this skill when the current question is not "what is the next worktrack action", but "how should this one action be dispatched right now":

- consume the current next action that was already selected from the active `Plan / Task Queue`
- package the current work item into a bounded execution contract
- carry forward the acceptance criteria slice and acceptance-alignment result that justify this bounded execution round
- decide whether a specialized skill is available and semantically appropriate
- fall back to a general task-completion execution carrier if not
- run one bounded dispatch round
- return structured evidence and handoff data to `Harness`

## Workflow

1. Load the minimum `WorktrackScope` artifacts needed to understand the current selected work item.
2. Confirm that the current work item was already selected from the active `Plan / Task Queue`; if that selection does not exist, return to scheduling instead of inventing one here.
3. Confirm that the current work item still has an explicit acceptance-boundary mapping from scheduling; if that mapping is missing, stale, or contradictory, return to scheduling instead of packaging blind execution.
4. Build one `Dispatch Task Brief` and one `Dispatch Info Packet`.
5. Check whether a specialized skill is a clear semantic fit for the current work item.
6. If yes, dispatch via that specialized skill.
7. If no, dispatch via a general task-completion carrier using the same bounded task/info contract.
8. Record whether the round used:
   - delegated `SubAgent` dispatch
   - current-carrier runtime fallback
9. Return one fixed-format `Dispatch Result`.

## Hard Constraints

- Do not widen the work item beyond the current `Worktrack Contract` and `Plan / Task Queue`.
- Do not choose, reorder, or invent the current next action inside this skill; consume the selected work item that planning already produced.
- Do not detach the dispatched task from the acceptance criteria slice and acceptance-alignment result that scheduling already established.
- Do not treat "no specialized skill exists" as a blocked state by itself.
- Do not pass full-repo context when a bounded info packet is sufficient.
- Do not let the fallback execution carrier redefine acceptance criteria, non-goals, or verification requirements.
- Do not claim a delegated `SubAgent` was used unless the host runtime actually spawned one.
- Do not mutate `Harness Control State` or issue a gate verdict directly from this skill.
- Do not collapse selection reason, execution result, and evidence into one vague summary.

## Expected Output

When you use this skill, produce a `Dispatch Result` with at least these sections:

- `Dispatch Decision`
- `Dispatch Task Brief`
- `Dispatch Info Packet`
- `Actions Taken`
- `Evidence Collected`
- `Open Issues`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `selected_executor`
- `runtime_dispatch_mode`
- `selection_reason`
- `fallback_used`
- `task`
- `goal`
- `in_scope`
- `out_of_scope`
- `constraints`
- `acceptance_criteria_for_this_round`
- `acceptance_alignment_used`
- `verification_requirements`
- `done_signal`
- `required_context`
- `actions_taken`
- `files_touched_or_expected`
- `evidence_collected`
- `open_issues`
- `recommended_next_action`

## Resources

Use the selected work item, scheduling output, and the bounded execution packet as the authority for this dispatch round.
