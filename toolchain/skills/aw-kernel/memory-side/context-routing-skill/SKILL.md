---
name: context-routing-skill
description: Use this skill when a task is about to start and you need a minimal reading plan, ordered doc and code entrypoints, explicit do-not-read boundaries, or a fixed-format Route Card.
---

# Context Routing Skill

## Overview

Use this skill to generate a minimal `Route Card` before execution starts. The goal is to shrink reading scope, not to summarize the whole project or invent a task plan.

## When To Use

Use this skill when the task involves any of the following:

- a new coding or documentation task is about to start
- the user request is still broad and needs a tighter reading boundary
- the executing model needs explicit doc order, code entrypoints, and do-not-read rules
- multiple backends should start from the same mainline context

Do not use this skill to build the Knowledge Base or to perform task closeout. Those belong to `$knowledge-base-skill` and `$writeback-cleanup-skill`.

## Workflow

1. Read `references/entrypoints.md`.
2. Determine the task type.
3. Load the smallest set of canonical docs required for that task type.
4. Add the minimum code entrypoints needed to begin work.
5. Produce a fixed-format `Route Card`.

## Hard Constraints

- Do not default to whole-repo scanning.
- Do not turn the `Route Card` into an execution plan.
- Do not push `ideas`, `discussions`, `thinking`, or `archive` into the default path unless explicitly needed.
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
