---
name: task-planning-contract
description: Use this skill when a requirement document or issue list must be normalized into executable task units with dependencies and validation.
---

# Task Planning Contract

## Overview

Use this skill to transform one requirement source into a structured task plan that downstream executors can consume directly.

## When To Use

Use this skill when the input still contains multiple issues, problem statements, or implementation demands that must be normalized before execution starts.

## Workflow

1. Read `references/entrypoints.md`.
2. Load the requirement source and the minimum canonical docs needed to define task boundaries.
3. Split the work into the smallest independently verifiable task units.
4. Add dependencies, risk notes, validation plans, and exit criteria for each task.
5. Emit one structured task planning document plus batch guidance.

## Hard Constraints

- Do not merge unrelated work into one vague task.
- Do not assign execution to runtime-specific agents inside the task plan.
- Do not hide unknowns; mark them explicitly as risks or missing inputs.
- Keep the output usable without hidden context.

## Expected Output

When you use this skill, produce a compact result that includes:

- `task_inventory`
- `task_matrix`
- `dependency_graph`
- `batch_order`
- `parallel_groups`
- `high_risk_tasks`

## Resources

Read `references/entrypoints.md` first. Use `prompt.md` as the backend-agnostic prompt body, apply shared rules from `product/harness-operations/skills/harness-standard.md`, and use `references/bindings.md` before substituting host-repo values.
