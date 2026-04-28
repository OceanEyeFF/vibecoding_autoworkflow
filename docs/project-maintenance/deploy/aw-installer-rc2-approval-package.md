---
title: "aw-installer RC2 Approval Package"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer RC2 Approval Package

> Purpose: assemble the `aw-installer@0.4.0-rc.2` release tuple and prepublish evidence for an explicit approval decision. This page does not by itself authorize stable/latest release semantics, future versions, npm Trusted Publisher setup changes, or external forum handoff.

This page belongs to [Deploy Runbooks](./README.md). It consumes [aw-installer Release Channel Contract](./release-channel-contract.md), [aw-installer Release Operation Model](./aw-installer-release-operation-model.md), [aw-installer RC2 npx Install Readiness](./aw-installer-rc2-npx-install-readiness.md), [aw-installer RC2 Release Notes](./aw-installer-rc2-release-notes.md), and [aw-installer RC2 Rollback And Deprecation Plan](./aw-installer-rc2-rollback-deprecation-plan.md).

## Control Signal

- candidate_version: `0.4.0-rc.2`
- implementation_checkpoint_before_approval_docs: `bf1910f85ce880db0574d2ad26cc8b961118de37`
- final_publish_git_commit: `9bf66998e89556db03686b8db0381d919eb32c59`
- proposed_git_tag: `v0.4.0-rc.2`
- proposed_channel: `next`
- proposed_npm_dist_tag: `next`
- approval_package_status: published-to-next
- real_npm_publish_allowed_by_this_page: completed-for-approved-rc2-tuple
- stable_release_semantics_allowed: false
- forum_handoff_allowed_before_registry_rc2_smoke: false; registry rc2 smoke now passed on Linux local generated targets
- expected_package_lock_if_approved: `realPublishApproval=approved`, `approvedVersion=0.4.0-rc.2`, `approvedGitTag=v0.4.0-rc.2`, `approvedChannel=next`

## Candidate Identity

| Field | Proposed value |
|---|---|
| approved package identity | unscoped `aw-installer` |
| version | `0.4.0-rc.2` |
| release channel | `next` |
| npm dist-tag | `next` |
| git tag | `v0.4.0-rc.2` |
| backend | `agents` |
| publish context | explicit approval worktrack, then CI release workflow or manual maintainer fallback |

`0.4.0-rc.2` is a replacement release-candidate for forum-facing installer trials. It does not change the package identity or stable channel. The npm registry now resolves `aw-installer@next` to `0.4.0-rc.2`; bare `aw-installer` still follows `latest` and resolves to `0.4.0-rc.1`.

## Delta From RC1

The rc2 candidate is scoped to installer reliability and payload freshness:

- adds cross-platform Python launcher fallback in both Node package wrappers:
  - Windows: `py -3`, then `python`, then `python3`
  - Linux/macOS: `python3`, then `python`
- keeps ignoring `PYTHON` and `PYTHON3` environment variable overrides by design.
- packages the current 19-skill `agents` payload, including `generic-worker-skill` and `doc-catch-up-worker-skill`.
- keeps the same package name, bins, backend contract, package provenance boundary, and `next` prerelease channel.

## Evidence Bundle

| Evidence | Status | Notes |
|---|---|---|
| implementation checkpoint before approval docs | passed | `develop-aw@bf1910f85ce880db0574d2ad26cc8b961118de37` |
| final publish checkpoint | passed | `develop-aw@9bf66998e89556db03686b8db0381d919eb32c59`; local tag `v0.4.0-rc.2` points to this commit |
| current registry state | passed | `aw-installer@next` points to `0.4.0-rc.2`; `latest` remains `0.4.0-rc.1` |
| root package version | ready | `package.json` version is `0.4.0-rc.2` |
| root package approval lock | approved | approval fields bind `0.4.0-rc.2`, `v0.4.0-rc.2`, and `next` |
| root `npm pack --dry-run --json` | passed | candidate tarball reports `aw-installer-0.4.0-rc.2.tgz` |
| root `npm run publish:dry-run --silent` | passed | dry-run package id is `aw-installer@0.4.0-rc.2` |
| release metadata derivation | passed | `v0.4.0-rc.2` maps to npm channel `next` |
| real publish guard negative check | passed | guard rejects because approval lock is still pending |
| deploy wrapper fallback tests | passed | Windows/Unix Python launcher fallback behavior covered |
| deploy regression suite | passed | 113 tests passed |
| governance pytest suite | passed | 185 tests passed |
| folder/path/semantic governance checks | passed | no governance blocker observed |
| local multi-temp package smoke | passed | three generated temporary targets installed 19 managed skills |
| explicit local `npx --package <local.tgz>` flow | passed | install/update/verify reached 19 managed installs |
| closeout acceptance gate | passed | `closeout-governance-task-list-20260402` returned passed |
| manual npm publish | passed | maintainer publish completed for `aw-installer@0.4.0-rc.2` on dist-tag `next` |
| post-publish registry npx smoke | passed | `aw-installer@next` installed 19 managed skills across three generated Linux targets |

Long-term documents keep this sanitized evidence summary. Raw transient logs and absolute `/tmp` paths should remain runtime evidence unless a later audit explicitly needs them.

## Approval Boundary

This page records the completed rc2 approval decision and publish result. The root package metadata is bound to:

```json
{
  "realPublishApproval": "approved",
  "approvedVersion": "0.4.0-rc.2",
  "approvedGitTag": "v0.4.0-rc.2",
  "approvedChannel": "next"
}
```

The approval applies only to this release tuple. Any later version, stable channel, npm dist-tag mutation, or Trusted Publisher configuration change requires a separate decision.

## Approval Request Shape

The human approval request for rc2 should include:

- candidate version: `0.4.0-rc.2`
- channel and npm dist-tag: `next`
- git tag: `v0.4.0-rc.2`
- release notes: [aw-installer RC2 Release Notes](./aw-installer-rc2-release-notes.md)
- rollback/deprecation plan: [aw-installer RC2 Rollback And Deprecation Plan](./aw-installer-rc2-rollback-deprecation-plan.md)
- confirmation that local package and explicit local npx deployment flows passed.
- acknowledgement that registry `next` now resolves to `0.4.0-rc.2` and `latest` remains `0.4.0-rc.1`.
- acknowledgement that broad Windows PowerShell forum handoff still needs real Windows registry smoke.

## Publish Flow Used

The completed flow was:

1. updated the root `package.json` approval lock to the exact rc2 tuple.
2. committed the approval-lock change.
3. merged the approval branch back to `develop-aw`.
4. created local tag `v0.4.0-rc.2` at `9bf66998e89556db03686b8db0381d919eb32c59`.
5. published manually to npm with dist-tag `next`.
6. reran registry npx smoke against `aw-installer@next`.

## Wording Boundary

Allowed after publish:

- `rc2 published to npm next`
- `aw-installer@next resolves to 0.4.0-rc.2`
- `post-publish Linux registry npx smoke passed`

Still not allowed:

- `stable release`
- `latest is stable`
- `bare npx aw-installer installs rc2`
