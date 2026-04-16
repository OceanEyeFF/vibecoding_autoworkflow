---
name: harness-skill
description: Agents thin-shell payload for the first-wave Harness supervisor skill. Read the canonical Harness package in product/harness/skills/harness-skill/ before execution.
---

# Harness Skill Agents Wrapper

## Canonical Source

Read the canonical package below before using this wrapper:

1. `product/harness/skills/harness-skill/SKILL.md`
2. `product/harness/skills/harness-skill/references/entrypoints.md`

Tracing metadata:

- manifest: `product/harness/manifests/agents/skills/harness-skill.json`
- payload descriptor: `product/harness/adapters/agents/skills/harness-skill/payload.json`

## Backend Notes

- backend: `agents`
- wrapper role: first-wave thin-shell payload
- first-wave scope kind: `full-skill`
- runtime rule: use the canonical files above as the authority; this wrapper only carries backend routing and target metadata
- duplication rule: do not restate the canonical workflow, output contract, or doctrine in this wrapper

## Deploy Target

- target directory: `harness-skill`
- target entry name: `SKILL.md`
- payload policy: `thin-shell`
- supported target scopes: `local`
- references distribution: `repo-read-through-local-only`
- required payload files:
  - `SKILL.md`
  - `payload.json`
