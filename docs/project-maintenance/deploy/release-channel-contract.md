---
title: "aw-installer Release Channel Contract"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Release Channel Contract

> 目的：定义 `aw-installer` 从本地 `.tgz` / publish dry-run 进入真实 npm release channel 前必须满足的发布准入合同。本文不授权真实 `npm publish`。

本页属于 [Deploy Runbooks](./README.md) 系列，并承接 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 的发布准入部分。运行时 payload provenance 与 update trust boundary 由 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md) 承接。

## 当前状态

- 根目录 `package.json` 是 self-contained `aw-installer` package envelope；`aw-installer` 是当前 working package name / proposed package identity，不表示最终公开 npm 包名已经批准。
- 当前版本仍是 `0.0.0-local`，真实 publish 必须被拒绝。
- `npm pack --dry-run --json`、`npm run publish:dry-run --silent` 和根 `.tgz` smoke 只证明包面和运行入口，不等于发布授权。
- `prepublishOnly` guard 位于 `toolchain/scripts/deploy/bin/check-root-publish.js`，负责在真实 publish 前执行机器准入检查。

## Release Channels

| channel | npm dist-tag | version form | purpose |
|---|---|---|---|
| `latest` | `latest` | stable semver, for example `1.2.3` | 默认稳定发布 |
| `next` | `next` | prerelease semver with `alpha`, `beta`, or `rc`, for example `1.3.0-beta.1` | 预发布验证 |
| `canary` | `canary` | prerelease semver containing `canary`, for example `1.3.0-canary.20260427` | 短期实验验证 |

真实 publish 时，`AW_INSTALLER_RELEASE_CHANNEL` 必须与 npm dist-tag 一致。未显式设置 npm dist-tag 时，npm 默认按 `latest` 处理，因此非 `latest` channel 必须显式传入对应 tag。

## Publish Readiness Gate

真实 publish 必须同时满足：

- package name matches the separately approved public package identity; before that approval, `aw-installer` is only the working package name / proposed package identity used by the local package envelope and release-candidate docs.
- package version is valid semver and is not `0.0.0-local` or any `-local` version.
- `CI=true`.
- `AW_INSTALLER_PUBLISH_APPROVED=1`.
- `AW_INSTALLER_RELEASE_CHANNEL` is one of `latest`, `next`, or `canary`.
- npm dist-tag matches `AW_INSTALLER_RELEASE_CHANNEL`.
- `AW_INSTALLER_RELEASE_GIT_TAG` equals `v<package.version>`.
- latest channel uses stable versions only.
- next channel uses `alpha`, `beta`, or `rc` prerelease versions.
- canary channel includes a `canary` prerelease segment.

The guard intentionally allows publish dry-run with the local version so maintainers can keep validating package surface without authorizing a release.

## Required Evidence Before Approval

Before setting `AW_INSTALLER_PUBLISH_APPROVED=1`, collect:

- clean worktree on the intended release checkpoint.
- root `npm pack --dry-run --json`.
- root `npm run publish:dry-run --silent`.
- root `.tgz` smoke from an isolated target repo.
- closeout gate evidence for the release-prep worktrack.
- release notes or changelog summary for the published version.
- rollback or deprecation plan, at minimum naming the npm dist-tag correction or deprecation path.

## Out Of Scope

- npm account setup, tokens, 2FA, or registry credential storage.
- GitHub Actions release workflow implementation.
- Runtime payload provenance, remote update, self-update, signature verification, or rollback implementation; those remain governed by [Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md).
- Running `npm publish`.

## Operator Notes

Use dry-run while the package remains local:

```bash
npm run publish:dry-run --silent
```

Real publish requires a separate approval boundary and explicit release metadata. Example shape:

```bash
CI=true \
AW_INSTALLER_PUBLISH_APPROVED=1 \
AW_INSTALLER_RELEASE_CHANNEL=next \
AW_INSTALLER_RELEASE_GIT_TAG=v1.3.0-beta.1 \
npm publish --tag next
```

This command is an example of the guard contract, not a release instruction for the current repository state.
