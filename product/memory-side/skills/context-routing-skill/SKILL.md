---
name: context-routing-skill
description: Use this skill when a task is about to start and you need a minimal reading boundary or a fixed-format Route Card.
---

# Context Routing Skill

## Overview

Use this skill to generate a minimal `Route Card` before execution starts.

## When To Use

Use this skill when a task needs a tighter reading boundary, ordered entrypoints, or a fixed-format `Route Card`.

## Workflow

1. Read `references/entrypoints.md`.
2. Determine the task type.
3. Load the smallest set of canonical docs required for that task type.
4. Add the minimum code entrypoints needed to begin work.
5. Produce a fixed-format `Route Card`.

## Hard Constraints

- Do not default to whole-repo scanning.
- Do not turn the `Route Card` into an execution plan.
- Do not push unneeded `ideas`, `discussions`, `thinking`, or `archive` into the default path.
- Stop expanding the reading set once the task has enough context to begin.

## Expected Output

When you use this skill, produce a `Route Card` with at least these fields:

- `task_type`
- `goal`
- `read_first`
- `read_next`
- `code_entry`
- `do_not_read_yet`
- `stop_reading_when`

## Resources

Read `references/entrypoints.md` first. It tells you which canonical docs define routing rules and output format.
