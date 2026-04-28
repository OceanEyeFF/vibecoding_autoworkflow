---
title: "npx Command Test Execution"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# npx Command Test Execution

> Purpose: verify `aw-installer` package and npx command behavior across isolated temporary targets, covering the published registry package, explicit RC selector, and local `.tgz` package smoke. This page does not authorize new npm publish, stable release semantics, external repository mutation, PRs, or issue creation.

This page belongs to [Testing Runbooks](./README.md). Release channel and publish readiness rules live in [aw-installer Release Channel Contract](../deploy/release-channel-contract.md); deploy entrypoint semantics live in [Distribution Entrypoint Contract](../deploy/distribution-entrypoint-contract.md).

## Control Signal

- smoke_status: operator-runnable
- canonical_runner: `toolchain/scripts/test/aw_installer_registry_npx_smoke.js`
- local_tgz_runner: `toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh`
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

The registry smoke uses the published npm registry package. The local `.tgz` smoke packs the current checkout and exercises that package from temporary target repositories. Neither path publishes a new package.

Allowed:

- run `npx --package aw-installer -- aw-installer ...` from generated temporary targets.
- pin the RC stream with `--package aw-installer@next` when reproducing RC-specific results.
- run local `.tgz` package commands from generated temporary targets.
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

## Local Package Smoke

Use the local package smoke when the candidate is not yet published, or when validating the current checkout before a future release approval:

```bash
toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh
```

For offline or CI-style local-only checks:

```bash
toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh --skip-remote
```

The local package smoke:

- packs the current checkout into a local `.tgz` through `toolchain/scripts/test/npm_pack_tarball.sh`.
- pins npm cache, tmp, user config, and HOME under the evidence directory.
- creates one empty temporary git repo.
- clones the approved public target repositories into temporary directories unless `--skip-remote` is used.
- disables push URLs in temporary remote clones before installer commands run.
- runs help, version, non-interactive TUI guard, diagnose, update dry-run, install, verify, update apply, and final diagnose in each target.
- checks that planned target paths and final target roots stay inside each target workdir.
- checks that package source root does not resolve to the source checkout, target repo, or target root.

## Two-Target Tarball Smoke

When a smaller local package check is enough, use two generated targets:

```bash
tmpdir="$(mktemp -d)"
npm pack --json --pack-destination "$tmpdir" > "$tmpdir/pack.json"
package_file="$(
  node -e "const fs = require('node:fs'); const payload = JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); console.log(payload[0].filename);" "$tmpdir/pack.json"
)"
package_path="$tmpdir/$package_file"

for target_name in target-alpha target-beta; do
  target_repo="$tmpdir/$target_name"
  mkdir -p "$target_repo"
  (
    cd "$target_repo"
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer --help
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer --version
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer diagnose --backend agents --json
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer update --backend agents --json
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer install --backend agents
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer verify --backend agents
    AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npm exec --yes --package "$package_path" -- aw-installer update --backend agents --yes
  )
done
```

## What The Registry Runner Does

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

- Local-only mode passes generated temporary target workdirs.
- Default mode passes the generated empty repo plus temporary clones of the approved target repositories, unless network access is unavailable and the blocker is recorded.
- Each final diagnose reports managed installs equal to the selected package or candidate `binding_count`, with 0 conflicts and 0 unrecognized entries.
- Each dry-run planned target path stays inside its own temporary target workdir.
- No observed source root resolves inside the AW source checkout.
- No observed source root resolves inside any temporary target repository or equals a target root.
- npm state is pinned under the smoke evidence directory.
- No push, PR, issue, or remote mutation occurs.
- Each target has an `aw-installer-npx-run.log` suitable for sanitized feedback.

Long-term writeback should copy only sanitized summaries. Do not store private paths, tokens, credentials, private repository names, or full sensitive logs in docs.
