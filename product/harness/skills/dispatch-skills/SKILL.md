---
name: dispatch-skills
description: Use this skill when Harness is in WorktrackScope and needs one bounded dispatch round that selects a specialized skill or execution carrier without widening scope.
---

# Dispatch Skills

## Overview

Use this skill when `Harness` already has a current `Worktrack` action and needs to bind that action to the right execution carrier for one bounded round.

This skill packages a bounded task, selects the most appropriate specialized skill when one clearly fits, and falls back to a general task-completion execution carrier when no specialized skill is a clean match.

If the host runtime provides a real subagent dispatch shell, that fallback carrier may be a delegated `SubAgent`. If the host runtime does not provide one, the same bounded task/info contract must still be executed in the current carrier and explicitly reported as runtime fallback rather than fake subagent dispatch.

## When To Use

Use this skill when the current question is not "what is the next worktrack action", but "how should this one action be dispatched right now":

- package the current work item into a bounded execution contract
- decide whether a specialized skill is available and semantically appropriate
- fall back to a general task-completion execution carrier if not
- run one bounded dispatch round
- return structured evidence and handoff data to `Harness`

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `WorktrackScope` artifacts needed to understand the current work item.
3. Build one `Dispatch Task Brief` and one `Dispatch Info Packet`.
4. Check whether a specialized skill is a clear semantic fit for the current work item.
5. If yes, dispatch via that specialized skill.
6. If no, dispatch via a general task-completion carrier using the same bounded task/info contract.
7. Record whether the round used:
   - delegated `SubAgent` dispatch
   - current-carrier runtime fallback
8. Return one fixed-format `Dispatch Result`.

## Hard Constraints

- Do not widen the work item beyond the current `Worktrack Contract` and `Plan / Task Queue`.
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
- `verification_requirements`
- `done_signal`
- `required_context`
- `actions_taken`
- `files_touched_or_expected`
- `evidence_collected`
- `open_issues`
- `recommended_next_action`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one dispatch round and tells you when to pull in `Task Interface` or adjacent-system context.
