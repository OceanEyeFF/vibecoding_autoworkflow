# Harness Standard

## Contract vs Runtime

- `contract` is stable execution policy and validation boundary.
- `runtime` is per-run mutable state and ephemeral context.
- Never write runtime state back into canonical skill source.

## Source of Runtime Bindings

- Default file: `.autoworkflow/harness.yaml`.
- Required split:
  - `contract.*`: workflow policy, gate sequence, governance dimensions, and path boundaries.
  - `runtime.*`: workflow id, task reference, active state file, current contract file, and timestamps.

## Placeholder Policy

- Treat `${...}` placeholders as host-runtime bindings.
- Resolve placeholders from `harness.yaml` first, then explicit task input.
- If a required placeholder is missing, stop and report instead of guessing.

## Gate Discipline

- Run scope gate before static/test/smoke gates whenever workflow requires scope control.
- Backfill gate results to runtime artifacts after each verification phase.
- Keep evidence tied to the current run id.

## State Discipline

- Runtime status updates must only touch `.autoworkflow/` state files.
- Canonical docs under `docs/deployable-skills/` and `docs/project-maintenance/` are writeback targets only for verified facts.
- Adapter deploy targets (`.agents/`, `.claude/`, `.opencode/`) are never truth sources.
