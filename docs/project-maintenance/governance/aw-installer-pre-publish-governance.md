---
title: "aw-installer Pre-Publish Governance"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# aw-installer Pre-Publish Governance

> Purpose: define the minimum release-readiness boundary that must pass before any future `aw-installer` publish can be approved.

This page belongs to [Governance](./README.md).

## This Page Manages

- candidate release tuple readiness
- packlist and docs freshness
- required local preflight evidence classes
- the approval lock that authorizes a future publish

## This Page Does Not Manage

- the branch and GitHub Release sequence: see [aw-installer Release Standard Flow](./aw-installer-release-standard-flow.md)
- release-channel policy and current registry facts: see [aw-installer Release Channel Governance](./aw-installer-release-channel-governance.md)
- local `.tgz` and registry `npx` smoke execution: see [npx Command Test Execution](../testing/npx-command-test-execution.md)

## Stop Rule

Stop before publish if any of these are true:

- package files, docs, metadata, tag, channel, or approval lock do not describe the same release tuple
- required preflight or smoke evidence is missing
- docs still route operators to the wrong selector or stale behavior
- local package smoke has not proved the candidate package in temporary targets

Do not publish first and repair later. npm package versions are immutable.

## 1. Candidate Tuple

Before approval, confirm the exact tuple:

| Field | Required check |
| --- | --- |
| package name | root `package.json` name is `aw-installer` |
| package version | valid semver, not `0.0.0-local`, not already published |
| git tag | exactly `v<package.version>` |
| npm dist-tag | matches the intended release channel |
| GitHub Release prerelease flag | matches the semver prerelease state |
| release body marker | includes `aw-installer-publish-approved: v<package.version>` |
| approval lock | `approvedVersion`, `approvedGitTag`, and `approvedChannel` match the tuple |

For RC lanes, operator-facing commands must prefer `aw-installer@next`, not bare `aw-installer`.

## 2. Packlist And Docs Freshness

Run:

```bash
npm pack --dry-run --json
```

Before approval, verify:

- the packlist contains the package entrypoint, required payload descriptors, required canonical skill payload files, and package-facing docs
- the packlist excludes runtime state, caches, temporary evidence, and one-off review material
- root `README.md` and operator-facing governance/testing/usage docs point to the correct selector and current behavior
- deploy docs do not become release policy pages, and testing docs do not become approval pages

If the packlist or docs are wrong, fix them before approval.

## 3. Required Local Preflight Evidence

Before approval, retain passing evidence for:

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

This proves the candidate surface and publish guard. It does not publish anything.

## 4. Required Local Package Smoke

Before approval, also complete the local package smoke defined in [npx Command Test Execution](../testing/npx-command-test-execution.md).

This page requires that evidence to exist, but the command matrix, temporary-target rules, and pass criteria belong to the testing runbook.

## 5. Approval Lock

Only after the previous sections pass may the approval worktrack set:

```json
{
  "realPublishApproval": "approved",
  "approvedVersion": "<package.version>",
  "approvedGitTag": "v<package.version>",
  "approvedChannel": "<latest|next|canary>"
}
```

This page only authorizes the tuple lock. It does not execute the release sequence.

## 6. Next Step

Once the candidate tuple and evidence are ready, continue with [aw-installer Release Standard Flow](./aw-installer-release-standard-flow.md).
