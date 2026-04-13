---
name: execution-contract-template
description: Use this skill when one execution round needs a fixed contract for goal, scope, validation, and exit criteria before changes begin.
---

# Execution Contract Template

## Overview

Use this skill to freeze one execution round into a minimal contract before code or doc changes begin.

## When To Use

Use this skill when the task is ready for implementation but still needs an explicit boundary, validation plan, and exit criteria.

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum canonical docs needed to understand task truth and scope.
3. Produce one execution contract with goal, boundary, plan, validation, and risks.
4. Keep the contract updated if execution scope legitimately changes.
5. Stop if the contract can no longer represent the work safely.

## Hard Constraints

- Do not present unknowns as confirmed facts.
- Do not skip the boundary section.
- Do not continue execution after scope changes without updating the contract.
- Treat the contract as execution scaffolding, not as a replacement for canonical truth docs.

## Expected Output

When you use this skill, produce a compact result that includes:

- `goal`
- `non_goals`
- `in_scope_files`
- `out_of_scope_files`
- `preconditions`
- `plan`
- `validation_plan`
- `exit_criteria`
- `risks`

## Resources

Read `references/entrypoints.md` first. Use `prompt.md` as the backend-agnostic template body, apply shared rules from `product/harness-operations/skills/harness-standard.md`, and use `references/bindings.md` before substituting host-repo values.
