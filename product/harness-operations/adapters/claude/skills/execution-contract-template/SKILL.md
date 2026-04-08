---
name: execution-contract-template
description: Repo-local Claude adapter for the Harness Operations Execution Contract Template skill.
allowed-tools: Read, Grep, Glob, Bash
---

# Execution Contract Template (Repo Adapter)

This folder is a repo-local backend adapter. It does not define contract truth by itself.

## Canonical Source

1. `product/harness-operations/skills/execution-contract-template/SKILL.md`
2. `product/harness-operations/skills/execution-contract-template/references/entrypoints.md`
3. `product/harness-operations/skills/execution-contract-template/references/prompt.md`
4. `product/harness-operations/skills/execution-contract-template/references/bindings.md`

## Backend Notes

- No backend delta. Use the canonical contract semantics and bindings verbatim.

## Deploy Target

- `.claude/skills/` is the repo-local deploy target. It is not a truth layer.
