---
name: dispatch-skills
description: Agents thin-shell payload for the first-wave Worktrack dispatch skill. Read the canonical dispatch package in product/harness/skills/dispatch-skills/ before execution.
---

# Dispatch Skills Agents Wrapper

## Canonical Source

Read the canonical package below before using this wrapper:

1. `product/harness/skills/dispatch-skills/SKILL.md`
2. `product/harness/skills/dispatch-skills/references/entrypoints.md`

Tracing metadata:

- manifest: `product/harness/manifests/agents/skills/dispatch-skills.json`
- payload descriptor: `product/harness/adapters/agents/skills/dispatch-skills/payload.json`

## Backend Notes

- backend: `agents`
- wrapper role: first-wave thin-shell payload
- first-wave scope kind: `subset-by-a3-freeze`
- first-wave runtime boundary: prove the bounded dispatch contract plus fallback or general-executor path
- excluded first-wave work: full specialized-skill packaging coverage and downstream lifecycle expansion
- duplication rule: do not restate the canonical workflow, output contract, or doctrine in this wrapper

## Deploy Target

- target directory: `dispatch-skills`
- target entry name: `SKILL.md`
- payload policy: `thin-shell`
- supported target scopes: `local`
- references distribution: `repo-read-through-local-only`
- required payload files:
  - `SKILL.md`
  - `payload.json`
