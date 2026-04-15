---
name: gate-skill
description: Use this skill when Harness is in WorktrackScope.judging and needs one bounded gate adjudication round from existing evidence without re-executing work or refreshing repo state.
---

# Gate Skill

## Overview

Use this skill when `Harness` already has the current round's evidence and needs one bounded adjudication pass inside `WorktrackScope.judging`.

This skill packages the minimum gate context for one `gpt-5.4-xhigh` `SubAgent`, evaluates the current `implementation / validation / policy` evidence surfaces, and returns a structured verdict plus allowed next routes.

## When To Use

Use this skill when the current question is not "what should we execute next", but "does the current round have enough evidence to pass, fail, or stop":

- review, test, and rule-check evidence has already been collected or summarized
- `Harness` needs a current-round gate verdict from existing artifacts
- evidence may be incomplete, contradictory, or uneven across surfaces
- the system must choose between `integrating`, `recovering`, or staying blocked
- the adjudication must stay bounded to the current `Worktrack`

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `WorktrackScope` artifacts and current `Gate Evidence` for this round.
3. Build one `Gate Task Brief` and one `Gate Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
4. Evaluate the current round on three required surfaces:
   - `implementation-gate`
   - `validation-gate`
   - `policy-gate`
5. Determine the overall verdict:
   - `pass`
   - `soft-fail`
   - `hard-fail`
   - `blocked`
6. Return one fixed-format `Gate Report` with decisive evidence, missing evidence, and allowed next routes.
7. Stop before execution, recovery action, closeout, or repo refresh.

## Gate Adjudication Contract

Use the same bounded contract shape every time this skill runs.

### Gate Task Brief

- `trigger`
- `goal`
- `current_worktrack`
- `current_round`
- `in_scope`
- `out_of_scope`
- `verdict_options`
- `adjudication_rules`
- `done_signal`

### Gate Info Packet

- `current_worktrack_state`
- `worktrack_contract_summary`
- `queue_state_relevant_to_judgment`
- `implementation_evidence`
- `validation_evidence`
- `policy_evidence`
- `known_gaps_or_conflicts`
- `required_context`

### Gate Verdict Handoff

- `implementation_gate`
- `validation_gate`
- `policy_gate`
- `overall_verdict`
- `decisive_evidence`
- `missing_or_conflicting_evidence`
- `residual_risks`
- `allowed_next_routes`
- `recommended_next_route`
- `approval_request`

## Hard Constraints

- Do not execute fixes, rerun implementation work, or collect fresh repo state from this skill.
- Do not treat missing evidence as implied success; surface the gap explicitly.
- Do not collapse per-surface judgments into one vague overall verdict.
- Do not rewrite the `Worktrack Contract`, acceptance criteria, or non-goals.
- Do not jump directly into recovery, merge, closeout, or repo refresh from this skill.
- Do not mutate `Harness Control State`; return an adjudication result for supervisor use instead.
- Do not expand into adjacent systems unless the current evidence boundary clearly depends on them.

## Expected Output

When you use this skill, produce a `Gate Report` with at least these sections:

- `Gate Trigger`
- `Evidence Assessment`
- `Per-Surface Verdicts`
- `Overall Gate Verdict`
- `Allowed Next Routes`
- `Programmer Review Request`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `gate_trigger`
- `current_worktrack`
- `current_round`
- `implementation_gate`
- `validation_gate`
- `policy_gate`
- `overall_verdict`
- `decisive_evidence`
- `missing_or_conflicting_evidence`
- `residual_risks`
- `allowed_next_routes`
- `recommended_next_route`
- `needs_programmer_approval`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded gate adjudication round and tells you when to pull in `Task Interface` or adjacent-system context.
