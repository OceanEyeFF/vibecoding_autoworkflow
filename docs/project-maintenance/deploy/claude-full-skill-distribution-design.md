---
title: "Claude Full Skill Distribution Design"
status: draft
updated: 2026-05-01
owner: aw-kernel
last_verified: 2026-05-01
---
# Claude Full Skill Distribution Design

## Control Signal

- worktrack: `WT-20260501-claude-full-skill-distribution`
- backlog_item: `P0-036`
- design_status: implemented-in-current-worktrack
- previous_claude_payload: only `set-harness-goal-skill`
- distribution_shape: full current Harness skill set, with side-effecting skills protected for manual invocation
- target_dir_policy: Claude target dirs use `<skill-name>` without the `aw-` prefix; existing `aw-<skill-name>` dirs remain legacy managed dirs for migration cleanup
- implementation_status: implemented by `WT-CLAUDE-002` in the active worktrack
- release_allowed_by_this_doc: no

## Current State

The `agents` backend currently carries the full Harness skill set through `product/harness/adapters/agents/skills/`. The current skill inventory is:

- `close-worktrack-skill`
- `dispatch-skills`
- `doc-catch-up-worker-skill`
- `gate-skill`
- `generic-worker-skill`
- `harness-skill`
- `init-worktrack-skill`
- `recover-worktrack-skill`
- `repo-append-request-skill`
- `repo-change-goal-skill`
- `repo-refresh-skill`
- `repo-status-skill`
- `repo-whats-next-skill`
- `review-evidence-skill`
- `rule-check-skill`
- `schedule-worktrack-skill`
- `set-harness-goal-skill`
- `test-evidence-skill`
- `worktrack-status-skill`

Before this worktrack, the `claude` backend carried only:

- `set-harness-goal-skill`

The previous Claude target directory policy used `aw-set-harness-goal-skill`. That was acceptable for the compatibility lane, but it does not match the full Claude skill distribution shape, where project-level skills should be readable as `.claude/skills/<skill-name>/`.

## Proposed Payload Set

Claude should receive the full current Harness skill set, not only a startup subset.

Rationale:

- Harness control depends on the complete closed-loop skill family. Shipping only initialization leaves Claude users with a partial contract layer and no local path for observe, decide, dispatch, verify, judge, recover, close, or refresh.
- The skill source already separates control-plane semantics in `product/harness/skills/`; Claude distribution should adapt packaging and invocation safety, not redefine Harness truth.
- A subset would need a new policy for missing control functions. No such policy exists in the Goal Charter, and inventing one inside the adapter would create a second Harness model.

No current canonical Harness skill is excluded from the proposed payload set. If implementation discovers a Claude-specific incompatibility in a skill, the implementation task should either adapt packaging metadata for that skill or return to scheduling with a named exclusion and policy reason.

## Target Directory Policy

New Claude managed installs should target:

```text
.claude/skills/<skill-name>/
```

Examples:

- `.claude/skills/harness-skill/`
- `.claude/skills/repo-status-skill/`
- `.claude/skills/set-harness-goal-skill/`

The earlier `aw-<skill-name>` directory names should be treated as legacy managed target dirs for cleanup and drift detection:

```text
.claude/skills/aw-<skill-name>/
```

Implementation requirements:

- `target_dir` for new Claude payload descriptors should omit the `aw-` prefix.
- `legacy_target_dirs` should include the old `aw-<skill-name>` form where a previous Claude compatibility install may exist.
- `prune --all` and `update --yes` must only delete directories with recognizable current-backend managed markers.
- `check_paths_exist` must reject unrecognized or foreign content at planned current target dirs before writing.

## Side-Effecting Skill Protection

Claude packaging must distinguish passive guidance from workflows that can cause writes, branch changes, release operations, deployment, cleanup, or state transitions.

Policy:

- Side-effecting or state-transition skills must be manually invoked or otherwise protected from automatic model invocation.
- Where Claude skill metadata supports it, such skills should use `disable-model-invocation: true`.
- Read-only or explanatory skills may omit that protection only when the implementation task verifies that their workflow cannot mutate repo, runtime, remote, package, release, or branch state.

Skills that should be protected by default:

