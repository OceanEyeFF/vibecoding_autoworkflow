---
name: repo-whats-next-skill
description: Use this skill when Harness is in RepoScope and needs one bounded decision round on the next evolution direction without mutating control state.
---

# Repo What's Next Skill

## Overview

Use this skill when `Harness` is already in `RepoScope` and needs one bounded judgment about the most appropriate next evolution direction for the repo.

This skill is a decision carrier for a `gpt-5.4-xhigh` `SubAgent`: it consumes a bounded repo context packet, evaluates the current repo baseline, and returns a recommendation to `Harness` without directly mutating `Harness Control State`.

## When To Use

Use this skill when the current question is not "who should execute a work item", but "what should the repo do next from `RepoScope`":

- decide whether the next direction should be:
  - enter a new `WorktrackScope`
  - refresh repo baseline or repo state
  - enter goal change control
  - hold in `RepoScope` until missing evidence is filled
- explain why that direction is the best current move
- surface the minimum prerequisites and bounded context for the next round
- return the recommendation to `Harness` and the programmer for approval

## Workflow

1. Read `references/entrypoints.md`.
2. Load the minimum repo artifacts and current control-state view needed for this decision round.
3. Build one `Repo Direction Brief` and one `Repo Direction Info Packet` for the current `gpt-5.4-xhigh` reasoning round.
4. Evaluate the allowed candidate directions:
   - `enter-worktrack`
   - `refresh-repo-state`
   - `goal-change-control`
   - `hold-and-observe`
5. Recommend exactly one next direction and explain why the other directions are not the best current move.
6. Stop at the recommendation boundary and return one fixed-format `Repo Whats Next Decision` to `Harness`.

## Hard Constraints

- Do not mutate `Harness Control State`.
- Do not start, schedule, or execute a `WorktrackScope` round directly from this skill.
- Do not rewrite repo goals inside this skill; route real goal changes to `goal change control`.
- Do not dump full-repo context into the reasoning round when a bounded info packet is sufficient.
- Do not collapse repo assessment, direction choice, and approval boundary into one vague narrative.
- Do not issue a gate verdict from this skill.
- Do not read repo-local deploy targets as truth sources.

## Expected Output

When you use this skill, produce a `Repo Whats Next Decision` with at least these sections:

- `Current Repo Assessment`
- `Repo Direction Brief`
- `Repo Direction Info Packet`
- `Candidate Directions`
- `Recommended Next Direction`
- `Why Not The Others`
- `Required Preconditions`
- `Return To Harness`

Inside the result, include at least these fields or equivalents:

- `current_repo_state`
- `decision_goal`
- `allowed_directions`
- `in_scope`
- `out_of_scope`
- `decision_constraints`
- `required_context`
- `known_risks`
- `recommended_direction`
- `recommended_next_scope`
- `selection_reason`
- `alternatives_considered`
- `missing_evidence`
- `required_preconditions`
- `control_state_change_requested`
- `needs_programmer_approval`
- `how_to_review`

## Resources

Read `references/entrypoints.md` first. It defines the minimum repo-side reading boundary for one bounded `RepoScope` decision round and tells you when to pull in goal-change, worktrack, or adjacent-system context.
