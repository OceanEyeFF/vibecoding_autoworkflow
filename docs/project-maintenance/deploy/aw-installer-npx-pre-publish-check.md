---
title: "aw-installer npx Pre-Publish Check"
status: active
updated: 2026-04-29
owner: aw-kernel
last_verified: 2026-04-29
---
# aw-installer npx Pre-Publish Check

> Purpose: provide the maintainer-facing checklist that must be completed before any future `aw-installer` npm publish is approved or executed. npm package versions are immutable after publication; do not publish first and repair package files, docs, or metadata afterward.

This page belongs to [Deploy Runbooks](./README.md). It consumes release-channel rules from [aw-installer Release Channel Contract](./release-channel-contract.md), the publish carrier model from [aw-installer Release Operation Model](./aw-installer-release-operation-model.md), and package smoke commands from [npx Command Test Execution](../testing/npx-command-test-execution.md).

## Control Signal

- check_status: required-before-future-publish
- applies_to: `aw-installer` npm package
- real_publish_allowed_by_this_page: false
- required_before:
  - approving a future GitHub Release `published` workflow run
  - setting `awInstallerRelease.realPublishApproval=approved`
  - running manual `npm publish`
  - treating a published package as ready for external npx trial
- immutable_publish_risk: true

## Stop Rule

Stop before publish if any of these are true:

- a required package file is missing from the packlist.
- package metadata, git tag, GitHub Release prerelease flag, release body marker, npm dist-tag, or approval lock do not describe the same release tuple.
- docs still point users to the wrong selector, especially bare `npx aw-installer` when the candidate is only on `next`.
- `npm pack --dry-run --json`, `npm run publish:dry-run --silent`, governance checks, deploy tests, or closeout gate fail.
- local package smoke has not proved install/update/verify in temporary target repositories.
- for rc3 or later, `update --source github --github-ref master --json` has not proved that the GitHub source archive contains a valid Harness payload source and keeps target root separate from the archive extraction root.
- rollback/deprecation notes are missing.

Do not rely on a later patch version to repair a package that was missing files, stale docs, or wrong metadata at publish time. A replacement version can supersede a broken version, but it cannot mutate the already published tarball.

## 1. Candidate Identity

Record the release tuple before any package or docs change:

| Field | Required check |
|---|---|
| package name | root `package.json` name is `aw-installer` |
| package version | semver, not `0.0.0-local`, not reused from a prior npm publish |
| git tag | exactly `v<package.version>` |
| npm dist-tag | matches release channel: `next` for RC/prerelease, `latest` only for approved stable |
| GitHub Release prerelease flag | matches semver prerelease state |
| release body marker | includes `aw-installer-publish-approved: v<package.version>` |
| approval lock | `awInstallerRelease.approvedVersion`, `approvedGitTag`, and `approvedChannel` match the tuple |

For RC trials, user-facing commands must prefer `aw-installer@next`; bare `npx aw-installer` resolves through npm `latest` and may target an older RC.

## 2. Packlist Review

Run:

```bash
npm pack --dry-run --json
```

Review the emitted file list before approval. It must include:

- root `README.md`, `LICENSE`, and root `package.json`.
- `toolchain/scripts/deploy/bin/aw-installer.js`.
- deploy wrapper scripts used by the package entrypoint.
- `product/harness/skills/` canonical skill payload files required by agents bindings.
- `product/harness/adapters/agents/skills/` payload descriptors.
- `product/.aw_template/` files required for `.aw/` scaffold behavior.
- release/deploy docs needed by the package README or operator paths.

It must not include:

- `.aw/`, `.agents/`, `.claude/`, `.opencode/`, `.autoworkflow/`, `.spec-workflow/`, or `.nav/` runtime state.
- Python caches, pytest caches, `.pyc`, `.pyo`, npm debug logs, temporary evidence directories, or private target repo artifacts.
- one-off review evidence or old release approval packages that are not current operator truth.

If the packlist is wrong, fix package `files`, docs routing, or source layout before publish. Do not publish and then repair in a later commit.

## 3. Documentation Freshness

Before approval, check:

- root `README.md` names the correct selector for the candidate.
- [Deploy Runbooks](./README.md) routes deploy usage/explanation only.
- [Testing Runbooks](../testing/README.md) routes npx/local package smoke and Codex/Claude behavior tests.
- [aw-installer Release Channel Contract](./release-channel-contract.md) records the current registry facts and future publish boundary.
- [aw-installer Release Operation Model](./aw-installer-release-operation-model.md) matches the current workflow behavior.
- [npx Command Test Execution](../testing/npx-command-test-execution.md) describes the exact registry/local package smoke commands that will be used before and after publish.
- external trial feedback templates do not ask for private repo identifiers, tokens, credentials, or full sensitive logs.

If docs disagree with package behavior or registry facts, update docs and rerun governance before publish.

## 4. Dry-Run And Governance Evidence

Run these checks from a clean worktree on the candidate checkpoint:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/folder_logic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
npm pack --dry-run --json
npm run publish:dry-run --silent
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json
```

The dry-run path proves package surface and publish guard behavior. It does not authorize real publish.

## 5. Local Package Smoke Before Publish

Before any future publish approval, prove the candidate package from the current checkout:

```bash
toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh --skip-remote
```

When network access and target approvals are available, run the full matrix:

```bash
toolchain/scripts/test/aw_installer_multi_temp_workdir_smoke.sh
```

Minimum evidence:

- help/version/TUI guard succeed or fail as expected.
- `diagnose --backend agents --json` and `update --backend agents --json` run before mutation.
- `update --backend agents --source github --github-ref master --json` passes when the release includes GitHub source update capability.
- `install --backend agents`, `verify --backend agents`, and `update --backend agents --yes` pass.
- final diagnose reports managed installs equal to the selected candidate `binding_count`, with 0 conflicts and 0 unrecognized entries.
- source root resolves to the package payload, not the source checkout or target repository.
- target root stays inside each temporary target workdir.

## 6. Real Publish Approval Check

Only after the previous sections pass may the release-approval worktrack set:

```json
{
  "realPublishApproval": "approved",
  "approvedVersion": "<package.version>",
  "approvedGitTag": "v<package.version>",
  "approvedChannel": "<latest|next|canary>"
}
```

For manual publish, the command shape must include:

```text
CI=true
AW_INSTALLER_PUBLISH_APPROVED=1
AW_INSTALLER_RELEASE_GIT_TAG=v<package.version>
npm publish --tag <channel>
```

For GitHub Release / Trusted Publishing, the workflow must derive the same tuple from the release metadata and run the same pre-publish checks before `npm publish --provenance`.

## 7. Post-Publish Separation

After publish, run registry smoke through [npx Command Test Execution](../testing/npx-command-test-execution.md). Post-publish smoke verifies the registry artifact that now exists; it is not a substitute for the pre-publish checks above.

If post-publish smoke fails:

- do not mutate external target repositories.
- correct npm dist-tags if the wrong tag points at the version.
- deprecate the broken version if the package contents are wrong.
- prepare a replacement version through a new approval worktrack.
- pause external trial handoff until the replacement selector is proven.
