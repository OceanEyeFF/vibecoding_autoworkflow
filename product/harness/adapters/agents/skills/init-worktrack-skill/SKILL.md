---
name: init-worktrack-skill
description: Agents thin-shell payload for the first-wave Worktrack initialization skill. Read the canonical init-worktrack package in product/harness/skills/init-worktrack-skill/ before execution.
---

# Init Worktrack Skill Agents Wrapper

## Canonical Source

Read the canonical package below before using this wrapper:

1. `product/harness/skills/init-worktrack-skill/SKILL.md`
2. `product/harness/skills/init-worktrack-skill/references/entrypoints.md`
3. `product/harness/skills/init-worktrack-skill/templates/contract.template.md`

Tracing metadata:

- manifest: `product/harness/manifests/agents/skills/init-worktrack-skill.json`
- payload descriptor: `product/harness/adapters/agents/skills/init-worktrack-skill/payload.json`

## Backend Notes

- backend: `agents`
- wrapper role: first-wave thin-shell payload
- first-wave scope kind: `subset-by-a3-freeze`
- first-wave runtime boundary: branch, baseline, contract, initial queue, and first executor handoff only
- excluded first-wave work: queue replanning, evidence refresh, implementation, verification, and gate judgment
- duplication rule: do not restate the canonical workflow, output contract, or doctrine in this wrapper

## Deploy Target

- target directory: `init-worktrack-skill`
- target entry name: `SKILL.md`
- payload policy: `thin-shell`
- supported target scopes: `local`
- references distribution: `repo-read-through-local-only`
- required payload files:
  - `SKILL.md`
  - `payload.json`
