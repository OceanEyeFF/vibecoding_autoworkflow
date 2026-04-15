---
name: close-worktrack-skill
description: Use this skill when Harness is in WorktrackScope.integrating and needs one bounded closeout round for PR, merge, cleanup, and repo-refresh handoff without silently crossing approval boundaries.
---

# Close Worktrack Skill

## Overview

Use this skill when `Harness` already has a merge-eligible or merged `Worktrack` and needs one bounded closeout round inside `WorktrackScope.integrating`.

This skill packages the minimum closeout context for one `gpt-5.4-xhigh` `SubAgent`, determines the current closeout stage, and returns a structured closeout result plus an explicit `Repo Refresh Handoff` instead of silently pushing through merge, branch cleanup, or repo-level writeback.

## When To Use

Use this skill when the current question is not "how do we fix or judge the worktrack", but "how do we finish its closeout path without crossing authority boundaries":

- the current `Worktrack` already has a `Gate Evidence` result that allows closeout handling
- the system needs to determine whether this round is at `pr`, `merge`, `cleanup-branch`, or `repo-refresh handoff`
- closeout state may be partially complete, such as `PR open but not merged` or `merged but cleanup still pending`
- `Harness` needs a bounded report of what closeout actions are complete, what still needs approval, and what should be handed back to `RepoScope`
- the result must stay inside closeout handling instead of drifting back into implementation, gate adjudication, or repo refresh execution

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `WorktrackScope` artifacts plus current branch, PR, and merge-status evidence relevant to closeout.
3. Build one `Close Worktrack Task Brief` and one `Close Worktrack Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
4. Assess the current closeout stage:
   - `ready-for-pr`
   - `pr-open`
   - `ready-to-merge`
   - `merged`
   - `cleanup-ready`
   - `repo-refresh-ready`
   - `blocked-closeout`
5. Separate closeout results into:
   - actions completed in this round
   - actions still waiting on programmer approval or external merge state
   - cleanup items that are safe only after merge is confirmed
   - verified material that should be handed off to `repo-refresh-skill`
6. Stop after one bounded closeout round and return one fixed-format `Close Worktrack Report` plus one `Repo Refresh Handoff`.

## Closeout Contract

Use the same bounded contract shape every time this skill runs.

### Close Worktrack Task Brief

- `trigger`
- `goal`
- `current_worktrack`
- `current_closeout_stage`
- `in_scope`
- `out_of_scope`
- `authority_boundaries`
- `required_approvals`
- `done_signal`

### Close Worktrack Info Packet

- `current_worktrack_state`
- `worktrack_contract_summary`
- `gate_verdict_summary`
- `pr_state`
- `merge_state`
- `branch_cleanup_state`
- `accepted_change_summary`
- `residual_risks`
- `required_context`

### Repo Refresh Handoff

- `closed_worktrack`
- `baseline_branch`
- `accepted_change_summary`
- `verification_results`
- `closeout_status`
- `writeback_candidates`
- `residual_risks`
- `deferred_items`
- `approval_request`

## Hard Constraints

- Do not reopen implementation, replan the worktrack, or re-adjudicate the gate from this skill.
- Do not treat `gate pass` as implicit approval to merge, delete a branch, or update repo truth.
- Do not silently perform `merge`, `cleanup-branch`, or repo writeback when approval or state confirmation is still missing.
- Do not treat `PR opened` as equivalent to `merged`, or `merged` as equivalent to `repo refresh completed`.
- Do not clean up a branch until merge status and return-path safety are explicit.
- Do not mutate `Harness Control State`, `Repo Snapshot / Status`, or canonical docs from this skill; return a handoff instead.
- Do not widen scope into adjacent systems unless the current closeout boundary clearly depends on them.
- Do not collapse completed actions, pending approvals, and repo-refresh handoff into one vague closeout narrative.

## Expected Output

When you use this skill, produce a `Close Worktrack Report` with at least these sections:

- `Closeout Trigger`
- `Current Closeout Stage`
- `Closeout Actions Taken`
- `Authority Checks And Pending Approvals`
- `Repo Refresh Handoff`
- `Recommended Next Scope`
- `Programmer Review Request`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `closeout_trigger`
- `current_worktrack`
- `closeout_stage_before`
- `closeout_stage_after`
- `gate_verdict`
- `pr_status`
- `merge_status`
- `cleanup_status`
- `actions_taken`
- `actions_pending_approval`
- `decisive_evidence`
- `residual_risks`
- `repo_refresh_ready`
- `repo_refresh_handoff`
- `recommended_next_scope`
- `recommended_next_action`
- `needs_programmer_approval`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one closeout round and tells you when to pull in adjacent-system context for authority-boundary checks.
