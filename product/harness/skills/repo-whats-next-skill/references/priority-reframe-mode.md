# Repo Priority Reframe Mode Appendix

Use this appendix only when `repo-whats-next-skill` enters `priority reframe / contradiction analysis` mode. It is a bounded `RepoScope` deciding aid, not a separate skill.

## Trigger Matrix

Trigger this mode only when at least one of these conditions holds:

- the repo has multiple plausible next directions and no clear first move
- the current path feels busy but not decisive
- time, scope, or resources are clearly tighter than the stated goal
- a worktrack just closed or stalled and the repo-level priority may need to be reframed
- the repo may need to choose between `enter-worktrack`, `refresh-repo-state`, `goal-change-control`, or `hold-and-observe`

If none of those conditions holds, stay in the default `next-direction` mode instead of expanding into contradiction analysis.

## Minimum Input Contract

Collect only the minimum bounded repo packet:

- current repo goal or charter
- current repo snapshot or status
- current control-state view
- current time or delivery pressure if it materially changes the decision
- recent gate or worktrack evidence only if it changes the repo-level judgment

If a key input is missing, say so explicitly instead of filling it in by imagination.

## Compression Rules

- facts first; do not promote assumptions into facts
- only one current primary contradiction
- only one top priority now
- `Do Not Do` must remove distraction, not pad the answer
- if evidence is too weak, recommend `hold-and-observe` plus the minimum missing info
- if a real goal change is needed, route to `goal-change-control`
- if execution should start, recommend entering `WorktrackScope`; do not start execution here
- do not output a long strategic report

## Output Mapping Back To Main Decision Contract

When this mode is used, fold the result back into the normal `Repo Whats Next Decision` and make sure it sets:

- `mode: priority-reframe`
- `mode_trigger_reason`
- `facts`
- `inferences`
- `unknowns`
- `current_primary_contradiction`
- `primary_aspect`
- `top_priority_now`
- `do_not_do`
- `recommended_repo_action`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_scope`
- `approval_reason`
- `minimal_missing_info`
