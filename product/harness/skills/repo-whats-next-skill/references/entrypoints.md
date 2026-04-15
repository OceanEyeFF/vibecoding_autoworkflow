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

## Choose The Operating Mode

Default mode:

- use the normal bounded next-direction round when the first repo move is already reasonably clear from current evidence

`priority reframe / contradiction analysis` mode:

- trigger it when the repo has multiple plausible next directions and no decisive first move
- trigger it when the current path is busy but not decisive
- trigger it when time, scope, or resource pressure materially changes repo priorities
- trigger it after a recent worktrack closeout or stall if repo-level priority may need reframing

Mode boundary:

- this is a `RepoScope` analysis mode inside `repo-whats-next-skill`
- this is not a separate skill
- this is not a `WorktrackScope` skill
- treat `references/priority-reframe-mode.md` as a supporting note only; the canonical mode contract is now this file plus `../SKILL.md`

## Required Output Focus

Keep the result compressed. The returned `Repo Whats Next Decision` should center on:

- `Facts`
- `Inferences`
- `Unknowns`
- `Current Primary Contradiction`
- `Primary Aspect`
- `Top Priority Now`
- `Do Not Do`
- `Recommended Repo Action`
- `Minimal Missing Info`

## Reading Policy

- This skill is a `RepoScope` decision skill, not the top-level supervisor and not a worktrack executor.
- Package one bounded repo decision packet before asking a `gpt-5.4-xhigh` `SubAgent` to reason.
- Load only the minimum repo-side artifacts needed to choose the next evolution direction.
- Separate facts from inferences and unknowns instead of blending them into narrative summary.
- Keep exactly one current primary contradiction and exactly one top priority now when the contradiction-analysis mode is active.
- Map the final recommendation to exactly one repo action: `enter-worktrack`, `refresh-repo-state`, `goal-change-control`, or `hold-and-observe`.
- Use adjacent-system docs only when the repo decision truly depends on them.
- Return a recommendation and requested control-state change to `Harness`; do not mutate control state inside this skill.
- If evidence is too weak, prefer `hold-and-observe` plus the minimum missing info instead of speculative synthesis.
- Do not read repo-local deploy targets during canonical repo decision generation.
- Do not output a long strategic report; this is a bounded `RepoScope` review artifact.
