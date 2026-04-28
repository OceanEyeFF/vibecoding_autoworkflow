---
title: "aw-installer RC2 Rollback And Deprecation Plan"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer RC2 Rollback And Deprecation Plan

> Purpose: define the minimum response plan if `aw-installer@0.4.0-rc.2` is published incorrectly or fails post-publish registry npx validation. This page does not implement automatic rollback and does not authorize npm publish.

This page belongs to [Deploy Runbooks](./README.md). It supports [aw-installer RC2 Approval Package](./aw-installer-rc2-approval-package.md) and follows [aw-installer Release Candidate Prep](./aw-installer-release-candidate-prep.md).

## Control Signal

- candidate_version: `0.4.0-rc.2`
- release_channel: `next`
- rollback_plan_status: ready-for-approval-review
- automatic_rollback_available: false
- stable_release_semantics_allowed: false
- primary_repair_mechanisms: npm dist-tag correction, npm deprecation, replacement RC worktrack

## Response Matrix

| Failure after publish | Minimum response |
|---|---|
| `next` points to the wrong version | Correct the npm dist-tag to the approved version or back to the last known working RC, record the command and registry result, then rerun registry npx smoke. |
| `latest` appears to imply stable semantics | Record it as an npm registry default/alias fact only, keep public instructions pinned to `aw-installer@next` where clarity matters, and avoid stable wording. |
| package tarball misses expected files or skills | Stop recommending rc2, deprecate `0.4.0-rc.2` with a clear message, and open a replacement RC worktrack. |
| Windows PowerShell launcher still fails | Preserve the sanitized feedback log, stop forum handoff, deprecate rc2 if the published package is broadly unusable, and open a focused wrapper bugfix worktrack. |
| Linux/macOS `npx` install/update/verify fails | Preserve smoke evidence, stop recommending rc2, and either correct docs if operator instructions were wrong or prepare a replacement RC. |
| target repo receives writes outside `.agents/skills/` | Treat as a hard blocker, stop recommending rc2, preserve logs, and open a security/scope bugfix worktrack before any replacement publish. |
| registry package installs fewer or more than 19 managed skills unexpectedly | Stop handoff, compare package payload to `product/harness/adapters/agents/skills`, and prepare a replacement RC if the registry tarball is wrong. |
| release notes or quickstart contradict registry facts | Patch docs, rerun governance checks, and do not restart external handoff until docs and registry smoke agree. |
| Trusted Publishing authentication fails | Do not mutate package version or dist-tags. Use the manual maintainer fallback only if the same rc2 tuple has explicit approval and local guard checks pass. |

## npm Actions

Allowed repair actions after a failed publish must stay scoped to the approved package and candidate line:

- inspect registry state with `npm view aw-installer version dist-tags --json`.
- adjust `next` only when the observed dist-tag contradicts the approved tuple.
- deprecate the broken rc2 version with a precise message if the package is already published and should not be used.
- publish a replacement only through a new approval tuple, such as `0.4.0-rc.3`.

Do not delete registry history as a primary repair path. npm package versions are immutable once published.

## Communication Boundary

Before post-publish registry smoke passes, operator-facing docs may say:

- `rc2 was published but is under smoke verification`
- `use rc1 or pause until rc2 verification is restored`
- `forum handoff is paused`

They must not say:

- `stable release`
- `automatic rollback`
- `self-update will repair it`
- `latest is stable`

## Post-publish Recovery Evidence

Any recovery action must record:

- observed npm dist-tags before and after the action.
- affected version.
- exact command class used, without tokens or credential details.
- sanitized smoke or feedback evidence.
- whether the public quickstart should pin `aw-installer@next`, avoid bare `npx aw-installer`, or pause external trial instructions.
