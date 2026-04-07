---
name: writeback-cleanup-skill
description: >
  Repo-local Claude adapter for the Memory Side Writeback Cleanup skill.
  Read the canonical Memory Side skill and canonical docs, then produce the
  minimal Writeback Card for this repository.
allowed-tools: Read, Grep, Glob, Bash
---

# Writeback Cleanup Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define writeback truth by itself.

## Canonical Source

Always load the canonical skill layer first:

1. `product/memory-side/skills/writeback-cleanup-skill/SKILL.md`
2. `product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Backend Notes

- Prefer the project-level skill before introducing Claude-specific subagents.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
