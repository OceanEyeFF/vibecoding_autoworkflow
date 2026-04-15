# Repo Priority Reframe Mode

Use this note when `repo-whats-next-skill` needs a stronger repo-level priority judgment and the default "what's next" framing is still too loose.

This is a bounded `RepoScope` analysis mode, not a separate skill.

## Purpose

Use this mode to:

- separate facts from wishes
- identify the current primary contradiction at repo level
- identify the primary aspect of that contradiction
- decide the top repo priority now
- state what should not be done now
- surface the minimum missing info before the next repo decision

## When To Trigger This Mode

Trigger this mode only when at least one of these conditions holds:

- the repo has multiple plausible next directions and no clear first move
- the current path feels busy but not decisive
- time, scope, or resources are clearly tighter than the stated goal
- a worktrack just closed or stalled and the repo-level priority may need to be reframed
- the repo may need to choose between `enter-worktrack`, `refresh-repo-state`, `goal-change-control`, or `hold-and-observe`

Do not trigger this mode when the next move is already obvious from current evidence.

## Minimum Inputs

Collect only the minimum bounded repo packet:

- current repo goal or charter
- current repo snapshot or status
- current control-state view
- current time or delivery pressure if it materially changes the decision
- recent gate or worktrack evidence only if it changes the repo-level judgment

If a key input is missing, say so explicitly instead of filling it in by imagination.

## Required Output Shape

When this mode is used, fold the result back into the normal `Repo Whats Next Decision` and make sure it contains:

- `Facts`
- `Inferences`
- `Unknowns`
- `Current Primary Contradiction`
- `Primary Aspect`
- `Top Priority Now`
- `Do Not Do`
- `Recommended Repo Action`
- `Minimal Missing Info`

## Judgment Rules

- facts first; do not promote assumptions into facts
- only one current primary contradiction
- only one top priority now
- "do not do" must remove distraction, not pad the answer
- if evidence is too weak, recommend `hold-and-observe` plus the minimum missing info
- if a real goal change is needed, route to `goal-change-control`
- if execution should start, recommend entering `WorktrackScope`; do not start execution here

## Compression Rule

Do not output a long strategic report.

Keep the analysis compressed enough that `Harness` can review it in one round and decide whether to:

- approve the repo action
- request missing info
- switch scope
- hold the current layer
