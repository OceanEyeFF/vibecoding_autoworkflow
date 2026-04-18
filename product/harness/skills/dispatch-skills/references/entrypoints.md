# Dispatch Skills Entrypoints

Load the Harness worktrack dispatch docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`
- `docs/harness/artifact/control/control-state.md`

## Read If This Round Depends On Existing Evidence

- `docs/harness/artifact/worktrack/gate-evidence.md`

## Read If Dispatch Needs A Stronger Execution Boundary

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If The Dispatch Round Crosses Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a worktrack dispatcher, not the supervisor and not the executor ontology itself.
- Start from the current work item, then load only the artifacts needed to package one bounded dispatch round.
- Use `Task Contract` only when the current dispatch round needs an upstream execution boundary; do not always pull it in by default.
- Keep the fallback execution carrier on the same bounded task/info contract as a specialized skill would receive.
- Report `runtime_dispatch_mode` explicitly so the result distinguishes delegated subagent dispatch from `current-carrier` runtime fallback.
- Do not imply that a delegated `SubAgent` path exists when the host runtime lacks a real dispatch shell.
- Do not read repo-local deploy targets during canonical dispatch generation.
