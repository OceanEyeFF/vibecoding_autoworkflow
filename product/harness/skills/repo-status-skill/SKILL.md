---
name: repo-status-skill
description: Use this skill when Harness is in RepoScope and needs one bounded status-observation round, optionally carried by a dedicated gpt-5.4-xhigh SubAgent when the host runtime supports that carrier.
---

# Repo Status Skill

## Overview

Use this skill as the specialized `RepoScope` status observer in `Codex`.

It realizes one bounded `RepoScope.observing` round, reads the minimum canonical artifacts for the current question, and returns a structured repo status summary plus one observation handoff to `Harness`.

## When To Use

Use this skill when the current question is not "what should we do next", but "what is the repo baseline state right now":

- summarize current mainline status for `RepoScope`
- surface active branches, governance signals, and known risks
- refresh the status basis before `repo-whats-next-skill` or `goal-change-control-skill`
- provide a bounded repo-status context packet instead of broad repo exploration

## Workflow

1. Confirm this is a `RepoScope` status-observation round, not worktrack dispatch, next-step decision, or direct execution.
2. Load `Harness Control State`, `Repo Snapshot / Status`, and only the minimum additional artifacts required by the current question.
3. If the canonical snapshot is missing, stale, or clearly insufficient, collect only the smallest sensor evidence needed to explain the gap.
4. Summarize current repo baseline state, active branches, governance and freshness signals, and known risks.
5. Decide whether the current observation basis is sufficient to enter the next bounded repo judgment round, and record that readiness explicitly.
6. Return one fixed-format `Repo Status Summary` to `Harness`.
7. If no formal stop condition is hit, allow the supervisor to continue directly into the next legal repo-level judgment.

## Formal Stop Conditions

Stop and return control when at least one of these conditions is true:

- the observation basis is missing, stale, or contradictory enough that `RepoScope.deciding` would be guessing
- collecting the next sensor signal would widen into full-repo rediscovery instead of one bounded observation round
- the next required probe would cross a read-only or authority boundary that needs explicit approval

## Hard Constraints

- Do not create, mutate, or schedule a `Worktrack`.
- Do not choose the next repo action; return handoff signals for supervisor judgment instead.
- Do not treat this observing round as a repo-deciding round; it may recommend the next route, but it must not choose the next repo action itself.
- Do not widen into implementation planning, code editing, or execution dispatch.
- Do not claim that a dedicated `SubAgent` was used unless the host runtime actually delegated the round.
- Do not treat repo-local execution templates or deploy targets as truth artifacts.
- Do not read the whole repository when canonical artifacts and bounded sensor checks are sufficient.
- Do not collapse stale inputs, observed evidence, and inferred status into one vague paragraph.

## Expected Output

When you use this skill, produce a `Repo Status Summary` with at least these sections:

- `RepoScope Status`
- `Current Baseline`
- `Active Branches And Surfaces`
- `Governance And Freshness Signals`
- `Observation Readiness`
- `Route Handoff`
- `Known Risks And Unknowns`
- `Handoff To Harness`

Inside the result, include at least these fields or equivalents:

- `current_scope`
- `current_phase`
- `control_state`
- `observation_status`
- `snapshot_basis`
- `snapshot_freshness`
- `goal_reference_used`
- `mainline_status`
- `active_branches`
- `governance_signals`
- `known_risks`
- `stale_or_missing_inputs`
- `bounded_sensor_checks`
- `repo_judgment_ready`
- `allowed_next_routes`
- `recommended_next_route`
- `continuation_ready`
- `continuation_blockers`
- `approval_required`
- `approval_reason`
- `handoff_signals`
- `needs_supervisor_decision`

## Resources

Use the current `Harness Control State`, the repo snapshot artifacts, and the smallest bounded sensor evidence needed for this observing round. The result should stay narrow enough to hand off into repo judgment, not expand into repo planning.
