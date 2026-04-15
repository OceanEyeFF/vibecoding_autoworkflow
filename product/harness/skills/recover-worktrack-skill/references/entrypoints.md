# Recover Worktrack Skill Entrypoints

Load the Harness worktrack recovery docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/worktrack-scope.md`
- `docs/harness/artifact/worktrack/contract.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`
- `docs/harness/artifact/worktrack/gate-evidence.md`
- `docs/harness/artifact/control/control-state.md`

## Read If Recovery Needs A Stronger Upstream Task Boundary

- `docs/harness/adjacent-systems/task-interface/task-contract.md`

## Read If `refresh-baseline` Becomes A Real Candidate

- `docs/harness/scope/repo-scope.md`
- `docs/harness/artifact/repo/snapshot-status.md`
- `docs/harness/artifact/repo/goal-charter.md`

## Read Only If Adjacent-System Drift Is The Recovery Trigger

- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a `WorktrackScope.recovering` recovery chooser, not the supervisor, not the executor, and not the closeout path.
- The minimum packet for the `gpt-5.4-xhigh` `SubAgent` should include the bounded recovery trigger, `Worktrack Contract` summary, current plan and blocker state, current `Gate Evidence` summary, baseline status, known constraints, and available authority limits.
- Start from the present failure classification and choose among `retry`, `rollback`, `split-worktrack`, or `refresh-baseline`; do not widen into broad repo rediscovery unless `refresh-baseline` is a real candidate.
- `retry` must remain inside the same approved worktrack goal, non-goals, and baseline expectations.
- `rollback` may identify a rollback target or safe rollback rule, but must stop before destructive mutation without programmer approval.
- `split-worktrack` may propose new bounded follow-up worktracks, but must not silently create or switch to them.
- `refresh-baseline` may request a repo-facing refresh round, but must not rewrite repo truth artifacts from this skill.
- Do not read repo-local deploy targets during canonical recovery generation.
