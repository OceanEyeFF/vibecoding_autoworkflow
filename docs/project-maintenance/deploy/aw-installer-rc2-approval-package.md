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
- final_publish_git_commit: pending explicit approval-lock commit
- proposed_git_tag: `v0.4.0-rc.2`
- proposed_channel: `next`
- proposed_npm_dist_tag: `next`
- approval_package_status: evidence-complete-for-human-approval-review
- real_npm_publish_allowed_by_this_page: false
- stable_release_semantics_allowed: false
- forum_handoff_allowed_before_registry_rc2_smoke: false
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

`0.4.0-rc.2` is a replacement release-candidate for forum-facing installer trials. It does not change the package identity or stable channel. The current npm registry still resolves `aw-installer@next` to `0.4.0-rc.1` until this candidate is approved and published.

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
| final publish checkpoint | pending | must be the commit that opens the rc2 approval lock before `v0.4.0-rc.2` is created |
| current registry state | observed stale | `aw-installer@next` still points to `0.4.0-rc.1` |
| root package version | ready | `package.json` version is `0.4.0-rc.2` |
| root package approval lock | pending | approval fields are intentionally not opened yet |
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

Long-term documents keep this sanitized evidence summary. Raw transient logs and absolute `/tmp` paths should remain runtime evidence unless a later audit explicitly needs them.

## Approval Boundary

This page prepares the approval decision. It does not open the publish lock. Real publish remains blocked until a separate explicit approval updates the root package metadata to:

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
- acknowledgement that registry `next` remains `0.4.0-rc.1` until publish succeeds.
- acknowledgement that Windows PowerShell forum handoff waits for post-publish registry smoke.

## Expected Publish Flow After Approval

After approval only:

1. update the root `package.json` approval lock to the exact rc2 tuple.
2. commit the approval-lock change.
3. create `v0.4.0-rc.2` at the approved commit or create a GitHub Release with that tag.
4. publish through the GitHub Release workflow when Trusted Publishing is configured, or use the documented manual maintainer fallback.
5. rerun registry npx smoke and record the result before forum handoff.

## Wording Boundary

Allowed before publish:

- `rc2 candidate`
- `local package npx flow passed`
- `evidence complete for approval review`
- `expected release tuple`

Not allowed before publish:

- `rc2 is published`
- `registry next is rc2`
- `stable release`
- `latest is stable`
- `forum handoff is ready`
