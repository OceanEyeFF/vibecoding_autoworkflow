---
title: "aw-installer RC Approval Package"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer RC Approval Package

> Purpose: record the approval package and publish evidence for the first `aw-installer` npm release-candidate line. This page does not authorize stable/latest release semantics or future publish automation.

This page belongs to [Deploy Runbooks](./README.md). It consumes the release channel rules in [aw-installer Release Channel Contract](./release-channel-contract.md), the candidate evidence checklist in [aw-installer Release Candidate Prep](./aw-installer-release-candidate-prep.md), and the package/source boundary in [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md).

## Control Signal

- approval_status: approved-for-P0-019
- real_npm_publish_allowed: true-for-approved-RC-command-only
- publish_requires_separate_approval: satisfied-by-P0-019
- package_version_currently_committed: `0.4.0-rc.1`
- package_real_publish_lock: `awInstallerRelease.realPublishApproval=approved`
- proposed_version_line: `0.4.x`
- proposed_candidate_version: `0.4.0-rc.1`
- proposed_channel: `next`
- proposed_npm_dist_tag: `next`
- proposed_git_tag: `v0.4.0-rc.1`
- proposed_publish_context: CI release context only
- supported_backend_for_candidate: `agents`
- registry_publish_status: published
- registry_dist_tags_observed: `next: 0.4.0-rc.1`, `latest: 0.4.0-rc.1`
- registry_primary_rc_selector: `aw-installer@next`

## Version Rationale

The first release-candidate line should use `0.4.x` because this repository is now in its fourth product shape:

1. repo-local prompt / skill experimentation.
2. Harness doctrine and repo-side contract layer.
3. deployable `agents` backend payload and local package wrapper.
4. `aw-installer` as the near-term Node/npm/npx distribution envelope.

Normal development may use `0.0.0-local`; the release-preflight checkpoint uses `0.4.0-rc.1` as candidate metadata. `P0-019` is the explicit approval worktrack that authorizes publishing this candidate to `next` when the guard inputs and verification evidence match.

## Candidate Identity

| Field | Proposed value |
|---|---|
| approved package identity | unscoped `aw-installer` |
| version | `0.4.0-rc.1` |
| release channel | `next` |
| npm dist-tag | `next` |
| git tag | `v0.4.0-rc.1` |
| backend | `agents` |
| publish context | CI release context only |

The publish guard must reject real publish unless all release-channel contract inputs are present, including tracked package metadata `awInstallerRelease.realPublishApproval=approved`, `CI=true`, `AW_INSTALLER_PUBLISH_APPROVED=1`, derived or explicit channel `next`, `AW_INSTALLER_RELEASE_GIT_TAG=v0.4.0-rc.1`, and the matching npm `--tag next`.

## Evidence Bundle

Use these evidence paths as the approval package bundle:

| Evidence | Path | Status |
|---|---|---|
| Release channel contract | `docs/project-maintenance/deploy/release-channel-contract.md` | active |
| RC prep checklist | `docs/project-maintenance/deploy/aw-installer-release-candidate-prep.md` | active |
| Payload/update trust boundary | `docs/project-maintenance/deploy/payload-provenance-trust-boundary.md` | active |
| External target smoke runbook | `docs/project-maintenance/deploy/aw-installer-external-target-smoke.md` | active |
| Multi temporary workdir smoke runbook | `docs/project-maintenance/deploy/aw-installer-multi-temp-workdir-smoke.md` | active |
| Non-publish release rehearsal | `docs/project-maintenance/deploy/aw-installer-release-rehearsal.md` | passed |
| Runtime external smoke operation artifact | `.aw/repo/aw-installer-external-target-smoke-runbook.md` | runtime evidence |
| Runtime two-target smoke report | `.aw/repo/aw-installer-external-target-smoke-report.md` | passed for local `.tgz` / dry-run evidence |
| Package metadata source | `package.json` | currently `0.4.0-rc.1` release-preflight metadata |
| Real publish metadata lock | `package.json` | currently `approved` for `P0-019` |
| Worktrack backlog source | `.aw/repo/worktrack-backlog.md` | `P0-007` approval package source |
| Latest repo snapshot | `.aw/repo/snapshot-status.md` | refreshed after `develop-aw@f16f55e` |

Before publish execution, refresh or re-run evidence if the intended release checkpoint differs from the smoke checkpoint or if package metadata changes beyond the approved candidate version and approval-lock fields.

