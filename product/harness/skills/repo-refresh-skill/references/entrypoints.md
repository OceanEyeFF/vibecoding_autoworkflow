# Repo Refresh Skill Entrypoints

Load the Harness repo refresh docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/repo-scope.md`
- `docs/harness/artifact/repo/goal-charter.md`
- `docs/harness/artifact/repo/snapshot-status.md`
- `docs/harness/artifact/control/control-state.md`

## Read For Post-Closeout Refresh

- `docs/harness/artifact/worktrack/gate-evidence.md`

## Read If Repo Direction May Need A Separate Follow-Up

- `docs/harness/artifact/control/goal-change-request.md`

## Reading Policy

- This skill is for post-closeout repo refresh and verified writeback preparation, not for worktrack execution.
- Start from the current repo snapshot and the verified closeout evidence, then load only the additional repo-control context needed for this round.
- Package a bounded context packet for one `gpt-5.4-xhigh` `SubAgent`.
- Include only the context needed to refresh slow variables:
  - closed worktrack identity
  - baseline branch
  - accepted change summary
  - verification and gate results
  - repo artifacts that may require writeback
  - remaining risks or deferred items
- Do not fall back to full-repo scanning unless the closeout evidence shows that the repo baseline meaning itself has changed.
- Return a `Verified Writeback Handoff` for programmer review and approval instead of assuming writeback is already committed.
