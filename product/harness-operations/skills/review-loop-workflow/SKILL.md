---
name: review-loop-workflow
description: Use this skill when a code review must run through a multi-round harness loop with inspection, fixing, meta-review, and integration gating.
---

# Review Loop Workflow

## Overview

Use this skill to run a code-first review loop with structured roles, harness state, and integration-only final acceptance.

## When To Use

Use this skill when the input is a commit, PR, diff range, or target path that needs staged review findings and controlled fix iterations.

## Workflow

1. Read `references/entrypoints.md`.
2. Freeze the review scope and initialize harness state.
3. Run the inspector, fixer, and meta-review stages in the defined order.
4. Re-run the required gates after each repair cycle.
5. Accept only the integration worktree result as final delivery.

## Hard Constraints

- Do not turn review-loop into a broad refactor.
- Do not let fix branches become the final delivery artifact.
- Do not continue when scope violations or missing gates remain unresolved.
- Do not silently downgrade to partial fixes without explicit reporting.

## Expected Output

When you use this skill, produce a compact result that includes:

- `review_scope`
- `findings_and_severity`
- `fixed_vs_blocked_issues`
- `validation_summary`
- `stop_or_continue_recommendation`
- `governance_assessment`

## Resources

Read `references/entrypoints.md` first. Use `references/prompt.md` as the canonical prompt body and `references/bindings.md` before substituting host-repo values.
