---
name: repo-refresh-skill
description: Use this skill when Harness returns to RepoScope after a worktrack closeout and needs one bounded repo refresh round plus a verified writeback handoff.
---

# Repo Refresh Skill

## Overview

Use this skill when `Harness` has finished a `WorktrackScope` closeout round and needs to refresh repo-level slow variables from verified evidence.

This skill packages one bounded post-closeout refresh round for a `gpt-5.4-xhigh` `SubAgent`, updates the repo-level assessment, and returns a structured writeback handoff for programmer approval instead of assuming repo truth was already updated.

## When To Use

Use this skill when the current question is not "how do we finish the worktrack", but "what repo-level truth now needs to be refreshed from that verified closeout":

- a worktrack has reached closeout or merge-complete status
- `Gate Evidence` is available and has already established the verified outcome
- `Repo Snapshot / Status` now needs a slow-variable refresh
- verified findings may need writeback into repo-level formal artifacts
- `Harness` needs a bounded repo refresh result before deciding the next repo action

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `RepoScope` artifacts plus the just-closed worktrack's verified `Gate Evidence`.
3. Build one `Repo Refresh Task Brief` and one `Repo Refresh Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
4. Refresh the repo-level assessment against `Repo Goal / Charter`, current `Repo Snapshot / Status`, and the verified closeout evidence.
5. Separate items into:
   - verified writeback candidates
   - deferred or still-unverified items
   - repo-level risks that remain open after closeout
6. Stop after one bounded repo refresh round and return one fixed-format `Repo Refresh Report` plus one `Verified Writeback Handoff`.

## Hard Constraints

- Do not reopen, replan, or re-execute the closed worktrack from this skill.
- Do not treat a merged diff or a claimed closeout as sufficient by itself; use verified `Gate Evidence`.
- Do not write unverified conclusions into repo truth artifacts.
- Do not silently mutate `Harness Control State` or repo-level docs from this skill; return a writeback handoff first.
- Do not expand into full-repo rediscovery when the refresh only depends on bounded closeout evidence.
- Do not turn repo refresh into goal change control unless the evidence clearly indicates a separate follow-up path.

## Repo Refresh Contract

Use the same bounded contract shape every time this skill runs.

### Repo Refresh Task Brief

- `trigger`
- `goal`
- `closed_worktrack`
- `in_scope`
- `out_of_scope`
- `constraints`
- `writeback_targets`
- `done_signal`

### Repo Refresh Info Packet

- `current_repo_state`
- `repo_artifacts_in_play`
- `gate_evidence_summary`
- `accepted_change_summary`
- `verification_results`
- `known_risks`
- `required_context`
- `missing_or_deferred_items`

### Verified Writeback Handoff

- `writeback_targets`
- `verified_findings`
- `proposed_updates`
- `evidence_basis`
- `deferred_items`
- `approval_request`

## Expected Output

When you use this skill, produce a `Repo Refresh Report` with at least these sections:

- `Repo Refresh Trigger`
- `Repo Refresh Assessment`
- `Verified Writeback Handoff`
- `Deferred Or Unverified Items`
- `Recommended RepoScope Next Step`
- `Programmer Review Request`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `refresh_trigger`
- `baseline_branch`
- `closed_worktrack`
- `repo_state_changes`
- `verified_findings`
- `snapshot_updates`
- `writeback_targets`
- `proposed_writeback`
- `evidence_basis`
- `deferred_items`
- `open_risks`
- `recommended_next_repo_action`
- `needs_programmer_writeback_approval`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one post-closeout repo refresh round and tells you when to pull in additional repo-control context.
