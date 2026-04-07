---
name: task-contract-skill
description: Use this skill when a task discussion has converged and you need a fixed-format Task Contract.
---

# Task Contract Skill

## Overview

Use this skill to turn a converged discussion into one formal execution baseline.

## When To Use

Use this skill when a discussion has converged and multiple executors should share one fixed-format `Task Contract`.

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum canonical docs needed to define Task Interface boundaries.
3. Extract confirmed facts and isolate unresolved points as `pending`.
4. Produce a fixed-format `Task Contract`.
5. Stop before coding, agent assignment, or execution planning.

## Hard Constraints

- Do not invent facts that were not confirmed in the discussion or canonical docs.
- Do not turn the output into a multi-step execution plan.
- Do not assign agents or define runtime orchestration.
- Do not merge `Route Card` or `Writeback Card` fields into the result.
- Do not treat repo-local deploy targets as truth sources.

## Expected Output

When you use this skill, produce a `Task Contract` with at least these sections:

- `Task Contract Role`
- `Project Baseline`
- `Current Task Contract`
- `Open Decisions`
- `Downstream Consumption`

Inside `Current Task Contract`, include at least:

- `task`
- `goal`
- `non_goals`
- `in_scope`
- `out_of_scope`
- `acceptance_criteria`
- `constraints`
- `dependencies`
- `risks`
- `verification_requirements`

## Resources

Read `references/entrypoints.md` first. It tells you which canonical docs define Task Interface boundaries and the Task Contract structure.
