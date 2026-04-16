---
name: repo-whats-next-skill
description: Agents thin-shell payload for the first-wave RepoScope next-direction skill. Read the canonical repo-whats-next package in product/harness/skills/repo-whats-next-skill/ before execution.
---

# Repo What's Next Skill Agents Wrapper

## Canonical Source

Read the canonical package below before using this wrapper:

1. `product/harness/skills/repo-whats-next-skill/SKILL.md`
2. `product/harness/skills/repo-whats-next-skill/references/entrypoints.md`
3. `product/harness/skills/repo-whats-next-skill/references/priority-reframe-mode.md`

Tracing metadata:

- manifest: `product/harness/manifests/agents/skills/repo-whats-next-skill.json`
- payload descriptor: `product/harness/adapters/agents/skills/repo-whats-next-skill/payload.json`

## Backend Notes

- backend: `agents`
- wrapper role: first-wave thin-shell payload
- first-wave scope kind: `subset-by-a3-freeze`
- first-wave supported repo actions:
  - `enter-worktrack`
  - `hold-and-observe`
- runtime rule: keep the canonical decision contract, but restrict the `agents` first-wave path to the frozen action subset above
- duplication rule: do not restate the canonical workflow, output contract, or doctrine in this wrapper

## Deploy Target

- target directory: `repo-whats-next-skill`
- target entry name: `SKILL.md`
- payload policy: `thin-shell`
- supported target scopes: `local`
- references distribution: `repo-read-through-local-only`
- required payload files:
  - `SKILL.md`
  - `payload.json`
