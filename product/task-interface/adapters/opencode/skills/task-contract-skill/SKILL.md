---
name: task-contract-skill
description: Repo-local OpenCode adapter for the Task Interface Task Contract skill in this repository.
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
- Use this wrapper only to expose the same Task Interface boundary to OpenCode-side runners.

## Execution Rules

1. Read the canonical skill and entrypoints before drafting a `Task Contract`.
2. Extract only confirmed facts from the discussion and canonical docs.
3. Mark unresolved items as `pending` instead of filling them with guesses.
4. Stop before implementation, agent assignment, or execution planning.

## OpenCode Notes

- Prefer exact doc paths and exact field names over broad summaries.
- `.opencode/skills/` is the repo-local deploy target. It is never a truth layer.

## Output Contract

Return the same contract as the canonical skill:

- `Task Contract Role`
- `Project Baseline`
- `Current Task Contract`
- `Open Decisions`
- `Downstream Consumption`
