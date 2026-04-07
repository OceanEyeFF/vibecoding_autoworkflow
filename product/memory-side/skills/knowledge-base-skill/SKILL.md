---
name: knowledge-base-skill
description: Use this skill when you need to classify repository docs, repair Knowledge Base entrypoints, or apply the smallest safe mainline doc update.
---

# Knowledge Base Skill

## Overview

Use this skill to keep `docs/` aligned with the repo-local Knowledge Base without turning the skill into a second truth layer.

## When To Use

Use this skill when the task needs Knowledge Base classification, entrypoint repair, or another smallest-safe mainline doc update.

## Workflow

1. Read `references/entrypoints.md`.
2. Load only the canonical docs needed for the current repository state.
3. Determine whether the repo is in `Bootstrap` or `Adopt` mode.
4. Classify the relevant docs and entrypoints.
5. Apply the smallest safe Knowledge Base update.

## Hard Constraints

- Treat `docs/` as the truth layer. Do not store project truth inside this skill.
- Do not rewrite an existing doc system unless the task explicitly requires it.
- Do not promote unconfirmed ideas or archive material into the mainline.
- Prefer adding entrypoints, status fields, indexes, and links over large rewrites.

## Expected Output

When you use this skill, produce a compact result that includes:

- `mode`: `Bootstrap` or `Adopt`
- `layer_classification`
- `broken_or_missing_entrypoints`
- `smallest_required_updates`

## Resources

Read `references/entrypoints.md` first. It tells you which canonical docs to load and in what order.
