# Repo What's Next Skill Entrypoints

Load the Harness repo-decision docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness指导思想.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/repo-scope.md`
- `docs/harness/artifact/repo/goal-charter.md`
- `docs/harness/artifact/repo/snapshot-status.md`
- `docs/harness/artifact/control/control-state.md`

## Read If The Current Repo Decision Depends On A Pending Goal Shift

- `docs/harness/artifact/control/goal-change-request.md`

## Read If The Repo Decision Depends On Recent Worktrack Evidence

- `docs/harness/artifact/worktrack/gate-evidence.md`
- `docs/harness/artifact/worktrack/plan-task-queue.md`

## Read Only If This Repo Decision Truly Crosses Adjacent Systems

- `docs/harness/adjacent-systems/task-interface/task-contract.md`
- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/layer-boundary.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a `RepoScope` decision skill, not the top-level supervisor and not a worktrack executor.
- Package a bounded `Repo Direction Brief` and `Repo Direction Info Packet` before asking a `gpt-5.4-xhigh` `SubAgent` to reason.
- Load only the minimum repo-side artifacts needed to choose the next evolution direction.
- Use adjacent-system docs only when the repo decision truly depends on them.
- Return a recommendation and requested control-state change to `Harness`; do not mutate control state inside this skill.
- Do not read repo-local deploy targets during canonical repo decision generation.
