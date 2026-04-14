---
name: harness-skill
description: Use this skill when you need the top-level Harness supervisor to determine the current layer, run one bounded Harness loop in that layer, summarize what happened, and ask the programmer whether to switch status and start the next Harness round.
---

# Harness Skill

## Overview

Use this skill as the top-level `Harness` supervisor entry in `Codex`.

It determines the current control layer, runs one bounded Harness loop inside that layer, and returns a structured handoff for the programmer instead of silently continuing forever.

## When To Use

Use this skill when the task is not just "write code", but "run one Harness round":

- determine whether the repo is currently in `RepoScope` or `WorktrackScope`
- operate within that current scope only
- collect the minimum evidence needed for this round
- decide whether to stay in the current layer or request a layer/status switch
- tell the programmer what happened, what to review, and what approval would unlock the next round

## Workflow

1. Read `references/entrypoints.md`.
2. Load the current `Harness Control State` and the minimum current-scope artifacts.
3. Determine the active layer:
   - `RepoScope`
   - `WorktrackScope`
4. Run one bounded Harness loop inside that layer.
5. Stop at the current authority boundary instead of silently pushing into the next round.
6. Produce one fixed-format `Harness Turn Report`.

## Hard Constraints

- Do not treat `Harness` as the direct coding executor.
- Do not silently switch `RepoScope` and `WorktrackScope` without explicit approval.
- Do not mutate control state just because a next step seems obvious; surface the requested state transition first.
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
- `Recommended Next Scope`
- `Recommended Next Action`
- `Approval Request`
- `How To Review`

Inside the result, include at least these fields or equivalents:

- `current_scope`
- `current_state`
- `actions_taken`
- `artifacts_read`
- `evidence_collected`
- `status_or_verdict`
- `recommended_next_scope`
- `recommended_next_action`
- `needs_approval`
- `approval_to_apply`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for the current Harness round and tells you which artifacts to load for `RepoScope` and `WorktrackScope`.
