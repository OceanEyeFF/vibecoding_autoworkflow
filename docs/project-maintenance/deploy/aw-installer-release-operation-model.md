---
title: "aw-installer Release Operation Model"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Release Operation Model

> Purpose: define the `aw-installer` publish operating model after the first manual RC publish and registry npx smoke. This page records the selected GitHub Release `published` plus npm Trusted Publishing model and the repository-side workflow preflight. It does not authorize a future npm publish or mutate npm-side Trusted Publisher settings.

This page belongs to [Deploy Runbooks](./README.md). It builds on [aw-installer Release Channel Contract](./release-channel-contract.md), [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md), and [aw-installer Registry npx Smoke](./aw-installer-registry-npx-smoke.md).

## Control Signal

- decision_status: repository-workflow-preflight-implemented
- selected_operation_model: GitHub Release `published` trigger with npm Trusted Publishing
- selected_auth_model: npm Trusted Publisher through GitHub Actions OIDC
- long_lived_npm_token_required: false
- publish_workflow_implemented: true
- publish_workflow_path: `.github/workflows/publish.yml`
- future_npm_publish_allowed_by_this_page: false
- required_human_approval_action: create or publish a GitHub Release for an already reviewed version/tag
- required_release_body_marker: `aw-installer-publish-approved: v<package.version>`
- recommended_workflow_filename: `publish.yml`
- recommended_github_environment: `npm`
- recommended_node_version_for_publish_job: `24`
- minimum_npm_cli_for_trusted_publishing: `11.5.1`
- repository_workflow_requires_followup_worktrack: false
- release_guard_hardening_requires_followup_worktrack: false

## Decision

Future `aw-installer` publish implementation should use:

- GitHub Actions as the CI carrier.
- GitHub Release `published` as the publish trigger.
- npm Trusted Publishing as the registry authentication path.
- GitHub Environment protection named `npm` if the repository owner wants an additional reviewer gate before the publish job runs.

This is a better fit than fully automatic main-branch release for this repository because it keeps a human approval moment at Release publication while still removing manual 2FA/browser publish friction and long-lived npm token handling.

## Why Release Published

Release `published` is the preferred trigger for this project over raw tag push:

| Option | Fit | Decision |
|---|---|---|
| tag push | simple and common, but a pushed tag can be too easy to create accidentally | keep as a fallback |
| GitHub Release `published` | explicit operator action with release notes, artifacts, and reviewable UI | preferred |
| main branch auto release | useful for mature libraries with automated changelog/versioning | not selected now |

The selected model keeps the release action visible:

1. prepare version, release notes, and evidence in a normal worktrack.
2. merge the release-prep commit to the release branch.
3. create or publish a GitHub Release for the exact tag.
4. GitHub Actions runs the publish job.
5. npm accepts the publish through Trusted Publishing if the npm package settings match the workflow identity.

## Trusted Publishing Setup

npm-side package settings must configure a Trusted Publisher:

| Field | Value |
|---|---|
| Provider | GitHub Actions |
| Organization or user | repository owner |
| Repository | this repository |
| Workflow filename | `publish.yml` |
| Environment name | `npm` if environment protection is used, otherwise empty |

The workflow must live at:

```text
.github/workflows/publish.yml
```

Trusted Publishing uses short-lived OIDC credentials and should be preferred over `NPM_TOKEN` for this package. Traditional token-based publish remains a fallback only if Trusted Publishing is unavailable.

## Workflow Shape

The repository-side workflow preflight now lives at `.github/workflows/publish.yml`. It is triggered only by GitHub Release `published`, grants `id-token: write`, uses the `npm` GitHub Environment, installs npm `11.5.1` on Node `24` for Trusted Publishing compatibility, resolves the release channel from `v<package.version>`, requires an exact release-body approval marker, rejects GitHub prerelease/channel mismatches, runs the local publish guard, and publishes with npm provenance only after the pre-publish checks pass.

The implemented workflow follows this shape:

```yaml
name: Publish aw-installer

on:
  release:
    types: [published]

permissions:
  contents: read
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: npm
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "24"
          registry-url: "https://registry.npmjs.org"
      - run: npm install -g npm@11.5.1
      - run: PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
      - run: PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
      - run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
      - run: npm pack --dry-run --json
      - run: npm run publish:dry-run --silent
      - run: npm publish --provenance --access public --tag "$AW_INSTALLER_RELEASE_CHANNEL"
```

The publish job intentionally remains stricter than `.github/workflows/ci.yml` about release metadata and registry authentication.

## Implemented Guard Shape

The first repository-side workflow preflight resolves these details:

- GitHub Release tag must exactly equal `v<package.version>`.
- `AW_INSTALLER_RELEASE_GIT_TAG` is populated from the release tag.
- `AW_INSTALLER_PUBLISH_APPROVED=1` remains required inside the publish job and is only set after `resolve-release-metadata.js` accepts the release metadata.
- the GitHub Release body must contain `aw-installer-publish-approved: v<package.version>`.
- prerelease GitHub Releases map to npm `next` or `canary`; stable GitHub Releases map to npm `latest`.
- the workflow rejects GitHub Releases whose prerelease flag and semver prerelease state disagree.
- `npm publish --provenance --access public --tag <channel>` uses the derived `AW_INSTALLER_RELEASE_CHANNEL`.

The root package metadata now binds the approval lock to the exact approved version, git tag, and channel through `approvedVersion`, `approvedGitTag`, and `approvedChannel`. Future versions must update those fields inside a separate approval worktrack before the local publish guard accepts a real publish.

## Approval Boundary

This page selects an operating model. It does not authorize:

- changing package version.
- publishing a future npm version.
- changing npm package Trusted Publisher settings.
- removing the manual publish repair path.

The repository-side workflow file exists, but a future Trusted Publishing run still needs the release-prep evidence and human approval encoded by the GitHub Release plus any `npm` environment protection. npm-side Trusted Publisher settings must be configured separately by the package owner before the workflow can authenticate through OIDC.

## Fallback

If Trusted Publishing setup is blocked, keep the manual maintainer publish path from [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md):

- exact release tuple is approved.
- guard inputs are set explicitly.
- `npm pack --dry-run --json` and `npm run publish:dry-run --silent` pass.
- manual `npm publish --tag <channel>` is run by the maintainer.
- registry npx smoke is rerun after publish.

Do not fall back to a long-lived `NPM_TOKEN` secret without a separate security review.
