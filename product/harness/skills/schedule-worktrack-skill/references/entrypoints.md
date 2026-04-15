# Schedule Worktrack Skill Entrypoints

Load the Harness worktrack scheduling docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`
- `docs/harness/artifact/control/control-state.md`

## Read If This Round Depends On Existing Evidence

- `docs/harness/artifact/worktrack/gate-evidence.md`

## Read If Scheduling Needs A Stronger Task Boundary

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If The Scheduling Round Crosses Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a worktrack scheduler, not the supervisor and not the downstream executor.
- Start from the current queue snapshot and evidence delta, then load only the artifacts needed to refresh one bounded round.
- If you use a `gpt-5.4-xhigh` `SubAgent` as the reasoning carrier, pass only the bounded scheduling packet for this round instead of broad repo context.
- Return one selected `current next action` or an explicit blocked result; do not dispatch implementation from here.
- Do not read repo-local deploy targets during canonical scheduling generation.
