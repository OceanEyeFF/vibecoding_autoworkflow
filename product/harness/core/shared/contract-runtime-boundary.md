# Contract vs Runtime Boundary

This file extracts the stable `contract` vs `runtime` split from the legacy Harness composite source.

## Stable rules

- `contract` is stable execution policy and validation boundary.
- `runtime` is per-run mutable state and ephemeral context.
- Canonical skill source must not persist runtime state back into source files.
- Runtime-only values belong to repo-local state, not to canonical product source.

## Current runtime split

- `contract.*`
  - workflow policy
  - gate sequence
  - governance dimensions
  - path boundaries
- `runtime.*`
  - workflow id
  - task reference
  - active state file
  - current contract file
  - timestamps

## Current runtime container

- Default runtime binding file: `.autoworkflow/harness.yaml`

This extracted file is canonical for the shared boundary definition.
Legacy deploy-source composites may repeat or embed the same rules during transition.
