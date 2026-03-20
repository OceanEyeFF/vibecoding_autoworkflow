---
name: knowledge-base-skill
description: Use this skill when you need to bootstrap or adopt a repository documentation system, classify project docs into canonical layers, or repair Knowledge Base entrypoints before routing or execution starts.
---

# Knowledge Base Skill

## Overview

Use this skill to maintain the repo-local Knowledge Base without turning the skill itself into a second truth layer. The canonical truth stays under `docs/`; this skill only guides how to inspect, classify, and minimally update it.

## When To Use

Use this skill when the task involves any of the following:

- establishing a minimal documentation system in a repo that has little structure
- adopting an existing documentation system without rewriting everything
- classifying docs into `Core Truth`, `Operational Truth`, `Exploratory Records`, and `Archive`
- fixing missing entrypoints, status fields, indexes, or links before other work starts

Do not use this skill for task-specific reading plans or task closeout. Those belong to `$context-routing-skill` and `$writeback-cleanup-skill`.

## Workflow

1. Read `references/entrypoints.md`.
2. Load only the canonical docs needed for the current repository state.
3. Decide whether the repo is in `Bootstrap Mode` or `Adopt Mode`.
4. Classify the relevant docs by layer.
5. Propose or apply the smallest safe Knowledge Base changes.

## Hard Constraints

- Treat `docs/` as the truth layer. Do not store project truth inside this skill.
- Do not rewrite an existing doc system unless the task explicitly requires it.
- Do not promote `ideas`, `discussions`, `thinking`, or `archive` material into the mainline without confirmation.
- Prefer adding entrypoints, status fields, indexes, and links over large rewrites.

## Expected Output

When you use this skill, produce a compact result that includes:

- the current mode: `Bootstrap` or `Adopt`
- the current layer classification
- the missing or broken mainline entrypoints
- the smallest set of doc updates required

## Resources

Read `references/entrypoints.md` first. It tells you which canonical docs to load and in what order.
