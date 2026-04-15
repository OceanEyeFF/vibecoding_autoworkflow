---
name: review-evidence-skill
description: Use this skill when Harness is in WorktrackScope.verifying and needs one bounded review-evidence round that collects and synthesizes review findings without issuing the final gate verdict.
---

# Review Evidence Skill

## Overview

Use this skill when `Harness` needs the review lane of `Gate Evidence` for the current `Worktrack`, but does not yet need the final gate adjudication.

This skill runs one bounded review-evidence round with a dedicated `gpt-5.4-xhigh` `SubAgent`, packages the minimum review context for that round, collects code-review and structural-risk signals, and returns a normalized review-evidence slice for later gate synthesis.

It stops before final `pass / soft-fail / hard-fail / blocked` gate judgment.

## When To Use

Use this skill when the current question is not "should the whole worktrack pass the gate", but "what review evidence do we have for this change right now":

- collect the review lane for the current `WorktrackScope.verifying` round
- summarize code-review findings against the bounded `Worktrack Contract`
- synthesize diff, structure, and static-review signals into one review-evidence slice
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
6. Normalize the result into one `Review Evidence Report` plus one `Gate Evidence Review Slice`.
7. Stop before issuing the final gate verdict.

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
- `missing_evidence`
- `follow_up_actions`
- `ready_for_gate_synthesis`
- `needs_additional_review`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded review-evidence round and the minimum context packet that should be handed to the `gpt-5.4-xhigh` `SubAgent`.
