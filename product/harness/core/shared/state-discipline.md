# State Discipline

This file extracts the stable write-location and truth-boundary rules shared by Harness workflows.

## Runtime state

- Runtime status updates may only touch `.autoworkflow/` state files.
- Repo-local mount targets are not truth sources.

## Writeback targets

- `docs/harness/` is a canonical writeback target for verified Harness facts.
- `docs/project-maintenance/` is a canonical writeback target for verified repo-local governance and operations facts.
- `docs/deployable-skills/` is transition-only and should receive writeback only when a legacy path still needs compatibility maintenance.

## Non-truth layers

- `.agents/`, `.claude/`, and `.opencode/` are deploy targets, not truth sources.
- Repo-local runtime artifacts do not define product-layer ontology.
