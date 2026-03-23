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

## Canonical Sources

Always load the canonical skill layer first:

1. `product/task-interface/skills/task-contract-skill/SKILL.md`
2. `product/task-interface/skills/task-contract-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/` files named there

## Adapter Role

Use this wrapper to apply the canonical `task-contract-skill` inside this repository.

- Keep Task Contract truth in `docs/knowledge/`.
- Keep canonical skill semantics in `product/task-interface/skills/`.
- Prefer this project-level skill before inventing a Claude-specific subagent flow.

## Execution Rules

1. Read the canonical skill and entrypoints before drafting a `Task Contract`.
2. Extract only confirmed facts from the discussion and canonical docs.
3. Mark unresolved items as `pending` instead of filling them with guesses.
4. Stop before implementation, agent assignment, or execution planning.

## Claude Notes

- `.claude/skills/` is the repo-local deploy target.
- Keep the same capability boundary as `product/task-interface/adapters/agents/skills/task-contract-skill/`.
- Do not expand this into a large subagent catalog.
- Do not store Task Contract truth under `.claude/skills/`.

## Output Contract

Return the same contract as the canonical skill:

- `Task Contract Role`
- `Project Baseline`
- `Current Task Contract`
- `Open Decisions`
- `Downstream Consumption`
