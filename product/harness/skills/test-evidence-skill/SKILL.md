---
name: test-evidence-skill
description: Use this skill when Harness is in WorktrackScope and needs one bounded validation round that collects test evidence against acceptance criteria and verification requirements.
---

# Test Evidence Skill

## Overview

Use this skill when `Harness` already has an active `Worktrack` and needs one bounded validation round to collect test evidence for the current change.

This skill packages the minimum validation context for one `gpt-5.4-xhigh` `SubAgent`, maps checks to the current acceptance criteria and verification requirements, and returns a structured evidence report for later gate judgment.

## When To Use

Use this skill when the current question is not "what should we build next", but "what evidence do we have that this work satisfies the stated acceptance and verification bar":

- implementation or content changes already exist for the current work item
- `Worktrack Contract` defines acceptance criteria that now need validation coverage
- the current round has explicit `verification_requirements`
- `Harness` needs fresh or reused test evidence before gate judgment
- the next step depends on a clear statement of what was validated, what failed, and what remains uncovered

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum `WorktrackScope` artifacts for the current validation round.
3. Build one `Test Evidence Task Brief` and one `Test Evidence Info Packet` for a bounded `gpt-5.4-xhigh` `SubAgent`.
4. Build a validation mapping for this round:
   - which acceptance criteria are in scope
   - which verification requirements apply
   - which checks, commands, or existing results can satisfy them
5. Collect or refresh bounded validation evidence only for this round:
   - reuse fresh and trustworthy results when they already satisfy the requirement
   - run the exact missing checks when the requirement still lacks evidence
   - mark a requirement as blocked or uncovered when the needed evidence cannot be produced safely
6. Produce one fixed-format `Validation Evidence Report`.
7. Stop before review synthesis, gate judgment, recovery planning, or closeout.

## Test Evidence Contract

Use the same bounded contract shape every time this skill runs.

### Test Evidence Task Brief

- `trigger`
- `validation_goal`
- `current_work_item`
- `acceptance_criteria`
- `verification_requirements`
- `in_scope`
- `out_of_scope`
- `constraints`
- `done_signal`

### Test Evidence Info Packet

- `current_worktrack_state`
- `relevant_change_summary`
- `impacted_modules`
- `available_test_surfaces`
- `existing_evidence`
- `environment_constraints`
- `required_context`
- `known_risks`

### Validation Evidence Report

- `subagent_model`
- `validation_scope`
- `acceptance_coverage`
- `verification_results`
- `checks_run_or_reused`
- `evidence_artifacts`
- `uncovered_or_blocked_items`
- `open_issues`
- `recommended_next_action`

## Hard Constraints

- Do not redefine acceptance criteria, non-goals, or verification requirements.
- Do not treat a claimed manual check, a green diff, or a vague confidence statement as sufficient evidence by itself.
- Do not convert missing evidence into an implicit pass; return uncovered or blocked status explicitly.
- Do not turn this skill into code review synthesis, policy checking, or final gate judgment.
- Do not pass broad repo context when a bounded validation packet is sufficient.
- Do not mutate `Harness Control State`, close the worktrack, or recommend merge directly from this skill.
- Do not hide failing or flaky checks; include them in the returned evidence surface.

## Expected Output

When you use this skill, produce a `Validation Evidence Report` with at least these sections:

- `Validation Target`
- `Acceptance Coverage`
- `Verification Execution`
- `Evidence Collected`
- `Uncovered Or Blocked Items`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `subagent_model`
- `validation_goal`
- `current_work_item`
- `acceptance_criteria_checked`
- `verification_requirements_checked`
- `coverage_summary`
- `checks_run`
- `checks_reused`
- `results_by_check`
- `evidence_paths_or_commands`
- `uncovered_requirements`
- `blocked_requirements`
- `open_issues`
- `ready_for_gate`
- `recommended_next_action`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one bounded validation round and tells you when to pull in task-interface context for stronger verification requirements.
