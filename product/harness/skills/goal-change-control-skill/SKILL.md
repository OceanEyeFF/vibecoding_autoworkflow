---
name: goal-change-control-skill
description: Use this skill when Harness is in RepoScope and needs one bounded goal-level change-control round that analyzes impact, preserves authority boundaries, and returns a decision packet for programmer approval.
---

# Goal Change Control Skill

## Overview

Use this skill when `Harness` is in `RepoScope` and receives a goal-level change request.

This skill packages the request, gives one bounded analysis round to a single `gpt-5.4-xhigh` `SubAgent`, and returns a structured change-control report instead of directly mutating repo truth.

## When To Use

Use this skill when the current question is not "what should we implement next", but "should the repo goal change at all":

- a request would change `Repo Goal / Charter`, success criteria, or system invariants
- a request may invalidate the current repo baseline
- a request may force active `Worktrack` items to pause, split, re-scope, or rebuild
- a request needs explicit impact analysis before approval

Do not use this skill for ordinary task replanning, local implementation detail changes, or worktrack-level scope adjustments that do not alter repo goals.

## Workflow

1. Load the current `Goal Change Request` and the minimum `RepoScope` artifacts needed to interpret it.
2. Build one bounded `Goal Change Brief` and one `Goal Impact Packet` for a single `gpt-5.4-xhigh` `SubAgent`.
3. Ask that `SubAgent` to analyze:
   - what goal delta is being requested
   - which invariants, baselines, and active worktracks are affected
   - whether the request should be accepted, deferred, rejected, or redirected
4. Normalize the result into one fixed-format `Goal Change Control Report`; when useful, keep the request summary aligned with `templates/goal-change-request.template.md`.
5. Stop at the authority boundary and return the approval request to the programmer.

## Hard Constraints

- Do not rewrite `Repo Goal / Charter` directly from this skill.
- Do not approve or reject a goal-level change on behalf of the programmer.
- Do not silently rebuild baseline, close worktracks, or switch into `WorktrackScope`.
- Do not collapse goal impact, worktrack impact, and authority boundary into one vague narrative.
- Do not pass full-repo context to the `SubAgent` when a bounded impact packet is sufficient.
- Do not let the `SubAgent` redefine repo goals, acceptance criteria, or governance rules.
- Do not treat ambiguity as approval; surface unresolved questions explicitly.

## Expected Output

When you use this skill, produce a `Goal Change Control Report` with at least these sections:

- `Goal Change Request`
- `Impact Analysis`
- `Authority Boundary`
- `Recommended Decision`
- `Required Follow-up`

Inside the result, include at least these fields or equivalents:

- `requested_change`
- `change_reason`
- `goal_delta`
- `baseline_impact`
- `worktrack_impact`
- `invariants_at_risk`
- `evidence_or_gaps`
- `selected_subagent`
- `subagent_context`
- `recommended_decision`
- `approval_required`
- `approval_scope`
- `required_follow_up`

## Resources

Use the current `Goal Change Request`, the minimum `RepoScope` artifacts, and `templates/goal-change-request.template.md` when you need a stable request/decision draft shape for this round.
