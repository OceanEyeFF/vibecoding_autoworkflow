---
name: strict-workflow
description: Repo-local Codex adapter for the Harness Operations Strict Workflow skill.
---

# Strict Workflow (Repo Adapter)

This folder is a repo-local backend adapter. It does not define workflow truth by itself.

## Canonical Source

1. `product/harness-operations/skills/strict-workflow/SKILL.md`
2. `product/harness-operations/skills/strict-workflow/references/entrypoints.md`
3. `product/harness-operations/skills/strict-workflow/references/prompt.md`
4. `product/harness-operations/skills/strict-workflow/references/bindings.md`

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical workflow semantics and bindings verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
