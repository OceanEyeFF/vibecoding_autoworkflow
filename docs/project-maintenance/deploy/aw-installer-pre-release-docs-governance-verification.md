---
title: "aw-installer Pre-release Docs Governance Verification"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Pre-release Docs Governance Verification

> Purpose: record the final documentation governance state before the first public or near-public `aw-installer` trial wave. This page does not authorize npm publish, recruit testers, or mutate external repositories.

This page belongs to [Deploy Runbooks](./README.md). It verifies the documentation state after the Harness dispatch/review-gate tuning, root README onboarding update, and external-trial docs alignment worktracks.

## Control Signal

- docs_governance_status: passed for pre-release trial documentation
- direct_public_npx_available: true-but-not-primary-until-registry-smoke
- registry_rc_available: true
- npm_publish_allowed: true-for-approved-P0-019-RC-command-only
- package_name_decided: true
- approved_package_name: unscoped `aw-installer`
- external_trial_execution_started: false
- stable_trial_backend: `agents`
- claude_code_status: compatibility trial lane only
- remaining_docs_blockers: none known after this pass
- remaining_approval_blockers:
  - registry npx smoke and docs primary-path flip
  - external tester recruitment / execution approval

## Verified Entry Points

| Entry point | Verified role |
|---|---|
| [Root README](../../../README.md) | public-facing repository entry; separates intended `npx` path, clean target directory initialization, and existing-work target repository initialization |
| [Deploy README](./README.md) | deploy runbook index; routes quickstart, feedback templates, multi-temp smoke, RC approval, rehearsal, and backend boundaries |
| [Public Quickstart Prompts](./aw-installer-public-quickstart-prompts.md) | copy-paste Codex main path and Claude Code compatibility path for pre-release `.tgz` trials |
| [External Trial Feedback Contract](./aw-installer-external-trial-feedback.md) | structured feedback fields and privacy boundary |
| [Trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) | GitHub issue entry for structured trial feedback |
| [Bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml) | GitHub issue entry for install, verify, update, initialization, or operator-confusion failures |
| [Multi Temporary Workdir Smoke](./aw-installer-multi-temp-workdir-smoke.md) | preferred pre-trial package smoke across isolated temporary targets and approved target repo temporary clones |
| [RC Approval Package](./aw-installer-rc-approval-package.md) | approved `0.4.x` release-candidate evidence and P0-019 publish command boundary |
| [Non-Publish Release Rehearsal](./aw-installer-release-rehearsal.md) | historical pack / dry-run / guard / smoke rehearsal before publish authorization |
| [Codex Usage Help](../usage-help/codex.md) | `agents` backend target-root and external trial safety guidance |
| [Claude Usage Help](../usage-help/claude.md) | Claude Code runtime compatibility lane and cold-start helper boundary |

## Non-contradiction Check

- Direct public `npx aw-installer` is technically available because `aw-installer@0.4.0-rc.1` is now the only published registry version; it is not yet the documentation primary path until P0-020 registry smoke passes.
- `aw-installer` is now the approved unscoped package identity; `P0-019` approved `aw-installer@0.4.0-rc.1` as the RC. Registry facts show both `next` and `latest` currently point at this same RC, so RC smoke/trial commands should prefer the explicit selector `aw-installer@next`.
- Codex with `agents` backend remains the primary trial path.
- Claude Code remains a compatibility trial lane and is not described as an implemented deploy adapter backend.
- Target writes are consistently scoped to the target repository `.agents/skills/` for `agents` install/update, or to the Claude project-level cold-start helper path for the Claude compatibility lane.
- Temporary target repository smoke writes only inside generated temporary workdirs or approved target repository temporary clones; push, PR, issue creation, non-temporary checkout mutation, stable/latest npm publish, and external trial execution remain out of scope.

## Blocker Classification

### Documentation Blockers

- N/A

No documentation blocker is known after the P0-013, P0-014, P0-015, and P0-016 verification passes.

### Approval Blockers

- Registry `npx aw-installer` smoke and public-docs primary-path flip remain in `P0-020`.
- External tester recruitment and real trial execution are not approved by this page.

### Technical Blockers

- N/A

Current docs governance checks and closeout gate passed in the worktrack that created this page.

## Verification Evidence

This page was created after the following worktracks completed:

- `WT-20260428-harness-dispatch-review-gate-tuning`
- `WT-20260428-root-readme-external-onboarding`
- `WT-20260428-external-trial-docs-alignment`

The P0-016 worktrack must preserve evidence for:

- SubAgent docs review.
- `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py`
- `git diff --check`
- `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json`

## Next Decision Boundary

The documentation set is ready for P0-020 registry smoke and public-docs primary-path verification. External-trial recruitment remains a separate approval boundary and must not be inferred from this verification record.
