---
name: review-loop-workflow
description: Repo-local Claude adapter for the Harness Operations Review Loop Workflow skill.
allowed-tools: Read, Grep, Glob, Bash
---

# Review Loop Workflow (Repo Adapter)

This folder is a repo-local backend adapter. It does not define workflow truth by itself.

## Canonical Source

1. `product/harness-operations/skills/review-loop-workflow/SKILL.md`
2. `product/harness-operations/skills/review-loop-workflow/references/entrypoints.md`
3. `product/harness-operations/skills/review-loop-workflow/references/prompt.md`
4. `product/harness-operations/skills/review-loop-workflow/references/bindings.md`

## Backend Notes

- No backend delta. Use the canonical workflow semantics and bindings verbatim.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
