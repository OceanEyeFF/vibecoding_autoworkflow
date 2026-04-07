---
name: task-contract-skill
description: Repo-local Claude adapter for the Task Interface Task Contract skill.
allowed-tools: Read, Grep, Glob, Bash
---

# Task Contract Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define Task Contract truth by itself.

## Canonical Source

1. `product/task-interface/skills/task-contract-skill/SKILL.md`
2. `product/task-interface/skills/task-contract-skill/references/entrypoints.md`

## Backend Notes

- Prefer the project-level skill before introducing Claude-specific subagents.
- No backend delta beyond Claude metadata and deploy target.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
