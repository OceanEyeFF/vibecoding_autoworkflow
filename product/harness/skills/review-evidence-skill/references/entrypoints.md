# Review Evidence Skill Entrypoints

Load the Harness review-evidence docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`
- `docs/harness/artifact/control/control-state.md`

## Read If The Review Round Needs Task Progress Or Queue Context

- `docs/harness/artifact/worktrack/plan-task-queue.md`

## Read If The Review Round Needs A Stronger Upstream Task Boundary

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read Only If The Review Round Explicitly Crosses Adjacent Systems

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a `WorktrackScope.verifying` review collector and synthesizer, not the supervisor, not the executor, and not the final `gate-skill`.
- The minimum packet for the `gpt-5.4-xhigh` `SubAgent` should include the bounded review target, `Worktrack Contract` summary, current change summary or diff reference, existing review inputs, acceptance reference, and known risks.
- Start from the current review target and `Gate Evidence` need; load only the additional context required to explain review findings and confidence.
- If canonical review inputs are sufficient, stop there; do not widen into broad repo reading or final adjudication logic.
- Use `Task Contract` only when the review question needs a stricter upstream execution boundary than the current `Worktrack Contract` already provides.
- Return one bounded `Gate Evidence Review Slice` for downstream synthesis instead of deciding the final worktrack gate outcome here.
