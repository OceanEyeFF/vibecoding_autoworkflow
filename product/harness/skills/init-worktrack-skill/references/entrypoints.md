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
- Creating the bounded worktrack branch is part of successful initialization, not an optional side path.
- Pull `Repo Snapshot / Status` only when the branch creation or baseline decision depends on current repo state; do not widen into repo-wide reading by default.
- Use `Task Contract` only when initialization inherits an upstream execution boundary; preserve that truth boundary instead of rewriting it.
- Build a minimal handoff packet for the next bounded round, specialized skill, or general execution carrier; the default next bounded round is `schedule-worktrack-skill`, not direct execution dispatch.
- This skill does not perform implementation, verification, or gate judgment itself, but if the next route is continuation-ready and no formal stop condition is hit, it should leave the worktrack ready for bounded continuation into `schedule-worktrack-skill` or `dispatch-skills`.
- Do not silently reuse an existing branch to satisfy initialization; if branch creation is unsafe or blocked, return that state explicitly.
- Only allow direct continuation into `dispatch-skills` when the active queue already contains one valid current next action and no extra scheduling judgment is needed.
- If the next route is blocked, approval-gated, or missing required runtime support, return that blocked state explicitly instead of pretending execution already started.
