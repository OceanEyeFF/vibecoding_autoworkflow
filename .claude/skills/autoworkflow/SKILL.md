---
name: autoworkflow
description: >
  Use the repo-local `.autoworkflow` toolchain to enforce a deterministic test-green gate
  (plan -> review -> gate) and keep an auditable execution state.
allowed-tools: Read, Grep, Glob, Bash
---

# Autoworkflow (repo-local gate)

This skill standardizes how to run the repo-local workflow:

1) Ensure `.autoworkflow/` exists (init if missing)
2) Generate or set gate commands (auto-gate / set-gate)
3) Run `plan review` (default guard)
4) Run `gate` until green

Key artifacts (shared across hosts):
- `.autoworkflow/spec.md`
- `.autoworkflow/state.md`
- `.autoworkflow/gate.env`

Cross-platform entrypoints:
- Windows (PowerShell): `.autoworkflow/tools/aw.ps1`
- WSL/Linux (bash): `.autoworkflow/tools/aw.sh`

Notes:
- Treat `gate` as the single source of truth for “tests all green”.
- Prefer editing `.autoworkflow/gate.env` directly for complex shell quoting.
- Optional: `autoworkflow git branch start` can create a work branch when you are on `main/master`.

