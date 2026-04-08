---
name: simple-workflow
description: Use this skill when a small or medium task needs one explicit execution contract, fixed gates, and strict boundary control.
---

# Simple Workflow

## Overview

Use this skill to drive one constrained implementation task from contract generation to closeout.

## When To Use

Use this skill when the task is already scoped enough for direct execution and does not require multi-task batching or review-loop orchestration.

## Workflow

1. Read `references/entrypoints.md`.
2. Load the source requirement and the minimum canonical docs needed to define scope.
3. Produce one execution contract before making changes.
4. Execute only within the frozen scope.
5. Report gate results, completion state, and residual risks.

## Hard Constraints

- Do not expand the task boundary without stopping first.
- Do not silently downgrade to a partial fallback.
- Stop on missing inputs, missing environment, or scope conflicts.
- Treat repo-local deploy targets and runtime state as non-authoritative.

## Expected Output

When you use this skill, produce a compact result that includes:

- `execution_contract_summary`
- `changed_files`
- `completion_status`
- `validation`
- `residual_risks`

## Resources

Read `references/entrypoints.md` first. Use `references/prompt.md` as the canonical prompt body and `references/bindings.md` before substituting host-repo values.