## Publish Evidence

`P0-019` published `aw-installer@0.4.0-rc.1` from release checkpoint `55ec715` with local annotated tag `v0.4.0-rc.1`.

Registry evidence:

- package: `aw-installer@0.4.0-rc.1`
- npm account / maintainer: `oceaneye <fdch00@163.com>`
- registry tarball: `https://registry.npmjs.org/aw-installer/-/aw-installer-0.4.0-rc.1.tgz`
- gitHead: `55ec715c7be7878303e4ad0d34767c724947666c`
- shasum: `27e9135f158050e1c615775d2cd05d17dade966b`
- integrity: `sha512-5tt1gLFfSppW4ED3tw0qXfLwXpTSAfUP1SPxMUXFzG2Yd5F+tpOXik2AAlZUnEbHOyT+4SyQJguDwEV8kDqSPA==`
- fileCount: 71
- dist-tags observed after publish:
  - `next: 0.4.0-rc.1`
  - `latest: 0.4.0-rc.1`

The `latest` alias exists because this is the first and only published package version. `npm dist-tag rm aw-installer latest` returned `E400 Bad Request`; do not treat the alias as stable release approval. Use `aw-installer@next` for RC smoke and trial commands until a stable release is explicitly approved.

## Release Notes Draft

`aw-installer@0.4.0-rc.1` is the first proposed release-candidate line for the AW Harness installer.

Included:

- self-contained npm package envelope using the approved unscoped package identity `aw-installer`.
- `aw-installer` CLI entrypoint and `aw-harness-deploy` compatibility alias.
- `aw-installer tui` guided update flow over the same deploy contracts.
- `agents` backend payload sourced from the package or an explicit trusted checkout override.
- install, verify, diagnose, dry-run update, and explicit `update --yes` flows.
- publish guard requiring non-local semver, channel/tag alignment, CI context, and explicit publish approval.
- local `.tgz` smoke evidence covering two isolated target repositories.

Known exclusions:

- no remote fetch.
- no channel-based payload selection.
- no self-update.
- no signature verification.
- no automatic rollback.
- no `claude` or `opencode` deploy backend.
- no stable release semantics or future stable publish without a separate approval decision.

## Rollback Or Deprecation Plan

| Failure after publish | Minimum response |
|---|---|
| Wrong npm dist-tag after multiple versions exist | Correct the dist-tag to the intended channel, record the correction, and preserve the audit note in the release evidence. |
| Initial package exposes `latest` because it is the only version | Record the registry fact, require `aw-installer@next` in RC smoke/trial commands, and do not describe the RC as stable. |
| Bad package surface | Deprecate `0.4.0-rc.1` with a clear message and open a bugfix worktrack before any replacement candidate. |
| Target install failure | Stop recommending the candidate, preserve the target smoke output, and open a bugfix worktrack scoped to the failing command. |
| Documentation mismatch | Patch deploy docs, rerun governance checks, and refresh the evidence bundle before requesting renewed approval. |
| Publish guard mismatch | Treat publish as blocked; fix guard inputs or metadata before retrying any publish command. |

Do not claim automatic rollback unless that behavior has been implemented and verified in a separate worktrack.

## Approval Request Shape

The eventual approval request should include:

- candidate version: `0.4.0-rc.1`
- channel and npm dist-tag: `next`
- git tag: `v0.4.0-rc.1`
- evidence bundle paths from this page
- release notes summary from this page
- rollback/deprecation plan from this page
- confirmation that the package payload does not rely on target repository source layout
- confirmation that multi-temporary-workdir smoke has passed or has a documented, approval-visible rerun blocker
- explicit acknowledgement that `AW_INSTALLER_PUBLISH_APPROVED=1` is supplied only for the approved publish command
- explicit acknowledgement that `awInstallerRelease.realPublishApproval=approved` applies only to `0.4.0-rc.1` on `next`

## Forbidden Wording

Do not use these phrases before registry smoke and public primary-path verification:

- `release is ready`
- `stable release`
- `npx aw-installer is the primary path`
- `update pulls latest`
- `remote update`
- `self-update`

Prefer:

- `published RC candidate`
- `aw-installer@next`
- `registry RC evidence`
- `registry smoke pending`
- `update reinstalls from the current trusted package or checkout payload`
