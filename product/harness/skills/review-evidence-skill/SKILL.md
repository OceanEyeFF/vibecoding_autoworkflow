---
name: review-evidence-skill
description: Use this skill when Harness is in WorktrackScope.verifying and needs one bounded review-evidence round that collects and synthesizes review findings without issuing the final gate verdict.
---

# Review Evidence Skill

## Overview

Use this skill when `Harness` needs the review lane of `Gate Evidence` for the current `Worktrack`, but does not yet need the final gate adjudication.

This skill runs one bounded review-evidence round with a dedicated `gpt-5.4-xhigh` `SubAgent`, packages the minimum review context for that round, collects code-review and structural-risk signals, and returns a normalized review-evidence slice for later gate synthesis.

It stops before final `pass / soft-fail / hard-fail / blocked` gate judgment, and it applies a noise-control fence so low-severity review residue does not keep expanding into new pseudo-blockers.

## When To Use

Use this skill when the current question is not "should the whole worktrack pass the gate", but "what review evidence do we have for this change right now":

- collect the review lane for the current `WorktrackScope.verifying` round
- summarize code-review findings against the bounded `Worktrack Contract`
- synthesize diff, structure, and static-review signals into one review-evidence slice
- separate actionable findings from low-severity residual risks before they sprawl
- flag repeated or boundary-driven symptoms as possible upstream constraint issues
- make explicit what review coverage exists, what is still missing, and what follow-up is needed
- return review evidence for `gate-skill`, `recover-worktrack-skill`, or programmer review

## Workflow

1. Read `references/entrypoints.md`.
2. Confirm this is a bounded review-evidence round, not final gate adjudication, scheduling, or execution dispatch.
3. Load the minimum `WorktrackScope` artifacts and current review inputs for the round.
4. Build one `Review Evidence Task Brief` and one `Review Evidence Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
5. Collect and synthesize the review lane only:
   - diff and change-summary review signals
   - structural or architectural review signals
   - existing code-review comments or inline findings
   - static-review findings that matter to review quality
6. Apply review triage before packaging the result:
   - keep actionable findings focused on acceptance, verification credibility, contract integrity, recovery-path risk, or operator-facing semantic drift
   - keep low-severity residue as representative items plus `residual_risks`, not as an unbounded action queue
   - mark repeated or boundary-driven symptoms with `possible_upstream_constraint_issue`
7. Normalize the result into one `Review Evidence Report` plus one `Gate Evidence Review Slice`.
8. Stop before issuing the final gate verdict.

## Review Triage Rules

- Promote a review item into `findings` only when it threatens acceptance, verify confidence, contract integrity, recovery-path safety, or operator-facing semantics.
- For low-severity items, including `P2 / P3`, that do not hit those triggers and do not show a credible amplification chain, keep at most three representative items in `findings` and fold the rest into `residual_risks`.
- Do not create new `follow_up_actions` for low-severity residue unless the action is needed to restore acceptance coverage, recovery safety, operator-facing semantics, or a broken contract boundary.
- If the same review pattern repeats across files, rounds, or comments, or clearly depends on an unresolved contract, scope, or boundary definition, mark the representative finding with `possible_upstream_constraint_issue: true` and summarize it under `upstream_constraint_signals`.
- Use `follow_up_actions` for bounded next actions that unblock gate synthesis, not as a bucket for every review preference or cleanup thought.

## Review Evidence Contract

Use the same bounded contract shape every time this skill runs.

### Review Evidence Task Brief

- `review_target`
- `goal`
- `in_scope`
- `out_of_scope`
- `review_focus`
- `constraints`
- `acceptance_reference`
- `done_signal`

### Review Evidence Info Packet

- `current_worktrack_state`
- `worktrack_contract_summary`
- `change_summary`
- `diff_or_patch_reference`
- `existing_review_inputs`
- `static_or_structure_signals`
- `known_risks`
- `required_context`
- `missing_evidence`

### Gate Evidence Review Slice

- `review_verdict`
- `findings`
- `severity_map`
- `coverage_assessment`
- `residual_risks`
- `upstream_constraint_signals`
- `missing_evidence`
- `follow_up_actions`
- `confidence`

## Hard Constraints

- Do not issue the final `Gate` verdict for the whole `Worktrack`.
- Do not widen review scope beyond the current `Worktrack Contract`, bounded diff, and acceptance reference.
- Do not treat "no review comments found" as positive evidence by itself.
- Do not dispatch implementation, rewrite the task queue, or mutate `Harness Control State`.
- Do not collapse raw findings, synthesized review judgment, and follow-up actions into one vague summary.
- Do not pass full-repo context to the `gpt-5.4-xhigh` `SubAgent` when a bounded review packet is sufficient.
- Do not overwrite canonical `Gate Evidence`; return a review-evidence slice for downstream synthesis instead.
- Do not expand low-severity findings into new `follow_up_actions` unless they materially threaten acceptance, recovery, operator-facing semantics, or contract integrity.
- Do not keep more than three representative low-severity items in `findings`; aggregate the remainder into `residual_risks`.
- Do not leave repeated or boundary-driven symptoms unlabeled; mark them `possible_upstream_constraint_issue` and surface them in `upstream_constraint_signals`.

## Expected Output

When you use this skill, produce a `Review Evidence Report` with at least these sections:

- `Review Target`
- `Review Evidence Summary`
- `Findings And Severity`
- `Coverage And Confidence`
- `Gate Evidence Review Slice`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `review_target`
- `review_focus`
- `change_summary`
- `review_inputs_used`
- `review_verdict`
- `findings`
- `severity_map`
- `coverage_assessment`
- `residual_risks`
- `upstream_constraint_signals`
- `missing_evidence`
- `follow_up_actions`
- `low_severity_cutoff_applied`
- `ready_for_gate_synthesis`
- `needs_additional_review`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded review-evidence round and the minimum context packet that should be handed to the `gpt-5.4-xhigh` `SubAgent`.
