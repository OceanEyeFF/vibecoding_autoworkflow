---
name: knowledge-base-skill
description: Repo-local Codex adapter for the Memory Side Knowledge Base skill in this repository.
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
- Modify `docs/knowledge/` when maintenance is required. Do not rewrite this wrapper to store repo truth.

## Execution Rules

1. Read the canonical skill and entrypoints before making any judgment.
2. Load only the canonical docs needed to decide `Bootstrap` vs `Adopt`, layer classification, and entrypoint fixes.
3. Prefer small entrypoint, status, index, and link repairs over broad rewrites.
4. Do not cross into `context-routing-skill` or `writeback-cleanup-skill` unless the task explicitly requires that boundary.

## Codex Notes

- Keep the reading set tight and path-specific.
- `.agents/skills/` is the repo-local deploy target. It is never a second memory layer.
- `agents/openai.yaml` is interface metadata only. It is not part of the truth layer.

## Output Contract

Return the same contract as the canonical skill:

- current mode: `Bootstrap` or `Adopt`
- current layer classification
- missing or broken mainline entrypoints
- the smallest safe doc updates required
