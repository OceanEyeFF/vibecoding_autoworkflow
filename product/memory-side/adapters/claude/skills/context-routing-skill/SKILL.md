---
name: context-routing-skill
description: >
  Repo-local Claude adapter for the Memory Side Context Routing skill.
  Read the canonical Memory Side skill and canonical docs, then produce the
  minimal Route Card for this repository.
allowed-tools: Read, Grep, Glob, Bash
---

# Context Routing Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define routing rules.

## Canonical Source

1. `product/memory-side/skills/context-routing-skill/SKILL.md`
2. `product/memory-side/skills/context-routing-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Backend Notes

- Prefer the project-level skill before introducing Claude-specific subagents.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
