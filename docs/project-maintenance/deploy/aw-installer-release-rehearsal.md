---
title: "aw-installer Non-Publish Release Rehearsal"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Non-Publish Release Rehearsal

> Purpose: record the reproducible release rehearsal path for `aw-installer` up to, but not including, real `npm publish`.

This page belongs to [Deploy Runbooks](./README.md). It validates the rehearsal path for the `0.4.x` candidate described in [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md). It does not authorize or run real `npm publish`.

## Control Signal

- rehearsal_status: passed
- candidate_version_proposal: `0.4.0-rc.1`
- rehearsal_package_version: `0.0.0-local`
- current_preflight_package_version: `0.4.0-rc.1`
- release_channel_under_review: `next`
- npm_dist_tag_under_review: `next`
- proposed_git_tag: `v0.4.0-rc.1`
- real_npm_publish_allowed: false
- publish_approval_status: pending
- technical_blockers: none found in this rehearsal
- approval_blockers: real publish still requires a separate explicit approval boundary

## Rehearsal Matrix

| Check | Command shape | Result | Meaning |
|---|---|---|---|
| Pack local package | `npm pack --json --pack-destination <tmpdir>` | passed | historical local package envelope produced `aw-installer-0.0.0-local.tgz` |
| Publish dry-run | `npm run publish:dry-run --silent` | passed | npm dry-run and `prepublishOnly` dry-run path remain reproducible |
| Real publish guard | `node toolchain/scripts/deploy/bin/check-root-publish.js` | rejected as expected | real publish remains blocked without explicit approval, CI, channel, dist-tag, and git-tag inputs |
| Candidate channel derivation | `deriveReleaseChannelFromTag('v0.4.0-rc.1', '0.4.0-rc.1', 'rc.1')` | `next` | proposed candidate tag/version shape maps to the intended channel |
| Two-target tarball smoke | local `.tgz` through `npm exec --package` in two temporary target repos | passed | packaged CLI/TUI guard/install/verify/update path is reproducible without source checkout reliance |

## Rehearsal Evidence

| Evidence | Value |
|---|---|
| package file | `aw-installer-0.0.0-local.tgz` |
| package identity | `aw-installer@0.0.0-local` |
| pack result | passed |
| publish dry-run result | passed |
| real publish guard result | expected rejection: `refusing to publish aw-installer 0.0.0-local; choose an approved non-local version first` |
| candidate channel derivation result | `next` |
| two-target smoke result | passed |
| smoke evidence directory | `/tmp/tmp.t5llF11DCF` |
| smoke package path | `/tmp/tmp.t5llF11DCF/aw-installer-0.0.0-local.tgz` |

The smoke evidence directory is a runtime path from this rehearsal. If a future release approval needs retained raw logs, rerun the rehearsal and store the resulting evidence bundle in the approved release artifact location.

## Two-Target Smoke Summary

| Target | help | version | tui guard | diagnose before | update dry-run | install | verify | update --yes | diagnose after |
|---|---|---|---|---|---|---|---|---|---|
| target-alpha | passed | passed | passed | passed | passed | passed | passed | passed | passed |
| target-beta | passed | passed | passed | passed | passed | passed | passed | passed | passed |

Both targets finished with:

- `issue_count: 0`
- `managed_install_count: 17`
- `conflict_count: 0`
- `unrecognized_count: 0`

## Technical Blockers

- N/A

No technical blocker was found for the non-publish rehearsal path. This page preserves historical `0.0.0-local` rehearsal evidence; after the release-preflight metadata is set to `0.4.0-rc.1`, the active worktrack must refresh pack and publish dry-run evidence before any publish approval request.

## Approval Blockers

- real npm publish requires separate explicit approval.
- candidate checkpoint metadata must be prepared in the release context before any actual publish attempt.
- `AW_INSTALLER_PUBLISH_APPROVED=1` must not be set by this rehearsal.
- npm dist-tag must be explicitly set to `next` for the proposed candidate.
- `AW_INSTALLER_RELEASE_GIT_TAG` must match `v0.4.0-rc.1` for the proposed candidate.

## Rehearsal Procedure

Use this as the minimal non-publish rehearsal shape:

```bash
npm pack --json --pack-destination "$tmpdir"
npm run publish:dry-run --silent
node toolchain/scripts/deploy/bin/check-root-publish.js
node -e "const {deriveReleaseChannelFromTag}=require('./toolchain/scripts/deploy/bin/check-root-publish.js'); const channel=deriveReleaseChannelFromTag('v0.4.0-rc.1','0.4.0-rc.1','rc.1'); if (channel !== 'next') process.exit(1);"
```

The direct guard command is expected to fail until real publish approval, CI context, channel, dist-tag, and matching release tag inputs are supplied. Treat that failure as a pass only when it preserves the real-publish boundary.

For the older two-target target smoke shape, use [aw-installer External Target Smoke](./aw-installer-external-target-smoke.md) from the release checkpoint under review. Before external trial or publish approval, prefer [aw-installer Multi Temporary Workdir Smoke](./aw-installer-multi-temp-workdir-smoke.md), which covers multiple isolated temporary workdirs and approved target repositories only through temporary clones.

## Forbidden Interpretation

Do not interpret this rehearsal as:

- a published RC.
- proof that `npx aw-installer` is publicly available.
- approval to set `AW_INSTALLER_PUBLISH_APPROVED=1`.
- support for remote update, self-update, signing, or automatic rollback.

This rehearsal only proves the local package, dry-run, guard, and `.tgz` target smoke path.
