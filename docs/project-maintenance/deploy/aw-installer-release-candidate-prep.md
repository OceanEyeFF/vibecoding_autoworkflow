---
title: "aw-installer Release Candidate Prep"
status: active
updated: 2026-04-27
owner: aw-kernel
last_verified: 2026-04-27
---
# aw-installer Release Candidate Prep

> Purpose: define the operator checklist for preparing an `aw-installer` release-candidate evidence bundle. This page does not authorize or run real `npm publish`.

This page belongs to [Deploy Runbooks](./README.md). It consumes the publish gate in [aw-installer Release Channel Contract](./release-channel-contract.md), the CLI/TUI entrypoint contract in [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md), and the payload/update trust boundary in [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md).

## Current Stop Line

- The current root `package.json` version is `0.0.0-local`.
- While that version remains local, the valid release-candidate output is a local `.tgz` plus dry-run and smoke evidence.
- A real npm release candidate requires a separate approval boundary and a non-local prerelease semver.
- Publish dry-run and root `.tgz` smoke prove package surface and entrypoint behavior only; they are not release authorization.
- `npm whoami` success is only an operator credential readiness signal. It does not approve real publish.

## Candidate Channel Proposal

Use this proposal when preparing the first npm release-candidate checkpoint:

| Field | Proposed value |
|---|---|
| package | `aw-installer` |
| channel | `next` |
| npm dist-tag | `next` |
| version form | `x.y.z-rc.N` |
| git tag form | `v<x.y.z-rc.N>` |
| publish context | CI release context only |

The release guard requires a real RC publish to satisfy all of these conditions:

- root package version is valid semver and not `0.0.0-local`.
- `AW_INSTALLER_RELEASE_GIT_TAG=v<package.version>`.
- npm dist-tag is `next`.
- `AW_INSTALLER_RELEASE_CHANNEL=next`, unless the guard derives the same channel from the release git tag.
- `CI=true`.
- `AW_INSTALLER_PUBLISH_APPROVED=1`.

Do not use `latest` for the first release-candidate checkpoint. Do not use `canary` unless the goal is explicitly a short-lived experimental artifact.

## Evidence Bundle

Collect this evidence before asking for real publish approval:

- clean worktree on the intended release checkpoint.
- root `npm pack --dry-run --json`.
- root `npm run publish:dry-run --silent`.
- isolated root `.tgz` smoke with both `AW_HARNESS_REPO_ROOT=""` and `AW_HARNESS_TARGET_REPO_ROOT=""`.
- smoke coverage for:
  - `aw-installer --help`
  - `aw-installer --version`
  - non-interactive `aw-installer tui` guard
  - `aw-installer diagnose --backend agents --json`
  - `aw-installer update --backend agents --json`
  - `aw-installer install --backend agents`
  - `aw-installer verify --backend agents`
  - `aw-installer update --backend agents --yes`
- closeout gate evidence for the release-prep worktrack.
- release notes or changelog summary for the candidate version.
- rollback or deprecation plan, at minimum naming npm dist-tag correction or package deprecation path.

Worktrack-specific smoke evidence may live in runtime artifacts while the release-candidate work is active. If that evidence becomes a stable operator procedure, promote the verified procedure into `docs/project-maintenance/deploy/` instead of treating runtime state as long-term truth.

## Release Notes Draft Requirements

The release notes or changelog summary should include:

- package name and candidate version.
- supported backend list; currently only `agents`.
- CLI/TUI entrypoints included in the package.
- payload provenance summary: source payload comes from the package or explicit checkout override.
- update boundary: current `update` reinstalls from the trusted package or checkout payload.
- known exclusions:
  - no remote fetch.
  - no channel-based payload selection.
  - no self-update.
  - no signature verification.
  - no automatic rollback.
  - no `claude` or `opencode` deploy backend.
- verification evidence links or paths.
- operator-facing recovery notes for install/update failure.

## Rollback Or Deprecation Plan

Before real publish approval, name the recovery path for at least these cases:

| Failure after publish | Minimum recovery path |
|---|---|
| Wrong dist-tag | Correct npm dist-tag to the intended channel and record the correction. |
| Bad package surface | Deprecate the broken version with a clear message and publish a fixed version after a new gate. |
| Target install failure | Stop recommending the candidate, preserve smoke evidence, and open a bugfix worktrack. |
| Documentation mismatch | Update deploy docs and README surfaces, then rerun governance checks and package smoke. |

Do not describe automatic rollback unless that behavior has been implemented and verified in a separate approved worktrack.

## Forbidden Wording

Avoid these phrases while the package remains local:

- `published RC`
- `release is ready`
- `npx aw-installer is available`
- `update pulls latest`
- `remote update`
- `self-update`

Prefer:

- `release-candidate prep checkpoint`
- `RC evidence bundle`
- `local .tgz smoke`
- `publish approval pending`
- `update reinstalls from the current trusted package or checkout payload`

## Verification For This Prep Work

For docs-only release-candidate prep changes, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
npm run publish:dry-run --silent
```

If the change alters closeout, release gate behavior, package metadata, wrapper behavior, or smoke coverage, add the relevant package/deploy tests and:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/closeout_acceptance_gate.py --json
```

## Handoff To Approval

Only request real publish approval after the evidence bundle is complete. The approval request should include:

- candidate version.
- channel and npm dist-tag.
- git tag.
- evidence bundle paths.
- release notes summary.
- rollback or deprecation plan.
- confirmation that the current package payload does not rely on target repo source layout.

Real publish remains out of scope until the approval boundary is explicitly crossed.
