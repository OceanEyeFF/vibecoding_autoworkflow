---
name: task-contract-skill
description: Repo-local Codex adapter for the Task Interface Task Contract skill in this repository.
---

# Task Contract Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define Task Contract truth by itself.

## Canonical Source

Always load the canonical skill layer first:

1. `product/task-interface/skills/task-contract-skill/SKILL.md`
2. `product/task-interface/skills/task-contract-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/` files named there

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical skill semantics and output contract verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
