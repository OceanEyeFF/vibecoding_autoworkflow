---
name: context-routing-skill
description: >
  Repo-local Claude adapter for the Memory Side Context Routing skill.
  Read the canonical Memory Side skill and canonical docs, then produce the
  minimal Route Card for this repository.
allowed-tools: Read, Grep, Glob, Bash
---

# Context Routing Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define route rules by itself.

## Canonical Sources

Always load the canonical skill layer first:

1. `product/memory-side/skills/context-routing-skill/SKILL.md`
2. `product/memory-side/skills/context-routing-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Adapter Role

Use this wrapper to apply the canonical `context-routing-skill` inside this repository.

- Keep routing truth in `docs/knowledge/memory-side/`.
- Keep canonical skill semantics in `product/memory-side/skills/`.
- Prefer this project-level skill before inventing a Claude-specific subagent flow.

## Execution Rules

1. Read the canonical skill and entrypoints before building a `Route Card`.
2. Stop after loading the minimum docs and code entrypoints needed to start work.
3. Do not turn the result into an execution plan.
4. Do not push `ideas`, `discussions`, `thinking`, or `archive` content into the default reading path unless the task explicitly needs it.

## Claude Notes

- `.claude/skills/` is the repo-local deploy target.
- Keep the same capability boundary as `product/memory-side/adapters/agents/skills/context-routing-skill/`.
- Do not expand this into a large subagent catalog.
- Use project-level skills first; only consider subagents later if the task truly needs orchestration.

## Output Contract

Return the same contract as the canonical skill:

- `task_type`
- `goal`
- `read_first`
- `read_next`
- `code_entry`
- `do_not_read_yet`
- `stop_reading_when`
