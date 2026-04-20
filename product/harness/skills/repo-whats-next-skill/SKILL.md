---
name: repo-whats-next-skill
description: Use this skill when Harness is in RepoScope and needs one bounded next-direction round, including a lightweight priority reframe / contradiction analysis mode, without mutating control state.
---

# Repo What's Next Skill

## Overview

Use this skill when `Harness` is already in `RepoScope` and needs one bounded judgment about the most appropriate next evolution direction for the repo.

This skill is a decision carrier for a `gpt-5.4-xhigh` `SubAgent`: it consumes a bounded repo context packet, evaluates the current repo baseline, and returns a recommendation to `Harness` without directly mutating `Harness Control State`.

This skill has one default decision path and one embedded `priority reframe / contradiction analysis` mode. That mode is part of this `RepoScope` skill. It is not a separate skill, not a `WorktrackScope` skill, and not a license to produce a long strategic report.

This document is a canonical executable skeleton. It defines the bounded operating shape and output contract for the mode, but it does not claim that a fully automated planner or supervisor implementation already exists.

## When To Use

Use this skill when the current question is not "who should execute a work item", but "what should the repo do next from `RepoScope`":

- decide whether the next direction should be:
  - enter a new `WorktrackScope`
  - refresh repo baseline or repo state
  - enter goal change control
  - hold in `RepoScope` until missing evidence is filled
- explain why that direction is the best current move
- reframe repo priority when there are multiple plausible directions but no decisive first move
- surface the minimum prerequisites and bounded context for the next round
- return the recommendation to `Harness`; only surface programmer approval when the selected route actually crosses a formal approval boundary

Use the embedded `priority reframe / contradiction analysis` mode when at least one of these conditions holds:

- the repo has multiple plausible next directions and no clear first move
- the current path looks busy but not decisive
- time, scope, or resources are materially tighter than the stated goal
- a `WorktrackScope` round just closed or stalled and repo-level priority may need reframing

Do not use this skill as a substitute for worktrack planning or execution dispatch. This remains a `RepoScope` judgment round.

## Workflow

1. Confirm this is a `RepoScope` decision round, not a `WorktrackScope` planning or execution round.
2. Load the minimum repo artifacts and current control-state view needed for this decision round.
3. Choose the operating mode:
   - default `next-direction` mode
   - `priority reframe / contradiction analysis` mode
4. Build one bounded repo decision packet for the current `gpt-5.4-xhigh` reasoning round.
5. Evaluate the allowed candidate repo actions:
   - `enter-worktrack`
   - `refresh-repo-state`
   - `goal-change-control`
   - `hold-and-observe`
6. Recommend exactly one repo action, explain why it is the top priority now, and state what should not be done now.
7. Return one fixed-format `Repo Whats Next Decision` to `Harness`.
8. If the selected route is already approved and no formal stop condition is hit, allow the supervisor to continue directly into the corresponding next scope.

## Priority Reframe / Contradiction Analysis Mode

When this mode is active, compress the round to one bounded repo-level contradiction judgment:

- separate `Facts`, `Inferences`, and `Unknowns`
- identify exactly one `Current Primary Contradiction`
- identify the current `Primary Aspect` of that contradiction
- name exactly one `Top Priority Now`
- state a short `Do Not Do` list that removes distraction instead of padding the answer
- map that priority to exactly one `Recommended Repo Action`
- surface only the `Minimal Missing Info` needed for the next repo decision

If evidence is too weak to support a decisive repo action, recommend `hold-and-observe` plus the minimum missing info. If the contradiction can only be resolved by changing repo goals, route to `goal-change-control`. If the contradiction is ready for execution, recommend entering `WorktrackScope`; when the next route is already approved and safe, supervisor continuation may proceed without an extra programmer handoff.

## Hard Constraints

- Do not mutate `Harness Control State`.
- Do not start, schedule, or execute a `WorktrackScope` round directly from this skill.
- Do not rewrite repo goals inside this skill; route real goal changes to `goal change control`.
- Do not treat "one bounded repo judgment" as an instruction that the whole Harness loop must stop.
- Do not dump full-repo context into the reasoning round when a bounded info packet is sufficient.
- Do not treat the embedded contradiction analysis mode as a separate skill or a new layer in the skill tree.
- Do not collapse facts, inferences, unknowns, and recommended action into one vague narrative.
- Do not issue a gate verdict from this skill.
- Do not read repo-local deploy targets as truth sources.
- Do not output a large strategic report; keep the result reviewable in one `RepoScope` round.

## Expected Output

When you use this skill, produce a `Repo Whats Next Decision` with at least these sections:

- `Mode`
- `Facts`
- `Inferences`
- `Unknowns`
- `Current Primary Contradiction`
- `Primary Aspect`
- `Top Priority Now`
- `Do Not Do`
- `Recommended Repo Action`
- `Minimal Missing Info`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `mode`
- `facts`
- `inferences`
- `unknowns`
- `current_primary_contradiction`
- `primary_aspect`
- `top_priority_now`
- `do_not_do`
- `recommended_repo_action`
- `recommended_next_scope`
- `allowed_repo_actions`
- `in_scope`
- `out_of_scope`
- `decision_constraints`
- `selection_basis`
- `selection_reason`
- `minimal_missing_info`
- `control_state_change_requested`
- `continuation_ready`
- `needs_programmer_approval`
- `how_to_review`

If the default mode is enough and no full contradiction reframe is needed, keep the contradiction-related sections brief instead of expanding them into a report. The output is still expected to stay bounded and decision-oriented.

## Resources

Use the current `Harness Control State`, the repo-side `.aw/` artifacts, and, when needed, `references/priority-reframe-mode.md` as the bounded reference for contradiction analysis.
