---
name: writeback-cleanup-skill
description: Repo-local Claude adapter for the Memory Side Writeback Cleanup skill.
allowed-tools: Read, Grep, Glob, Bash
---

# Writeback Cleanup Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define writeback truth by itself.

## Canonical Source

1. `product/memory-side/skills/writeback-cleanup-skill/SKILL.md`
2. `product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md`

## Backend Notes

- Prefer the project-level skill before introducing Claude-specific subagents.
- No backend delta beyond Claude metadata and deploy target.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
