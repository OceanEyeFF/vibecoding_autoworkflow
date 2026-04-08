---
name: task-planning-contract
description: Repo-local Codex adapter for the Harness Operations Task Planning Contract skill.
---

# Task Planning Contract (Repo Adapter)

This folder is a repo-local backend adapter. It does not define planning truth by itself.

## Canonical Source

1. `product/harness-operations/skills/task-planning-contract/SKILL.md`
2. `product/harness-operations/skills/task-planning-contract/references/entrypoints.md`
3. `product/harness-operations/skills/task-planning-contract/references/prompt.md`
4. `product/harness-operations/skills/task-planning-contract/references/bindings.md`

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical planning semantics and bindings verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
