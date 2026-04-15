---
name: repo-status-skill
description: Use this skill when Harness is in RepoScope and needs a dedicated gpt-5.4-xhigh SubAgent to summarize current repo baseline status without turning that round into planning or execution.
---

# Repo Status Skill

## Overview

Use this skill as the specialized `RepoScope` status observer in `Codex`.

It runs one bounded repo-status round with a dedicated `gpt-5.4-xhigh` `SubAgent`, reads the minimum canonical artifacts for the current question, and returns a structured repo status summary to `Harness`.

## When To Use

Use this skill when the current question is not "what should we do next", but "what is the repo baseline state right now":

- summarize current mainline status for `RepoScope`
- surface active branches, governance signals, and known risks
- refresh the status basis before `repo-whats-next-skill` or `goal-change-control-skill`
- provide a bounded repo-status context packet instead of broad repo exploration

## Workflow

1. Read `references/entrypoints.md`.
2. Confirm this is a `RepoScope` status-observation round, not worktrack dispatch, next-step decision, or direct execution.
3. Load `Harness Control State`, `Repo Snapshot / Status`, and only the minimum additional artifacts required by the current question.
4. If the canonical snapshot is missing, stale, or clearly insufficient, collect only the smallest sensor evidence needed to explain the gap.
5. Summarize current repo baseline state, active branches, governance and freshness signals, and known risks.
6. Stop after one bounded status round and return one fixed-format `Repo Status Summary` to `Harness`.

## Hard Constraints

- Do not create, mutate, or schedule a `Worktrack`.
- Do not choose the next repo action; return handoff signals for supervisor judgment instead.
- Do not widen into implementation planning, code editing, or execution dispatch.
- Do not treat repo-local execution templates or deploy targets as truth artifacts.
- Do not read the whole repository when canonical artifacts and bounded sensor checks are sufficient.
- Do not collapse stale inputs, observed evidence, and inferred status into one vague paragraph.

## Expected Output

When you use this skill, produce a `Repo Status Summary` with at least these sections:

- `RepoScope Status`
- `Current Baseline`
- `Active Branches And Surfaces`
- `Governance And Freshness Signals`
- `Known Risks And Unknowns`
- `Handoff To Harness`

Inside the result, include at least these fields or equivalents:

- `current_scope`
- `control_state`
- `snapshot_basis`
- `goal_reference_used`
- `mainline_status`
- `active_branches`
- `governance_signals`
- `known_risks`
- `stale_or_missing_inputs`
- `bounded_sensor_checks`
- `handoff_signals`
- `needs_supervisor_decision`

## Resources

Read `references/entrypoints.md` first. It defines the minimum reading boundary for one `RepoScope` status round and the minimum context packet that should be handed to the `gpt-5.4-xhigh` `SubAgent`.
