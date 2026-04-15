# Close Worktrack Skill Entrypoints

Load the Harness closeout docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/scope/state-loop.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`
- `docs/harness/artifact/control/control-state.md`

## Read If Repo Refresh Handoff Needs Explicit Writeback Target Framing

- `docs/harness/artifact/repo/snapshot-status.md`

## Read If The Closeout Boundary Depends On Execution Contract Semantics

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Reading Policy

- This skill is for `WorktrackScope.integrating` closeout handling, not for fresh execution, gate adjudication, or repo-refresh execution.
- Start from the current `Gate Evidence` and closeout-status evidence, then load only the additional contract or control-state context needed for this round.
- Package a bounded context packet for one `gpt-5.4-xhigh` `SubAgent`.
- Include only the context needed to finish closeout safely:
  - current worktrack identity
  - baseline branch and current branch state
  - gate verdict and decisive evidence
  - PR or merge status
  - cleanup preconditions and pending approvals
  - accepted change summary
  - repo-refresh handoff prerequisites
- Do not assume `PR opened`, `merge detected`, or `diff landed` means the whole closeout loop is complete.
- Do not silently cross `merge`, `cleanup-branch`, or repo writeback authority boundaries; return them as explicit approval-bearing outcomes.
- Stop once the current closeout stage, pending approvals, and `Repo Refresh Handoff` are clear.
