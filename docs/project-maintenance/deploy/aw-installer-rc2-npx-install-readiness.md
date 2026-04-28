---
title: "aw-installer RC2 npx Install Readiness"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer RC2 npx Install Readiness

> Purpose: record the `aw-installer@0.4.0-rc.2` install-flow readiness and post-publish registry smoke facts before any forum trial handoff. This page does not authorize stable/latest release, npm dist-tag mutation, or npm Trusted Publisher setup.

This page belongs to [Deploy Runbooks](./README.md). It complements [aw-installer Registry npx Smoke](./aw-installer-registry-npx-smoke.md), [aw-installer Public Quickstart Prompts](./aw-installer-public-quickstart-prompts.md), and [aw-installer Release Channel Contract](./release-channel-contract.md).

## Control Signal

- candidate_version: `0.4.0-rc.2`
- readiness_status: registry-next-install-flow-passed
- registry_current_next_version: `0.4.0-rc.2`
- registry_current_latest_version: `0.4.0-rc.1`
- registry_current_next_status: linux-local-registry-smoke-passed
- forum_trial_recommendation: use `aw-installer@next` for rc2; do not use bare `aw-installer` when rc2 behavior is required
- primary_blocker: Windows PowerShell and macOS registry smoke still need real host coverage before broad forum handoff
- real_npm_publish_allowed_by_this_page: false
- github_release_publish_priority: after registry `aw-installer@next` install flow is proven for the intended RC

## Observed Registry State

`npm view aw-installer name version dist-tags bin --json` and `npm view aw-installer@next name version bin --json` currently report:

- package: `aw-installer`
- default version through `latest`: `0.4.0-rc.1`
- `next`: `0.4.0-rc.2`
- `latest`: `0.4.0-rc.1`
- bin entries: `aw-installer`, `aw-harness-deploy`

The current rc2 registry package is available through `aw-installer@next`. Bare `aw-installer` still resolves to `0.4.0-rc.1` through npm `latest`.

## RC2 Fix Scope

The `0.4.0-rc.2` candidate keeps the same package entrypoints and adds cross-platform Python launcher fallback in both Node wrappers:

- Windows: `py -3`, then `python`, then `python3`
- Linux/macOS: `python3`, then `python`
- `PYTHON` and `PYTHON3` environment variable overrides remain ignored by design.

The candidate package also includes the current 19-skill agents payload, including the generic worker and doc catch-up worker skills.

## Verification Evidence

Local package candidate:

- `npm pack --dry-run --json`: produced `aw-installer-0.4.0-rc.2.tgz` with 77 files.
- `toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh --skip-remote --output-dir /tmp/aw-rc2-local-smoke-final`: passed for three generated temporary target workdirs.
- local smoke report: `/tmp/aw-rc2-local-smoke-final/report.md`
- local smoke summary: `/tmp/aw-rc2-local-smoke-final/summary.tsv`
- `toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh --skip-remote`: passed again in the prepublish closeout pass for three generated temporary target workdirs.
- explicit local `npx --package <aw-installer-0.4.0-rc.2.tgz> -- aw-installer update --backend agents --yes && verify`: passed for a generated target repo, with final `binding_count=19`, `managed_install_count=19`, `conflict_count=0`, and `unrecognized_count=0`.

Registry current package:

- `node toolchain/scripts/test/aw_installer_registry_npx_smoke.js --package aw-installer@next --skip-remote --output-dir /tmp/aw-rc2-postpublish-registry-smoke`: passed on Linux for three generated temporary target workdirs.
- registry smoke report: `/tmp/aw-rc2-postpublish-registry-smoke/report.md`
- registry smoke summary: `/tmp/aw-rc2-postpublish-registry-smoke/summary.tsv`
- observed registry version for `aw-installer@next`: `0.4.0-rc.2`
- observed final `binding_count`: `19`

Focused wrapper verification:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest toolchain.scripts.deploy.test_adapter_deploy.AdapterDeployTest.test_node_deploy_wrappers_fall_back_to_python_when_python3_is_missing toolchain.scripts.deploy.test_adapter_deploy.AdapterDeployTest.test_node_deploy_wrappers_ignore_python_env_overrides toolchain.scripts.deploy.test_adapter_deploy.AdapterDeployTest.test_node_deploy_wrappers_time_out_stalled_python_processes`: passed.
- full deploy regression suite: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'`: 113 tests passed.
- full `toolchain/scripts/test` pytest suite: 185 tests passed.
- folder, path, and semantic governance checks: passed.

## Publish Boundary

Publishing `0.4.0-rc.2` to npm `next` has completed through the explicit approval-lock flow. Root `package.json` now binds:

- `awInstallerRelease.realPublishApproval: approved`
- `approvedVersion: 0.4.0-rc.2`
- `approvedGitTag: v0.4.0-rc.2`
- `approvedChannel: next`

Published release tuple:

- version: `0.4.0-rc.2`
- git tag: `v0.4.0-rc.2`
- npm dist-tag: `next`

The rc2 publish approval package, release notes, and rollback plan are tracked separately:

- [aw-installer RC2 Approval Package](./aw-installer-rc2-approval-package.md)
- [aw-installer RC2 Release Notes](./aw-installer-rc2-release-notes.md)
- [aw-installer RC2 Rollback And Deprecation Plan](./aw-installer-rc2-rollback-deprecation-plan.md)

Do not use bare `npx aw-installer` when rc2 behavior is required; use `aw-installer@next` until a future stable/latest release is explicitly approved.
