---
name: writeback-cleanup-skill
description: >
  Repo-local Claude adapter for the Memory Side Writeback Cleanup skill.
  Read the canonical Memory Side skill and canonical docs, then produce the
  minimal Writeback Card for this repository.
allowed-tools: Read, Grep, Glob, Bash
---

# Writeback Cleanup Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define writeback truth by itself.

## Canonical Sources

Always load the canonical skill layer first:

1. `toolchain/skills/aw-kernel/memory-side/writeback-cleanup-skill/SKILL.md`
2. `toolchain/skills/aw-kernel/memory-side/writeback-cleanup-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Adapter Role

Use this wrapper to apply the canonical `writeback-cleanup-skill` inside this repository.

- Keep writeback truth in `docs/knowledge/`.
- Keep canonical skill semantics in `toolchain/skills/aw-kernel/memory-side/`.
- Prefer this project-level skill before inventing a Claude-specific subagent flow.

## Execution Rules

1. Read the canonical skill and entrypoints before building a `Writeback Card`.
2. Collect actual changes, non-changes, and verification basis before proposing any writeback.
3. Keep unverified claims out of canonical docs.
4. Use cleanup to remove stale guidance, not to erase useful history.

## Claude Notes

- Keep the same capability boundary as `.agents/skills/writeback-cleanup-skill/`.
- Do not expand this into a large subagent catalog.
- Use project-level skills first; only consider subagents later if the task truly needs orchestration.

## Output Contract

Return the same contract as the canonical skill:

- `task`
- `verified_changes`
- `non_changes`
- `write_to_core_truth`
- `write_to_operational_truth`
- `do_not_write_back`
- `cleanup_targets`
- `risks_left`
- `verification_basis`
