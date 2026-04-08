---
name: context-routing-skill
description: Repo-local Codex adapter for the Memory Side Context Routing skill.
---

# Context Routing Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define routing rules.

## Canonical Source

1. `product/memory-side/skills/context-routing-skill/SKILL.md`
2. `product/memory-side/skills/context-routing-skill/references/entrypoints.md`

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical skill semantics and output contract verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
