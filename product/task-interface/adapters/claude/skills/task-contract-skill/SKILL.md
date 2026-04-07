---
name: task-contract-skill
description: >
  Repo-local Claude adapter for the Task Interface Task Contract skill.
  Read the canonical Task Interface skill and canonical docs, then produce the
  fixed-format Task Contract for this repository.
allowed-tools: Read, Grep, Glob, Bash
---

# Task Contract Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define Task Contract truth by itself.

## Canonical Source

Always load the canonical skill layer first:

1. `product/task-interface/skills/task-contract-skill/SKILL.md`
2. `product/task-interface/skills/task-contract-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/` files named there

## Backend Notes

- Prefer the project-level skill before introducing Claude-specific subagents.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
