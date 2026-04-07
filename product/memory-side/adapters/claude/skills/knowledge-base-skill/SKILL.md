---
name: knowledge-base-skill
description: >
  Repo-local Claude adapter for the Memory Side Knowledge Base skill.
  Read the canonical Memory Side skill and canonical docs, then propose the
  smallest safe Knowledge Base updates for this repository.
allowed-tools: Read, Grep, Glob, Bash
---

# Knowledge Base Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define project truth.

## Canonical Source

1. `product/memory-side/skills/knowledge-base-skill/SKILL.md`
2. `product/memory-side/skills/knowledge-base-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Backend Notes

- Prefer the project-level skill before introducing Claude-specific subagents.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
