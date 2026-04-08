---
name: repo-governance-evaluation
description: Use this skill when a repository needs a governance and maintainability audit with evidence-backed scoring and harness compatibility assessment.
---

# Repo Governance Evaluation

## Overview

Use this skill to assess repository governance, maintainability, and AI or harness handoff readiness.

## When To Use

Use this skill before planning, before handoff, or before closeout when the repository needs an evidence-backed governance audit.

## Workflow

1. Read `references/entrypoints.md`.
2. Collect the minimum documentary and structural evidence needed for scoring.
3. Score the defined governance dimensions with explicit proof.
4. Produce prioritized issues and short-horizon improvement actions.
5. Report whether the repository is AI or harness compatible.

## Hard Constraints

- Do not infer evidence that you did not inspect.
- Do not reward documentation volume without governance quality.
- Keep change governance as the highest-priority evaluation dimension.
- Do not declare overall pass when the `code` dimension is not acceptable.

## Expected Output

When you use this skill, produce a compact result that includes:

- `repo_type`
- `dimension_scores`
- `evidence`
- `top_issues`
- `improvement_actions`
- `ai_harness_compatibility`

## Resources

Read `references/entrypoints.md` first. Use `references/prompt.md` as the canonical prompt body and `references/bindings.md` before substituting host-repo values.
