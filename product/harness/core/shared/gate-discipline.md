# Gate Discipline

This file extracts the stable verification and evidence rules shared by Harness workflows.

## Gate ordering

- Run `scope_gate` before static, test, or smoke gates whenever workflow policy requires scope control.
- Keep gate execution tied to the active workflow id and run id.

## Backfill rules

- Backfill gate results to runtime artifacts after each verification phase.
- Evidence must stay tied to the current run id.
- Excluded runtime paths do not count as scope violations.
- Excluded runtime paths also do not satisfy the "valid changed files exist" requirement on their own.

## Stop conditions

- Stop when the workflow source anchor cannot be resolved.
- Stop when the resolved source and live worktree disagree because extra non-excluded paths are dirty.
- Do not silently downgrade to a looser source interpretation.
