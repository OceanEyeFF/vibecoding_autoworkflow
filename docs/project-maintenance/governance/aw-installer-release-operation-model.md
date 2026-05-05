---
title: "aw-installer Release Operation Model"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# aw-installer Release Operation Model

> Purpose: record the selected publish operating model for `aw-installer`: GitHub Release `published` plus npm Trusted Publishing.

This page belongs to [Governance](./README.md).

## Control Signal

- decision_status: repository-workflow-preflight-implemented
- selected_operation_model: GitHub Release `published` trigger with npm Trusted Publishing
- selected_auth_model: npm Trusted Publisher through GitHub Actions OIDC
- long_lived_npm_token_required: false
- publish_workflow_implemented: true
- publish_workflow_path: `.github/workflows/publish.yml`
- future_npm_publish_allowed_by_this_page: false

## Decision

Future `aw-installer` publish implementation should use:

- GitHub Actions as the CI carrier
- GitHub Release `published` as the publish trigger
- npm Trusted Publishing as the registry authentication path
- optional GitHub Environment protection named `npm`

This keeps a human approval moment at Release publication while avoiding long-lived npm token handling.

## Why Release Published

| Option | Fit | Decision |
| --- | --- | --- |
| tag push | simple, but easy to create accidentally | fallback |
| GitHub Release `published` | explicit operator action with release notes | preferred |
| main branch auto release | useful for mature auto-release libraries | not selected |

## Trusted Publishing Setup

npm-side package settings must configure:

| Field | Value |
| --- | --- |
| Provider | GitHub Actions |
| Organization or user | repository owner |
| Repository | this repository |
| Workflow filename | `publish.yml` |
| Environment name | `npm` if environment protection is used |

The workflow lives at:

```text
.github/workflows/publish.yml
```

## Workflow Shape

The repository-side workflow preflight now lives at `.github/workflows/publish.yml`. It:

- triggers only on GitHub Release `published`
- grants `id-token: write`
- uses the `npm` GitHub Environment
- installs npm `11.5.1` on Node `24`
- resolves the release channel from `v<package.version>`
- requires the exact release-body approval marker
- rejects prerelease/channel mismatches
- runs the local publish guard
- publishes with npm provenance only after pre-publish checks pass

The workflow file itself is the authority.

## Release Procedure Navigation

For a future release:

1. complete [aw-installer Pre-Publish Governance](./aw-installer-pre-publish-governance.md)
2. confirm [aw-installer Release Channel Governance](./aw-installer-release-channel-governance.md)
3. follow [aw-installer Release Standard Flow](./aw-installer-release-standard-flow.md)
4. rerun [npx Command Test Execution](../testing/npx-command-test-execution.md) after publish

## Approval Boundary

This page selects an operating model. It does not authorize:

- changing package version
- publishing a future npm version
- changing npm package Trusted Publisher settings
- bypassing release-approval worktracks

## Fallback

If Trusted Publishing setup is blocked, keep the manual maintainer publish path only after the same release tuple is explicitly approved and all pre-publish checks pass.
