---
name: repo-governance-evaluation
description: Repo-local Codex adapter for the Harness Operations Repo Governance Evaluation skill.
---

# Repo Governance Evaluation (Repo Adapter)

This folder is a repo-local backend adapter. It does not define governance truth by itself.

## Canonical Source

1. `product/harness-operations/skills/repo-governance-evaluation/SKILL.md`
2. `product/harness-operations/skills/repo-governance-evaluation/references/entrypoints.md`
3. `product/harness-operations/skills/repo-governance-evaluation/references/prompt.md`
4. `product/harness-operations/skills/repo-governance-evaluation/references/bindings.md`

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical governance-evaluation semantics and bindings verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
