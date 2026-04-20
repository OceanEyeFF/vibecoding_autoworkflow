---
name: gate-skill
description: Use this skill when Harness is in WorktrackScope.judging and needs one bounded gate adjudication round from existing evidence without re-executing work or refreshing repo state.
---

# Gate Skill

## Overview

Use this skill when `Harness` already has the current round's evidence and needs one bounded adjudication pass inside `WorktrackScope.judging`.

This skill packages the minimum gate context for one `gpt-5.4-xhigh` `SubAgent`, evaluates the current `implementation / validation / policy` evidence surfaces, absorbs bounded low-severity noise, and returns a structured verdict plus allowed next routes.

## When To Use

Use this skill when the current question is not "what should we execute next", but "does the current round have enough evidence to pass, fail, or stop":

- review, test, and rule-check evidence has already been collected or summarized
- `Harness` needs a current-round gate verdict from existing artifacts
- evidence may be incomplete, contradictory, or uneven across surfaces
- evidence may include many low-severity findings that should stay residual unless they form a cross-surface or systemic pattern
- repeated symptoms may indicate an upstream contract or governance problem rather than another pure code-fix loop
- the system must choose between `integrating`, `recovering`, or staying blocked
- the adjudication must stay bounded to the current `Worktrack`

## Workflow

1. Load the minimum `WorktrackScope` artifacts and current `Gate Evidence` for this round.
2. Build one `Gate Task Brief` and one `Gate Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
3. Evaluate the current round on three required surfaces:
   - `implementation-gate`
   - `validation-gate`
   - `policy-gate`
4. Apply gate adjudication rules before the overall verdict:
   - absorb bounded low-severity `P2 / P3` residue into `residual_risks` unless it crosses the escalation fence
   - if evidence is flagged `possible_upstream_constraint_issue`, decide whether a pure code-fix route is no longer valid
5. Determine the overall verdict:
   - `pass`
   - `soft-fail`
   - `hard-fail`
   - `blocked`
6. Return one fixed-format `Gate Report` with decisive evidence, missing evidence, and allowed next routes; when useful, keep the result aligned with `templates/gate-evidence.template.md`.
7. Stop before execution, recovery action, closeout, or repo refresh.

## Gate Adjudication Rules

- Low-severity findings, including `P2 / P3`, stay in `residual_risks` by default when they do not break acceptance, recovery-path safety, operator-facing semantics, or contract integrity on any surface.
- A low-severity cluster may contribute to `soft-fail` or `hard-fail` only when at least one escalation fence is hit:
  - the same low-severity pattern appears on at least two of `implementation / validation / policy`
  - after deduplication, there are at least five distinct representative low-severity findings in the current round and the cluster materially reduces confidence in acceptance or recovery
- Do not let raw count alone override the bounded-worktrack view; duplicated variants should be absorbed before verdicting.
- If evidence includes a decisive finding marked `possible_upstream_constraint_issue`, or two or more findings point to the same unresolved contract, boundary, or governance dependency, `recommended_next_route` must not be pure code repair.
- When the upstream-route fence is hit, route to `rule-check`, contract or doc revision, or `recover-worktrack` re-scoping before asking for more implementation churn.

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
- `low_severity_finding_summary`
- `upstream_constraint_signals`
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
- `low_severity_absorption_applied`
- `upstream_route_required`
- `route_reason`
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
- Do not escalate a pile of bounded low-severity findings into `soft-fail` or `hard-fail` solely by count when they stay on one surface and do not threaten acceptance, recovery, or operator-facing semantics.
- Do not recommend pure implementation retry when `possible_upstream_constraint_issue` is decisive or repeated; route upstream explicitly.

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
- `low_severity_absorption_applied`
- `upstream_route_required`
- `route_reason`
- `allowed_next_routes`
- `recommended_next_route`
- `needs_programmer_approval`
- `how_to_review`

## Resources

Use the current round's `Gate Evidence`, `Worktrack Contract`, and `templates/gate-evidence.template.md` when you need a stable gate-report draft shape for this round.
