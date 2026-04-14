# Runtime Binding Policy

This file extracts the stable placeholder and source-binding rules from the legacy Harness composite source.

## Placeholder rules

- Treat `${...}` placeholders as host-runtime bindings.
- Explicit task input is the highest-precedence override for runtime-bound source values such as `task_source_ref`.
- When no explicit source override is provided, read `runtime.task_source_ref` from `harness.yaml`.
- Only when `task_source_ref` is missing or `pending` may the harness infer a fallback diff source.
- If a required placeholder is missing, stop and report instead of guessing.

## Source-anchor rules

- `task_source_ref` is the workflow source anchor.
- `task_source_ref` is not permission to ignore the live worktree.
- If the source anchor cannot be resolved, stop with `unresolved-source`.
- If the source anchor resolves but the live worktree contains extra non-excluded dirty paths, stop with a dirty scope conflict.
