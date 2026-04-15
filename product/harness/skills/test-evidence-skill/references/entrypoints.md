# Test Evidence Skill Entrypoints

Load the Harness validation-evidence docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`
- `docs/harness/artifact/control/control-state.md`

## Read If This Round Needs Queue Or Dispatch Context

- `docs/harness/artifact/worktrack/plan-task-queue.md`

## Read If Verification Requirements Need A Stronger Execution Contract

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If Validation Crosses Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a validation-evidence collector, not the supervisor, not the implementation executor, and not the final gate.
- Start from the current acceptance criteria and verification requirements, then load only the change summary and test surfaces needed for one bounded round.
- If you use a `gpt-5.4-xhigh` `SubAgent` as the reasoning carrier, pass only the `Test Evidence Task Brief` and `Test Evidence Info Packet` for this round instead of broad repo context.
- Reuse fresh evidence when it already satisfies the requirement; otherwise run or request the exact missing checks.
- Return explicit uncovered, failed, or blocked requirements instead of smoothing them into a generic summary.
- Do not read repo-local deploy targets during canonical validation-evidence generation.
