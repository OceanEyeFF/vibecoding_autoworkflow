---
title: "aw-installer Multi Temporary Workdir Smoke"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Multi Temporary Workdir Smoke

> Purpose: verify the pre-release `aw-installer` package in multiple independent temporary target workdirs before real external trials. This page does not authorize npm publish, package-name decisions, pushes, PRs, issue creation, or remote mutation.

This page belongs to [Deploy Runbooks](./README.md). It extends [aw-installer External Target Smoke](./aw-installer-external-target-smoke.md) from two generated targets to a reusable multi-workdir smoke matrix.

## Control Signal

- smoke_status: operator-runnable
- default_target_count: 3
- default_target_sources:
  - generated empty temporary git repo
  - temporary clone of `https://github.com/OceanEyeFF/T1.AI`
  - temporary clone of `https://github.com/OceanEyeFF/novel-agents`
- remote_mutation_allowed: false
- real_npm_publish_allowed: false
- package_name_decision_in_scope: false

## Boundary

The target repositories approved for this smoke are source inputs only. The smoke must clone or generate temporary workdirs and run installer writes only inside those temporary workdirs.

Allowed:

- clone approved public target repositories into a temporary directory.
- run local `.tgz` package commands from each temporary target workdir.
- write `.agents/skills/` inside each temporary target workdir.
- preserve local evidence under a temporary evidence directory.

Not allowed:

- push to `OceanEyeFF/T1.AI` or `OceanEyeFF/novel-agents`.
- open issues or PRs against those repositories.
- mutate a non-temporary checkout.
- use this smoke as npm publish approval.

## Script

Run from the AW source repository root:

```bash
toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh
```

The script:

- packs the current checkout into a local `.tgz` through `toolchain/scripts/test/npm_pack_tarball.sh`.
- pins npm cache, tmp, user config, and HOME used by package/exec commands under the evidence directory.
- creates one empty temporary git repo.
- clones the two approved target repositories into temporary directories unless `--skip-remote` is used.
- disables push URLs in temporary remote clones before running installer commands.
- runs `aw-installer --help`, `--version`, non-interactive `tui`, `diagnose --json`, `update --json`, `install`, `verify`, `update --yes`, and final `diagnose --json` in each target.
- checks that planned target paths and final target roots stay inside each target workdir.
- checks that final package source root does not resolve to the source checkout, target repo, or target root.
- writes `summary.tsv` and `report.md` under the evidence directory.

For offline or CI-style local-only checks:

```bash
toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh --skip-remote
```

## Pass Criteria

- At least three independent target workdirs pass in the default network-enabled run.
- The local-only fallback still covers three independent generated workdirs when remote access is unavailable.
- Each target completes help/version/TUI guard/diagnose/update dry-run/install/verify/update apply/final diagnose.
- Each final diagnose reports 17 managed installs, 0 conflicts, and 0 unrecognized entries.
- Each dry-run planned target path stays inside its own temporary target workdir.
- No observed source root resolves inside the AW source checkout.
- No observed source root resolves inside any temporary target repository or equals a target root.
- npm package/exec state is pinned under the smoke evidence directory rather than the operator home cache.
- No push, PR, issue, or remote mutation occurs.
- Temporary remote clones have push URLs set to `DISABLED_BY_AW_TEMP_SMOKE_NO_PUSH` before installer commands run.

## Evidence Template

The script emits a generated `report.md` with:

- candidate branch and commit.
- package path.
- node/npm versions.
- target source and target workdir path.
- pass/fail result per target.
- source-root and target-root leakage verdict.
- npm publish boundary.

Long-term writeback should copy only sanitized summaries. Do not store private paths, tokens, or full logs unless explicitly approved.
