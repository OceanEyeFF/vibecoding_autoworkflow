---
name: strict-workflow
description: Use this skill when a cross-module or high-risk task needs frozen scope, staged evidence, and strict stop conditions.
---

# Strict Workflow

## Overview

Use this skill to execute one high-risk task under frozen boundaries and auditable stage-by-stage evidence.

## When To Use

Use this skill when the task spans multiple modules, carries meaningful regression risk, or needs explicit escalation rules.

## Workflow

1. Read `references/entrypoints.md`.
2. Load the source requirement and the minimum canonical docs needed to freeze scope.
3. Produce one execution contract with blocking and rework risks.
4. Execute in stages and emit evidence after each stage.
5. Report gate outcomes and unresolved risks before closeout.

## Hard Constraints

- Freeze `In-scope` and `Out-of-scope` before implementation starts.
- Do not expand scope without an explicit stop-and-escalate step.
- Do not silently downgrade to a weaker or partial solution.
- Stop immediately when any required gate cannot be completed with valid evidence.

## Expected Output

When you use this skill, produce a compact result that includes:

- `execution_contract_summary`
- `stage_evidence`
- `changed_files`
- `gate_results`
- `completion_status`
- `residual_risks`

## Resources

Read `references/entrypoints.md` first. Use `references/prompt.md` as the canonical prompt body and `references/bindings.md` before substituting host-repo values.
