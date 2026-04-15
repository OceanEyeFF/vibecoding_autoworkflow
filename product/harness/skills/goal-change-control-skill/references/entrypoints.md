# Goal Change Control Skill Entrypoints

Load the Harness repo-level change-control docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness指导思想.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/repo-scope.md`
- `docs/harness/artifact/control/control-state.md`
- `docs/harness/artifact/control/goal-change-request.md`
- `docs/harness/artifact/repo/goal-charter.md`
- `docs/harness/artifact/repo/snapshot-status.md`

## Read If The Request Could Disrupt Active Worktracks

- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`

## Read Only If The Goal Change Round Crosses Adjacent Systems

- `docs/harness/adjacent-systems/task-interface/task-contract.md`
- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## SubAgent Context Policy

- Use exactly one bounded `gpt-5.4-xhigh` `SubAgent` for the impact-analysis round.
- Give the `SubAgent` a `Goal Change Brief` containing:
  - requested goal delta
  - change reason
  - explicit review question
  - authority boundary for this round
- Give the `SubAgent` a `Goal Impact Packet` containing only:
  - current `Repo Goal / Charter` summary
  - current `Repo Snapshot / Status` summary
  - active-worktrack impact summary, if relevant
  - known invariants and risks touched by the request
- Do not pass unrelated repo files, full worktrack history, or deploy-target state by default.

## Reading Policy

- This skill is a `RepoScope` change-control analyzer, not the supervisor and not the implementation executor.
- Start from the current `Goal Change Request`, then load only the artifacts needed to judge impact.
- Use worktrack artifacts only when the request could invalidate or redirect active work.
- Return a decision packet and approval request; do not mutate repo truth inside this skill.
- Do not read repo-local deploy targets during canonical skill execution.
