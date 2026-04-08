---
name: task-list-workflow
description: Use this skill when one source file contains multiple tasks and execution must be normalized, batched, and accepted through a harness-controlled integration flow.
---

# Task List Workflow

## Overview

Use this skill to detect multiple task items, normalize them into a task matrix, execute by batches, and close through integration gates.

## When To Use

Use this skill when the input document contains two or more executable tasks and single-task execution would cause dependency drift or validation gaps.

## Workflow

1. Read `references/entrypoints.md`.
2. Detect the task count and decide whether task-list orchestration is required.
3. Produce the task inventory, execution matrix, dependency graph, and batch plan.
4. Execute each batch in dependency order while updating harness state.
5. Accept only the integration worktree result after all gates pass.

## Hard Constraints

- Do not downgrade a multi-task input to a single-task workflow without proof that only one task exists.
- Do not continue when a P0 task is still information-blocked.
- Do not accept out-of-scope edits or unresolved merge conflicts.
- Do not silently fall back to an incomplete delivery.

## Expected Output

When you use this skill, produce a compact result that includes:

- `task_inventory`
- `task_execution_matrix`
- `batch_progress`
- `task_status_summaries`
- `integration_gate_results`
- `governance_assessment`

## Resources

Read `references/entrypoints.md` first. Use `references/prompt.md` as the canonical prompt body and `references/bindings.md` before substituting host-repo values.
