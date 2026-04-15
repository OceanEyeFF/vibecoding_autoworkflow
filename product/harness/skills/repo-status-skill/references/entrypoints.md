# Repo Status Skill Entrypoints

Load the `RepoScope` status docs in this order.

## Always Read First

- `docs/project-maintenance/foundations/root-directory-layering.md`
- `docs/harness/foundations/Harness运行协议.md`
- `docs/harness/scope/repo-scope.md`
- `docs/harness/artifact/repo/snapshot-status.md`
- `docs/harness/artifact/control/control-state.md`

## Read If This Summary Needs Baseline Intent

- `docs/harness/artifact/repo/goal-charter.md`

## Read If This Round Must Explain Goal Drift Or Pending Change Control

- `docs/harness/artifact/control/goal-change-request.md`

## Read Only If The Repo Status Question Explicitly Depends On Adjacent Systems

- `docs/harness/adjacent-systems/task-interface/task-contract.md`
- `docs/harness/adjacent-systems/memory-side/overview.md`
- `docs/harness/adjacent-systems/memory-side/skill-agent-model.md`

## Reading Policy

- This skill is a `RepoScope` observer, not the supervisor, not `repo-whats-next-skill`, and not a coding executor.
- The minimum context packet for the `gpt-5.4-xhigh` `SubAgent` should include the current repo-status question, current control-state facts, the `Repo Snapshot / Status` source, the baseline branch if known, and any known freshness concern.
- Start from `Repo Snapshot / Status`; use `Repo Goal / Charter` only when the summary must anchor current status against repo invariants or direction.
- If canonical artifacts are fresh and sufficient, stop there; do not fan out into broad repo reading.
- If artifacts are stale or missing, collect only bounded sensor evidence needed to state that fact and explain its impact on summary confidence.
- Do not load `WorktrackScope` or adjacent-system material unless the current repo-status question explicitly requires it.
