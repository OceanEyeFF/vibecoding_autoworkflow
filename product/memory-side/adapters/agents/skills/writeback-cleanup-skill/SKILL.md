---
name: writeback-cleanup-skill
description: Repo-local Codex adapter for the Memory Side Writeback Cleanup skill in this repository.
---

# Writeback Cleanup Skill (Repo Adapter)

This folder is a repo-local backend adapter. It does not define writeback truth by itself.

## Canonical Sources

Always load the canonical skill layer first:

1. `product/memory-side/skills/writeback-cleanup-skill/SKILL.md`
2. `product/memory-side/skills/writeback-cleanup-skill/references/entrypoints.md`
3. The canonical `docs/knowledge/memory-side/` files named there

## Adapter Role

Use this wrapper to apply the canonical `writeback-cleanup-skill` inside this repository.

- Keep writeback truth in `docs/knowledge/`.
- Keep canonical skill semantics in `product/memory-side/skills/`.
- Use this wrapper only to expose the same closeout boundary to Codex/OpenAI-side runners.

## Execution Rules

1. Read the canonical skill and entrypoints before building a `Writeback Card`.
2. Collect actual changes, non-changes, and verification basis before proposing any writeback.
3. Keep unverified claims out of canonical docs.
4. Use cleanup to remove stale guidance, not to erase useful history.

## Codex Notes

- Prefer exact verification evidence and exact target doc paths.
- `.agents/skills/` is the repo-local deploy target. It is never a second writeback log.
- `agents/openai.yaml` is interface metadata only. It is not part of the writeback rules.

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
