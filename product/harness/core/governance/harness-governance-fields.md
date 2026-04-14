# Harness Governance Fields

This file extracts the stable governance-bearing fields from the Harness contract shape.

## `gates`

Current stable gate slots:

- `scope_gate`
- `spec_gate`
- `static_gate`
- `test_gate`
- `smoke_gate`

These fields record per-gate verdict state for the active workflow contract.

## `risk_triage`

- `blocking_risks`
  - issues that must block completion or phase transition
- `rework_risks`
  - issues that do not block immediately but can invalidate delivery quality

## `governance`

Current stable dimensions:

- `rule`
- `folders`
- `document`
- `code`
- `overall`
- `improvement_suggestions`

These dimensions carry structured governance verdicts and recommendations for the current workflow outcome.

## `status`

- The extracted template currently initializes status as `planning`.
- Later lifecycle transitions belong to workflow/runtime handling and must remain compatible with the active Harness state model.
