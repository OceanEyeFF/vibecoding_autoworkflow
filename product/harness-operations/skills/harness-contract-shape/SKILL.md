---
name: harness-contract-shape
description: Use this skill when a harness-driven workflow needs a minimal contract JSON shape with scope, gates, risk triage, and governance status.
---

# Harness Contract Shape

## Overview

Use this skill to define the minimum JSON contract required for harness-driven workflows.

## When To Use

Use this skill when a review-loop, task-list workflow, or another harness-controlled run needs a stable contract file before execution starts.

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum governance docs needed to understand scope and folder rules.
3. Produce one contract JSON shape with scope, gate status, risk triage, governance state, and workflow metadata.
4. Keep runtime state out of the canonical template body.

## Hard Constraints

- Do not store live runtime state inside the canonical template.
- Do not omit scope or governance fields from the contract shape.
- Do not hardcode host-repo paths directly into the template body when a binding exists.

## Expected Output

When you use this skill, produce a compact result that includes:

- `workflow_id`
- `workflow_type`
- `task_ref`
- `scope`
- `gates`
- `risk_triage`
- `governance`
- `status`
- `last_updated`

## Resources

Read `references/entrypoints.md` first. Use `references/prompt.md` as the canonical template body and `references/bindings.md` before substituting host-repo values.
