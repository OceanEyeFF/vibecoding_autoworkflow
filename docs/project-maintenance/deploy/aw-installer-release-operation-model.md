---
title: "aw-installer Release Operation Model"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Release Operation Model

> Purpose: decide the next `aw-installer` publish operating model after the first manual RC publish and registry npx smoke. This page recommends GitHub Release `published` plus npm Trusted Publishing for future release implementation, but does not itself enable a publish workflow or authorize a future npm publish.

This page belongs to [Deploy Runbooks](./README.md). It builds on [aw-installer Release Channel Contract](./release-channel-contract.md), [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md), and [aw-installer Registry npx Smoke](./aw-installer-registry-npx-smoke.md).

## Control Signal

- decision_status: selected-design
- selected_operation_model: GitHub Release `published` trigger with npm Trusted Publishing
- selected_auth_model: npm Trusted Publisher through GitHub Actions OIDC
- long_lived_npm_token_required: false
- publish_workflow_implemented: false
- future_npm_publish_allowed_by_this_page: false
- required_human_approval_action: create or publish a GitHub Release for an already reviewed version/tag
- recommended_workflow_filename: `publish.yml`
- recommended_github_environment: `npm`
- recommended_node_version_for_publish_job: `24`
- implementation_requires_followup_worktrack: true

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

Implementation should start from this shape, but this page intentionally does not add the workflow:

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
      - uses: actions/checkout@v6
      - uses: actions/setup-node@v6
        with:
          node-version: "24"
          registry-url: "https://registry.npmjs.org"
      - run: npm ci
      - run: PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/path_governance_check.py
      - run: PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/test/governance_semantic_check.py
      - run: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
      - run: npm pack --dry-run --json
      - run: npm run publish:dry-run --silent
      - run: npm publish --provenance --access public
```

Implementation may reuse or factor common checks from `.github/workflows/ci.yml`, but the publish job must remain stricter about release metadata and registry authentication.

## Required Guards Before Implementation

Before adding `publish.yml`, decide and test these details:

- whether GitHub Release tag must exactly equal `v<package.version>`.
- how `AW_INSTALLER_RELEASE_GIT_TAG` is populated in CI.
- whether `AW_INSTALLER_PUBLISH_APPROVED=1` remains required for Trusted Publishing.
- whether `awInstallerRelease.realPublishApproval` should remain a tracked package lock, become a workflow-only release input, or be replaced by GitHub Environment approval.
- how prerelease GitHub Releases map to npm `next` and stable GitHub Releases map to npm `latest`.
- whether the workflow should reject GitHub Releases whose prerelease flag and semver prerelease state disagree.
- whether `npm publish --provenance --access public --tag <channel>` should compute `<channel>` from semver or from explicit release metadata.

## Approval Boundary

This page selects an operating model. It does not authorize:

- adding `.github/workflows/publish.yml`.
- changing package version.
- publishing a future npm version.
- changing npm package Trusted Publisher settings.
- removing the manual publish repair path.

A follow-up implementation worktrack should be opened before any workflow file is added. That worktrack must include a non-publishing dry-run or simulation path where possible, plus a final approval boundary before the first Trusted Publishing run.

## Fallback

If Trusted Publishing setup is blocked, keep the manual maintainer publish path from [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md):

- exact release tuple is approved.
- guard inputs are set explicitly.
- `npm pack --dry-run --json` and `npm run publish:dry-run --silent` pass.
- manual `npm publish --tag <channel>` is run by the maintainer.
- registry npx smoke is rerun after publish.

Do not fall back to a long-lived `NPM_TOKEN` secret without a separate security review.
