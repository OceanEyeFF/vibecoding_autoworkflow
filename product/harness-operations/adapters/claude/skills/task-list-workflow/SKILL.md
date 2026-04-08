---
name: task-list-workflow
description: Repo-local Claude adapter for the Harness Operations Task List Workflow skill.
allowed-tools: Read, Grep, Glob, Bash
---

# Task List Workflow (Repo Adapter)

This folder is a repo-local backend adapter. It does not define workflow truth by itself.

## Canonical Source

1. `product/harness-operations/skills/task-list-workflow/SKILL.md`
2. `product/harness-operations/skills/task-list-workflow/references/entrypoints.md`
3. `product/harness-operations/skills/task-list-workflow/references/prompt.md`
4. `product/harness-operations/skills/task-list-workflow/references/bindings.md`

## Backend Notes

- No backend delta. Use the canonical workflow semantics and bindings verbatim.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
