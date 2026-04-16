---
name: repo-status-skill
description: Agents thin-shell payload for the first-wave RepoScope status observer. Read the canonical repo-status package in product/harness/skills/repo-status-skill/ before execution.
---

# Repo Status Skill Agents Wrapper

## Canonical Source

Read the canonical package below before using this wrapper:

1. `product/harness/skills/repo-status-skill/SKILL.md`
2. `product/harness/skills/repo-status-skill/references/entrypoints.md`

Tracing metadata:

- manifest: `product/harness/manifests/agents/skills/repo-status-skill.json`
- payload descriptor: `product/harness/adapters/agents/skills/repo-status-skill/payload.json`

## Backend Notes

- backend: `agents`
- wrapper role: first-wave thin-shell payload
- first-wave scope kind: `full-skill`
- runtime rule: keep `RepoScope` status observation in the canonical package and treat this wrapper as backend routing only
- duplication rule: do not restate the canonical workflow, output contract, or doctrine in this wrapper

## Deploy Target

- target directory: `repo-status-skill`
- target entry name: `SKILL.md`
- payload policy: `thin-shell`
- supported target scopes: `local`
- references distribution: `repo-read-through-local-only`
- required payload files:
  - `SKILL.md`
  - `payload.json`
