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
- direct_public_npx_available: true-for-registry-rc2-via-next
- direct_public_npx_primary_path: `aw-installer@next`
- registry_rc_available: true
- registry_rc_version_currently_observed: `next=0.4.0-rc.2`, `latest=0.4.0-rc.1`
- rc2_candidate_status: published-to-next-and-linux-registry-smoke-passed
- npm_publish_allowed: completed-for-approved-rc2-next-command-only
- package_name_decided: true
- approved_package_name: unscoped `aw-installer`
- external_trial_execution_started: false
- stable_trial_backend: `agents`
- claude_code_status: compatibility trial lane only
- remaining_docs_blockers: none known after this pass
- remaining_approval_blockers:
  - Windows PowerShell and macOS registry smoke before broad forum handoff
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
| [RC2 Approval Package](./aw-installer-rc2-approval-package.md) | rc2 release tuple, approval-lock expectation, local npx evidence, and publish boundary |
| [RC2 Release Notes](./aw-installer-rc2-release-notes.md) | changelog summary for the proposed rc2 candidate |
| [RC2 Rollback And Deprecation Plan](./aw-installer-rc2-rollback-deprecation-plan.md) | minimum repair path if rc2 publish or registry npx smoke fails |
| [Non-Publish Release Rehearsal](./aw-installer-release-rehearsal.md) | historical pack / dry-run / guard / smoke rehearsal before publish authorization |
| [Codex Usage Help](../usage-help/codex.md) | `agents` backend target-root and external trial safety guidance |
| [Claude Usage Help](../usage-help/claude.md) | Claude Code runtime compatibility lane and cold-start helper boundary |

## Non-contradiction Check

- Direct public `aw-installer@next` is available for the currently published `0.4.0-rc.2` registry package; post-publish registry npx smoke has verified the selector for local multi-target trial use on Linux generated targets.
- Bare `npx aw-installer` still follows npm `latest` and resolves to `0.4.0-rc.1`; do not use the bare selector when rc2 behavior is required.
- `aw-installer` is now the approved unscoped package identity; `P0-019` approved `aw-installer@0.4.0-rc.1`, and the later rc2 approval worktrack approved `aw-installer@0.4.0-rc.2` for the `next` channel.
- Codex with `agents` backend remains the primary trial path.
- Claude Code remains a compatibility trial lane and is not described as an implemented deploy adapter backend.
- Target writes are consistently scoped to the target repository `.agents/skills/` for `agents` install/update, or to the Claude project-level cold-start helper path for the Claude compatibility lane.
- Temporary target repository smoke writes only inside generated temporary workdirs or approved target repository temporary clones; push, PR, issue creation, non-temporary checkout mutation, stable/latest npm publish, and external trial execution remain out of scope.

## Blocker Classification

### Documentation Blockers

- N/A

No documentation blocker is known after the P0-013, P0-014, P0-015, and P0-016 verification passes.

### Approval Blockers

- Broad Windows PowerShell forum handoff should wait for real Windows registry smoke against `aw-installer@next`.
- External tester recruitment and real trial execution are not approved by this page.

### Technical Blockers

- N/A

Current docs governance checks and closeout gate passed in the worktrack that created this page. The later rc2 local npx prepublish pass proved the local package deployment path, and the post-publish Linux registry smoke proved `aw-installer@next` installs 19 managed skills on generated temporary targets.

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

The documentation set has been updated for the rc2 `aw-installer@next` registry npx path and feedback-log workflow. External-trial recruitment and broad Windows PowerShell forum handoff remain separate approval boundaries and must not be inferred from this verification record.
