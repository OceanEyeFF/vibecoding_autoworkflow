---
name: execution-contract-template
description: Repo-local Codex adapter for the Harness Operations Execution Contract Template skill.
---

# Execution Contract Template (Repo Adapter)

This folder is a repo-local backend adapter. It does not define contract truth by itself.

## Canonical Source

1. `product/harness-operations/skills/execution-contract-template/SKILL.md`
2. `product/harness-operations/skills/execution-contract-template/references/entrypoints.md`
3. `product/harness-operations/skills/execution-contract-template/references/prompt.md`
4. `product/harness-operations/skills/execution-contract-template/references/bindings.md`

## Backend Notes

- `agents/openai.yaml` is interface metadata only.
- No backend delta. Use the canonical contract semantics and bindings verbatim.

## Deploy Target

- `.agents/skills/` is the repo-local deploy target. It is not a truth layer.
