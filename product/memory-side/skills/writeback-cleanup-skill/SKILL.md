---
name: writeback-cleanup-skill
description: Use this skill when a task is ending and you need a fixed-format Writeback Card.
---

# Writeback Cleanup Skill

## Overview

Use this skill to write back verified facts after work is done without turning the closeout into a long retrospective.

## When To Use

Use this skill when a task is ending and you need a fixed-format `Writeback Card` plus minimal cleanup targets.

## Workflow

1. Read `references/entrypoints.md`.
2. Collect the actual changes, non-changes, and verification basis.
3. Map verified facts to `Core Truth`, `Operational Truth`, or no writeback.
4. Identify stale prompts, entrypoints, or assumptions that should be cleaned up.
5. Produce a fixed-format `Writeback Card`.

## Hard Constraints

- Do not write unverified claims into the canonical truth layer.
- Do not confuse process notes with verified facts.
- Do not use cleanup as a reason to delete useful history.
- If a change is still uncertain, leave it out of mainline writeback.

## Expected Output

When you use this skill, produce a `Writeback Card` with at least these fields:

- `task`
- `verified_changes`
- `non_changes`
- `write_to_core_truth`
- `write_to_operational_truth`
- `do_not_write_back`
- `cleanup_targets`
- `risks_left`
- `verification_basis`

## Resources

Read `references/entrypoints.md` first. It tells you which canonical docs define writeback rules and output format.
