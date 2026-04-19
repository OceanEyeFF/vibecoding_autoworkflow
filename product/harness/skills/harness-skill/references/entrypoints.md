# Harness Skill Entrypoints

Load the Harness supervisor docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness指导思想.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/state-loop.md`
- `docs/harness/artifact/control/control-state.md`

## Read For RepoScope Rounds

- `docs/harness/scope/repo-scope.md`
- `docs/harness/artifact/repo/goal-charter.md`
- `docs/harness/artifact/repo/snapshot-status.md`
- `docs/harness/artifact/control/goal-change-request.md`

## Read For WorktrackScope Rounds

- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`

## Read Only If The Round Crosses Adjacent Systems

- `docs/harness/adjacent-systems/task-interface/task-contract.md`
- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is the supervisor layer, not the executor layer.
- Start from `Harness Control State`, then load only the artifacts required by the current scope.
- Treat `Harness指导思想` as doctrine and `Harness运行协议` as runtime behavior guidance.
- Concrete repo/worktrack content comes from the downstream scope skills and their artifacts, not from ad hoc supervisor invention.
- Default `RepoScope` continuation route: `repo-status-skill` -> `repo-whats-next-skill`.
- Default `WorktrackScope` continuation route: `init-worktrack-skill` -> `schedule-worktrack-skill` -> `dispatch-skills`.
- Do not let `dispatch-skills` run until `schedule-worktrack-skill` or an already-valid queue state has selected the current work item.
- Do not read repo-local deploy targets during Harness supervision.
- Continue across legal state transitions instead of stopping just because one bounded local round returned structured output.
- A `RepoScope` to `WorktrackScope` switch may continue without a fresh programmer handoff only when the current route has already marked that transition as continuation-ready and no formal stop condition requires approval.
- Stop and hand control back only when a formal stop condition is hit, including approval boundaries, missing or stale evidence, gate failure or block, runtime dispatch gaps, or contract-boundary violations.
