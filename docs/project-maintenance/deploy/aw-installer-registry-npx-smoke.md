---
title: "aw-installer Registry npx Smoke"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Registry npx Smoke

> Purpose: verify the published registry `aw-installer` package through npx across isolated temporary targets, and produce per-target run logs that can be attached to sanitized feedback. This page does not authorize new npm publish, stable release semantics, external repository mutation, PRs, or issue creation.

This page belongs to [Deploy Runbooks](./README.md). It follows the registry evidence recorded in [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md) and complements the local `.tgz` [aw-installer Multi Temporary Workdir Smoke](./aw-installer-multi-temp-workdir-smoke.md).

## Control Signal

- smoke_status: operator-runnable
- canonical_runner: `toolchain/scripts/test/aw_installer_registry_npx_smoke.js`
- supported_operator_shells:
  - Windows PowerShell
  - Linux bash
  - macOS bash
- default_package_selector: `aw-installer`
- rc_pin_selector: `aw-installer@next`
- default_target_count: 3
- feedback_log_artifact: `aw-installer-npx-run.log`
- remote_mutation_allowed: false
- real_npm_publish_allowed: false

## Boundary

The smoke uses the published npm registry package. It does not pack the current checkout and it does not publish a new package.

Allowed:

- run `npx --package aw-installer -- aw-installer ...` from generated temporary targets.
- pin the RC stream with `--package aw-installer@next` when reproducing RC-specific results.
- clone approved public target repositories into temporary directories.
- write `.agents/skills/` only inside generated temporary target workdirs.
- preserve local evidence under a temporary evidence directory.
- attach a sanitized `aw-installer-npx-run.log` to feedback.

Not allowed:

- push to `OceanEyeFF/T1.AI` or `OceanEyeFF/novel-agents`.
- open issues or PRs against those repositories.
- mutate a non-temporary checkout.
- treat the registry `latest` alias as stable release approval.
- store private repo identifiers, credentials, tokens, or sensitive full logs in long-term docs.

## Cross-Platform Runner

The canonical runner is Node-based so the same smoke logic works under Windows PowerShell, Linux bash, and macOS bash.

Windows PowerShell from the AW source repository root:

```powershell
node .\toolchain\scripts\test\aw_installer_registry_npx_smoke.js --skip-remote
node .\toolchain\scripts\test\aw_installer_registry_npx_smoke.js
```

Linux or macOS bash from the AW source repository root:

```bash
node toolchain/scripts/test/aw_installer_registry_npx_smoke.js --skip-remote
node toolchain/scripts/test/aw_installer_registry_npx_smoke.js
```

The bash compatibility wrapper delegates to the same Node runner:

```bash
toolchain/scripts/test/aw_installer_registry_npx_smoke.sh --skip-remote
```

Use an explicit output directory when you need stable artifact paths:

```bash
node toolchain/scripts/test/aw_installer_registry_npx_smoke.js --output-dir /tmp/aw-installer-registry-npx-smoke
```

```powershell
node .\toolchain\scripts\test\aw_installer_registry_npx_smoke.js --output-dir "$env:TEMP\aw-installer-registry-npx-smoke"
```

Use the RC channel pin only when you need to prove the `next` selector specifically:

```bash
node toolchain/scripts/test/aw_installer_registry_npx_smoke.js --package aw-installer@next --skip-remote
```

## What The Runner Does

The runner:

- records Node/npm versions, local git branch/ref, `npm view <selector> version`, and `npm dist-tag ls aw-installer`.
- creates one empty temporary git repo.
- clones the two approved target repositories into temporary directories unless `--skip-remote` is used.
- disables push URLs in temporary remote clones before installer commands run.
- runs help, version, non-interactive TUI guard, diagnose, update dry-run, install, verify, update apply, and final diagnose through npx.
- pins npm cache, tmp, user config, and HOME/USERPROFILE under the evidence directory.
- checks that target paths stay inside each temporary target workdir.
- checks that the package source root is not the AW source checkout and not the target repo.
- writes `summary.tsv`, `report.md`, and one `aw-installer-npx-run.log` per target.

## Feedback Log

Each target evidence directory contains:

```text
evidence/<target-alias>/aw-installer-npx-run.log
```

The log contains:

- sanitized target alias and target source category.
- package selector and observed registry version.
- Node/npm versions and registry dist-tags.
- each npx command executed.
- stdout, stderr, and exit status per command.

Before attaching a log to GitHub feedback, remove private paths, private repo names, user names, tokens, credentials, customer names, and any sensitive environment-specific details. Keep enough command output to diagnose the failure or confirm the pass.

## Pass Criteria

- Local-only mode passes three generated temporary target workdirs.
- Default mode passes the generated empty repo plus temporary clones of the two approved target repositories, unless network access is unavailable and the blocker is recorded.
- Each final diagnose reports managed installs equal to the published package `binding_count`, with 0 conflicts and 0 unrecognized entries.
- Each dry-run planned target path stays inside its own temporary target workdir.
- No observed source root resolves inside the AW source checkout.
- No observed source root resolves inside any temporary target repository or equals a target root.
- npm state is pinned under the smoke evidence directory.
- No push, PR, issue, or remote mutation occurs.
- Each target has an `aw-installer-npx-run.log` suitable for sanitized feedback.
