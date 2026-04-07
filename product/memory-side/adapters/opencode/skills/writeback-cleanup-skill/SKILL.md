---
name: writeback-cleanup-skill
description: Repo-local OpenCode adapter for the Memory Side Writeback Cleanup skill in this repository.
---

# Writeback Cleanup Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define writeback truth by itself.

## Canonical Source

Always load the canonical skill layer first:

1. `product/memory-side/skills/writeback-cleanup-skill/SKILL.md`
2. `product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Backend Notes

- No backend delta. Use the canonical skill semantics and output contract verbatim.

## Deploy Target

- `.opencode/skills/` is the repo-local deploy target. It is not a truth layer.