- `close-worktrack-skill`
- `dispatch-skills`
- `doc-catch-up-worker-skill`
- `gate-skill`
- `generic-worker-skill`
- `harness-skill`
- `init-worktrack-skill`
- `recover-worktrack-skill`
- `repo-append-request-skill`
- `repo-change-goal-skill`
- `repo-refresh-skill`
- `review-evidence-skill`
- `rule-check-skill`
- `schedule-worktrack-skill`
- `set-harness-goal-skill`
- `test-evidence-skill`
- `worktrack-status-skill`

`repo-status-skill` and `repo-whats-next-skill` are read/decision oriented, but they still participate in control routing. The verified implementation keeps the Claude full skill set conservative by applying `disable-model-invocation: true` to every Claude payload, including those two skills.

## Backend Metadata And Marker Treatment

Claude payloads should continue using backend payload descriptors under `product/harness/adapters/claude/skills/<skill>/payload.json`.

The deploy target remains runtime output, not source truth:

- canonical skill truth stays under `product/harness/skills/`
- Claude payload descriptors stay under `product/harness/adapters/claude/skills/`
- `.claude/skills/` remains a deploy target
- `payload.json` and `aw.marker` are runtime management artifacts, not user-authored Claude skill truth

Implementation should preserve the current managed-install safety model:

- source descriptors declare canonical paths and target dirs
- install copies only declared live payload files
- marker files identify current backend ownership and payload fingerprint
- verify detects missing files, drift, conflicts, unrecognized content, and foreign markers
- prune removes only recognized current-backend managed installs

`legacy_target_dirs` and `legacy_skill_ids` have separate migration meanings:

- `legacy_target_dirs` names old on-disk directories that may be removed when they carry a recognizable current-backend managed marker.
- `legacy_skill_ids` names old marker skill ids that should still be considered the same managed install during cleanup. It is only needed when a skill was renamed, so most payload descriptors intentionally omit it.

The Agents and Claude backends currently migrate in opposite directory-name directions. Agents payloads preserve the older no-prefix directory as legacy while installing into `aw-<skill-name>`; Claude payloads preserve the older `aw-<skill-name>` directory as legacy while installing into `<skill-name>`. Both directions use the same marker rule: only managed directories for the current backend are eligible for cleanup.

## Verification Matrix

The implementation phase should add or update focused coverage for:

- `adapter_deploy.py verify --backend claude`
- `aw-installer diagnose --backend claude --json`
- `aw-installer update --backend claude --json`
- `aw-installer install --backend claude`
- `aw-installer verify --backend claude`
- `aw-installer update --backend claude --yes`
- package-local `.tgz` smoke for Claude install and verify
- conflict handling for planned `.claude/skills/<skill-name>/` dirs
- legacy managed `aw-<skill-name>` cleanup behavior
- marker ownership and drift detection
- TUI path that presents Claude backend without implying stable/latest release support

General validation remains governed by the active worktrack contract:

- folder, path, and semantic governance checks
- deploy unittest discovery
- Node wrapper tests
- agents and Claude adapter verify
- package pack and publish dry-runs
- closeout acceptance gate before closeout

## Release Boundary

This design does not authorize a release.

Any future release-prep metadata update must first verify current registry facts and choose a new immutable version. `aw-installer@0.4.3-rc.0` is already published on `next`, so this worktrack must not attempt to publish that version again.

The following remain separately approval-gated:

- real npm publish
- npm dist-tag mutation
- GitHub Release publication
- tag push
- remote branch push
- GitHub PR creation or merge
- direct `master` mutation
- branch deletion

## Implementation Handoff

The next worktrack task may implement the approved design by:

- adding Claude payload descriptors for the full Harness skill set
- changing Claude `target_dir` values to no-prefix names with legacy `aw-` dirs retained for cleanup
- adding Claude-specific metadata or packaging treatment for side-effecting skills
- updating deploy adapter behavior only where required by target naming, marker safety, and verification
- adding focused tests for the verification matrix above
- updating Claude usage and deploy docs after implementation facts are verified

If implementation cannot satisfy the target naming or side-effecting protection policy without broad deploy redesign, it should return to scheduling rather than expanding scope silently.
