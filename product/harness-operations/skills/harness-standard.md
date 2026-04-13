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
- Use explicit task input as the highest-precedence override for runtime-bound source values such as `task_source_ref`.
- When no explicit source override is provided, read `runtime.task_source_ref` from `harness.yaml`.
- Only when `task_source_ref` is missing or `pending` may the harness infer a fallback diff source.
- If a required placeholder is missing, stop and report instead of guessing.

## Gate Discipline

- Run scope gate before static/test/smoke gates whenever workflow requires scope control.
- Backfill gate results to runtime artifacts after each verification phase.
- Keep evidence tied to the current run id.
- Treat `task_source_ref` as the workflow source anchor, not as permission to ignore the live worktree.
- If an explicit or runtime `task_source_ref` cannot be resolved, stop with an unresolved-source error instead of falling back.
- If a resolved source and the live worktree disagree because extra non-excluded paths are dirty, stop and report a dirty scope conflict.
- Excluded runtime paths do not count as scope violations, but they also do not satisfy the "valid changed files exist" requirement on their own.

## State Discipline

- Runtime status updates must only touch `.autoworkflow/` state files.
- Canonical docs under `docs/deployable-skills/` and `docs/project-maintenance/` are writeback targets only for verified facts.
- Adapter deploy targets (`.agents/`, `.claude/`, `.opencode/`) are never truth sources.
