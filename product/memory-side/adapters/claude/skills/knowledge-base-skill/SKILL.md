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

## Canonical Sources

Always load the canonical skill layer first:

1. `product/memory-side/skills/knowledge-base-skill/SKILL.md`
2. `product/memory-side/skills/knowledge-base-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Adapter Role

Use this wrapper to apply the canonical `knowledge-base-skill` inside this repository.

- Keep project truth in `docs/knowledge/`.
- Keep canonical skill semantics in `product/memory-side/skills/`.
- Prefer this project-level skill before inventing a Claude-specific subagent flow.

## Execution Rules

1. Read the canonical skill and entrypoints before making any judgment.
2. Load only the canonical docs needed to decide `Bootstrap` vs `Adopt`, layer classification, and entrypoint fixes.
3. Prefer small entrypoint, status, index, and link repairs over broad rewrites.
4. If maintenance is required, update `docs/knowledge/` rather than this wrapper.

## Claude Notes

- `.claude/skills/` is the repo-local deploy target.
- Keep the same capability boundary as `product/memory-side/adapters/agents/skills/knowledge-base-skill/`.
- Do not expand this into a large subagent catalog.
- Do not store repo truth under `.claude/skills/`.

## Output Contract

Return the same contract as the canonical skill:

- current mode: `Bootstrap` or `Adopt`
- current layer classification
- missing or broken mainline entrypoints
- the smallest safe doc updates required
