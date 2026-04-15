# Init Worktrack Skill Entrypoints

Load the Harness worktrack-initialization docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/control/control-state.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`

## Read If Branch Or Baseline Must Be Chosen From Current Repo State

- `docs/harness/artifact/repo/snapshot-status.md`
- `docs/harness/artifact/repo/goal-charter.md`

## Read If Initialization Is Spawned From An Upstream Execution Boundary

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If This Initialization Round Crosses Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill initializes a bounded `Worktrack`; it does not execute the `Worktrack`.
- Start from the current control state and intended worktrack goal, then load only enough repo/worktrack context to make branch, baseline, contract, and initial plan explicit.
- Pull `Repo Snapshot / Status` only when the branch or baseline decision depends on current repo state; do not widen into repo-wide reading by default.
- Use `Task Contract` only when initialization inherits an upstream execution boundary; preserve that truth boundary instead of rewriting it.
- Build a minimal executor handoff packet for the next specialized skill or fallback `SubAgent`, but do not dispatch that executor from this skill.
- Stop once the `Worktrack` is ready for a later execution round.
