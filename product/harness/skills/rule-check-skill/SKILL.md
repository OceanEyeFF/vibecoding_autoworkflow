---
name: rule-check-skill
description: Use this skill when Harness is in WorktrackScope.verifying and needs one bounded rule/governance evidence collection round for policy input without issuing the final gate verdict.
---

# Rule Check Skill

## Overview

Use this skill when `Harness` already has an active `Worktrack` and needs one bounded `rule-check` round inside `WorktrackScope.verifying`.

This skill packages the current rule/governance check into a bounded `gpt-5.4-xhigh` `SubAgent` task, collects policy-facing evidence, and returns a structured handoff for later gate use instead of adjudicating the final `policy-gate` by itself.

## When To Use

Use this skill when the current question is not "does the worktrack pass the gate", but "what rule/governance evidence do we have for this round":

- check whether the current diff stays inside the declared scope and layering rules
- verify whether required governance sync items were triggered by the touched surfaces
- run or inspect the minimum applicable rule/governance checks for this round
- collect path, structure, doc-sync, and boundary evidence for `Gate Evidence`
- return policy findings, gaps, and deferred checks to `Harness`

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `WorktrackScope` and governance artifacts needed for the current diff surface.
3. Build one `Rule Check Task Brief` and one `Rule Check Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
4. Determine which governance surfaces are actually in play for this round:
   - root or path layering
   - docs or required-sync obligations
   - skill or template boundary rules
   - branch or review-flow governance, if the work item depends on them
5. Run or inspect only the minimum applicable checks and rule sources for this round.
6. Separate the result into:
   - policy evidence collected
   - violations or scope leaks
   - missing evidence
   - deferred or not-applicable checks
7. Return one fixed-format `Rule Check Report` plus one `Policy Evidence Handoff`.
8. Stop before final gate adjudication.

## Rule Check Contract

Use the same bounded contract shape every time this skill runs.

### Rule Check Task Brief

- `trigger`
- `goal`
- `worktrack`
- `changed_surface`
- `in_scope`
- `out_of_scope`
- `constraints`
- `required_checks`
- `done_signal`

### Rule Check Info Packet

- `current_worktrack_state`
- `relevant_diffs`
- `artifacts_changed`
- `governance_rules_in_play`
- `verification_results_available`
- `known_risks`
- `required_context`
- `open_questions`

### Policy Evidence Handoff

- `policy_evidence_items`
- `violations_or_gaps`
- `required_sync_items`
- `deferred_checks`
- `review_commands`
- `recommended_follow_up`

## Hard Constraints

- Do not issue the final `pass / soft-fail / hard-fail / blocked` gate verdict from this skill.
- Do not widen the task from bounded rule/governance evidence collection into a full repo audit.
- Do not invent compliance; if evidence is missing, return `missing evidence` explicitly.
- Do not rewrite the `Worktrack Contract`, acceptance criteria, or non-goals from this skill.
- Do not treat review evidence or test evidence as rule-check evidence unless you are explicitly referencing them as inputs.
- Do not mutate `Harness Control State`, merge state, or canonical truth docs from this skill.
- Do not hide required sync obligations when touched paths clearly trigger them.
- Do not collapse violations, missing evidence, and deferred checks into one vague summary.

## Expected Output

When you use this skill, produce a `Rule Check Report` with at least these sections:

- `Rule Check Trigger`
- `Rule Surface Assessment`
- `Checks Run Or Inspected`
- `Policy Evidence Collected`
- `Violations And Gaps`
- `Deferred Or Not-Applicable Checks`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `worktrack`
- `changed_surface`
- `checks_run`
- `checks_passed`
- `policy_evidence_items`
- `violations_found`
- `missing_evidence`
- `required_sync_items`
- `deferred_checks`
- `ready_for_gate_input`
- `recommended_follow_up`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded `rule-check` round and tells you when to pull in extra governance or adjacent-system context.
