---
title: "aw-installer RC2 Release Notes"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer RC2 Release Notes

> Purpose: provide the changelog summary for the proposed `aw-installer@0.4.0-rc.2` npm release-candidate. This page does not authorize npm publish or stable release semantics.

This page belongs to [Deploy Runbooks](./README.md). It supports [aw-installer RC2 Approval Package](./aw-installer-rc2-approval-package.md) and follows the release-note requirements in [aw-installer Release Candidate Prep](./aw-installer-release-candidate-prep.md).

## Control Signal

- candidate_version: `0.4.0-rc.2`
- release_channel: `next`
- release_notes_status: ready-for-approval-review
- supported_backend: `agents`
- registry_publish_status: not-yet-published
- stable_release_semantics_allowed: false

## Draft Release Notes

`aw-installer@0.4.0-rc.2` is a prerelease candidate for the AW Harness installer on the npm `next` channel.

This candidate focuses on making the published `npx aw-installer` path safer for Windows PowerShell, Linux bash, and macOS bash trials before broader forum feedback.

Included changes:

- `aw-installer` and `aw-harness-deploy` package wrappers now choose a Python launcher per platform.
- Windows launcher order is `py -3`, then `python`, then `python3`.
- Linux/macOS launcher order is `python3`, then `python`.
- wrapper behavior still ignores `PYTHON` and `PYTHON3` environment variable overrides so package execution is not redirected through untrusted local environment variables.
- packaged `agents` payload now includes the current 19 canonical harness skills.
- `generic-worker-skill` and `doc-catch-up-worker-skill` are included in the packaged `agents` payload.
- package source/target isolation remains unchanged: with no overrides, `npx` reads source payload from the installed package and writes only into the target repository `.agents/skills/`.

Supported operator surface:

- `npx aw-installer --version`
- `npx aw-installer diagnose --backend agents --json`
- `npx aw-installer update --backend agents`
- `npx aw-installer update --backend agents --yes`
- `npx aw-installer verify --backend agents`
- `npx aw-installer install --backend agents`
- interactive `npx aw-installer tui` when a real terminal is available.

## Verification Summary

The rc2 candidate has passed:

- root package pack dry-run.
- root publish dry-run.
- release metadata derivation for `v0.4.0-rc.2 -> next`.
- negative real-publish guard check while approval remains pending.
- deploy regression suite.
- governance pytest suite.
- folder/path/semantic governance checks.
- local multi-temporary-workdir package smoke across three generated targets.
- explicit local `npx --package <local.tgz>` install/update/verify flow, with 19 managed installs and no conflicts.
- closeout acceptance gate.

## Known Exclusions

This candidate still does not implement:

- stable release semantics.
- remote payload fetch.
- channel-based payload selection at runtime.
- self-update.
- signature verification.
- automatic rollback.
- npm-side Trusted Publisher setup.
- `claude` or `opencode` deploy backend.

## Operator Notes

Until `0.4.0-rc.2` is actually published, `aw-installer@next` still resolves to the older `0.4.0-rc.1` registry package. Do not use the registry package as the Windows PowerShell forum candidate until post-publish registry smoke proves `next` resolves to rc2.
