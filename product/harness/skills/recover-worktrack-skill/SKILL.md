---
name: recover-worktrack-skill
description: Use this skill when Harness is in WorktrackScope.recovering and needs one bounded recovery-choice round that selects retry, rollback, split-worktrack, or refresh-baseline with explicit authority boundaries.
---

# Recover Worktrack Skill

## Overview

Use this skill when `Harness` has already concluded that the current `Worktrack` cannot continue on its present path and needs one bounded recovery-choice round.

This skill packages the minimum failure-path context for a `gpt-5.4-xhigh` `SubAgent`, evaluates the legal recovery operators, selects among `retry`, `rollback`, `split-worktrack`, or `refresh-baseline`, and returns a structured recovery handoff for `Harness`.

It stops at the recovery authority boundary instead of silently executing destructive rollback, redefining scope, or rewriting repo truth.

## When To Use

Use this skill when the current question is not "should the worktrack pass the gate", but "what is the correct recovery path now":

- classify the current failure or blocked condition from bounded evidence
- determine whether the current `Worktrack` can safely retry within the same goal and baseline
- decide whether rollback is required before any new attempt
- decide whether the work should be split into smaller bounded worktracks
- decide whether baseline drift or repo truth change requires `refresh-baseline`
- return a recovery decision with explicit approval boundaries and next-step handoff

## Workflow

1. Read `references/entrypoints.md`.
2. Confirm this is a bounded `WorktrackScope.recovering` round, not initial planning, implementation dispatch, final gate judgment, or closeout.
3. Load the minimum recovery artifacts for the current failure path.
4. Build one `Recovery Choice Task Brief` and one `Recovery Choice Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
5. Classify the current recovery trigger:
   - `soft-fail`
   - `hard-fail`
   - `blocked`
   - `baseline-drift`
6. Evaluate the legal recovery choices:
   - `retry`
   - `rollback`
   - `split-worktrack`
   - `refresh-baseline`
7. Select one primary recovery path and, if needed, one fallback recovery path.
8. Return one fixed-format `Recovery Choice Result` plus one `Recovery Authority Handoff`.
9. Stop before executing destructive rollback, opening new worktracks, or mutating repo truth.

## Recovery Choice Contract

Use the same bounded contract shape every time this skill runs.

### Recovery Choice Task Brief

- `recovery_trigger`
- `goal`
- `current_worktrack`
- `in_scope`
- `out_of_scope`
- `recovery_options`
- `constraints`
- `authority_limits`
- `done_signal`

### Recovery Choice Info Packet

- `current_worktrack_state`
- `worktrack_contract_summary`
- `plan_queue_status`
- `gate_evidence_summary`
- `failure_signals`
- `baseline_status`
- `known_risks`
- `required_context`
- `unresolved_questions`

### Recovery Authority Handoff

- `selected_recovery_mode`
- `selection_reason`
- `authority_boundary`
- `immediate_safe_actions`
- `approval_required`
- `follow_up_artifacts`
- `handoff_target`

## Recovery Authority Boundaries

The recovery choice must stay inside these authority limits:

- `retry`
  - Allowed only when the current goal, non-goals, and baseline remain valid.
  - May revise the next bounded task or evidence requirement.
  - Must not widen scope, redefine acceptance, or silently skip missing evidence.
- `rollback`
  - May identify rollback target, rollback reason, and safe sequence.
  - Must stop before destructive git or workspace mutation unless the programmer explicitly approves it.
  - Must not assume rollback alone resolves the underlying failure classification.
- `split-worktrack`
  - May propose a new bounded split shape and follow-up worktrack identities.
  - Must not silently create, schedule, or switch to new worktracks from this skill.
  - Must preserve which acceptance criteria stay in the current worktrack and which move out.
- `refresh-baseline`
  - May request a repo-level baseline refresh or re-initialization trigger when upstream truth changed or drift invalidated the current branch comparison.
  - Must not rewrite `Repo Snapshot / Status`, `Goal / Charter`, or control truth from this skill.
  - Must return a handoff that tells `Harness` which repo-facing round is needed next.

## Hard Constraints

- Do not issue the final `Gate` verdict from this skill; consume it only as recovery input.
- Do not keep executing inside the failed path just because a retry seems plausible.
- Do not treat `rollback`, `split-worktrack`, or `refresh-baseline` as implementation details hidden from the programmer.
- Do not widen the current worktrack beyond its approved goal, non-goals, and authority boundary.
- Do not pass full-repo context to the `gpt-5.4-xhigh` `SubAgent` when a bounded recovery packet is sufficient.
- Do not mutate `Harness Control State`, create new worktracks, or rewrite repo truth from this skill.
- Do not collapse recovery classification, recovery choice, and approval boundary into one vague narrative.

## Expected Output

When you use this skill, produce a `Recovery Choice Result` with at least these sections:

- `Recovery Trigger`
- `Recovery Option Assessment`
- `Selected Recovery Path`
- `Recovery Authority Handoff`
- `Open Risks And Follow-Up`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `recovery_trigger`
- `failure_classification`
- `current_worktrack_state`
- `selected_recovery_mode`
- `selection_reason`
- `fallback_recovery_mode`
- `retry_viability`
- `rollback_target_or_rule`
- `split_rationale`
- `baseline_refresh_reason`
- `authority_boundary`
- `immediate_safe_actions`
- `approval_required`
- `follow_up_artifacts`
- `open_risks`
- `recommended_next_action`
- `needs_programmer_approval`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded worktrack-recovery round and the minimum context packet that should be handed to the `gpt-5.4-xhigh` `SubAgent`.
