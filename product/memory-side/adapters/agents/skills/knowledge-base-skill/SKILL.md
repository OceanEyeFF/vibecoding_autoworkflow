---
name: knowledge-base-skill
description: Repo-local Codex adapter for the Memory Side Knowledge Base skill in this repository.
---

# Knowledge Base Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define project truth.

## Canonical Source

1. `product/memory-side/skills/knowledge-base-skill/SKILL.md`
2. `product/memory-side/skills/knowledge-base-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical skill semantics and output contract verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
