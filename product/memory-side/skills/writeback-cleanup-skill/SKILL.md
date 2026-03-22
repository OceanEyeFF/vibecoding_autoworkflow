---
name: writeback-cleanup-skill
description: Use this skill when a task is ending and you need to decide what verified results should be written back to canonical docs, what should stay out of the truth layer, and which stale entries or prompts should be cleaned up.
---

# Writeback Cleanup Skill

## Overview

Use this skill to produce a minimal `Writeback Card` after work is done. The goal is to write back verified facts to the right doc layer and remove stale guidance from the mainline, not to write a long retrospective.

## When To Use

Use this skill when the task involves any of the following:

- a coding or documentation task has finished
- there is enough verification evidence to decide what is safe to write back
- the repo needs a structured closeout summary for canonical docs
- stale prompts, entrypoints, or assumptions need cleanup

Do not use this skill during task entry or document-system adoption. Those belong to `$context-routing-skill` and `$knowledge-base-skill`.

## Workflow

1. Read `references/entrypoints.md`.
2. Collect the actual changes, non-changes, and verification basis.
3. Map verified facts to `Core Truth`, `Operational Truth`, or no writeback.
4. Identify stale prompts, stale entrypoints, or stale assumptions that should be cleaned up.
5. Produce a fixed-format `Writeback Card`.

## Hard Constraints

- Do not write unverified claims into the canonical truth layer.
- Do not confuse process notes with verified facts.
- Do not use cleanup as a reason to delete useful history.
- If a change is still uncertain, leave it out of mainline writeback and mark it for follow-up.

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
