---
title: "aw-installer Release Channel Contract"
status: active
updated: 2026-04-28
owner: aw-kernel
last_verified: 2026-04-28
---
# aw-installer Release Channel Contract

> 目的：定义 `aw-installer` 从本地 `.tgz` / publish dry-run 进入真实 npm release channel 前必须满足的发布准入合同，并记录首个 RC publish 的 registry 事实。本文不授权后续稳定发布、未来 npm publish 或 npm-side Trusted Publisher 设置变更。

本页属于 [Deploy Runbooks](./README.md) 系列，并承接 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 的发布准入部分。发布操作模型由 [aw-installer Release Operation Model](./aw-installer-release-operation-model.md) 承接；运行时 payload provenance 与 update trust boundary 由 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md) 承接。

## 当前状态

- 根目录 `package.json` 是 self-contained `aw-installer` package envelope；`aw-installer` 是已批准的 unscoped public package identity。`aw-installer@0.4.0-rc.1` 已发布到 npm registry。
- 当前 release metadata 使用 `0.4.0-rc.1` 作为首个 `0.4.x` RC checkpoint；`P0-019` 已跨过真实 publish 审批边界，并把 package metadata 设置为 `awInstallerRelease.realPublishApproval=approved`。后续 publish 仍必须同时满足本文的环境、tag、dist-tag、CI 与 registry 准入条件。
- `npm pack --dry-run --json`、`npm run publish:dry-run --silent` 和根 `.tgz` smoke 只证明包面和运行入口，不等于发布授权。
- `prepublishOnly` guard 位于 `toolchain/scripts/deploy/bin/check-root-publish.js`，负责在真实 publish 前执行机器准入检查。
- repository-side GitHub Release `published` workflow preflight 位于 `.github/workflows/publish.yml`；它把 release tag、GitHub prerelease 状态、release-body approval marker、derived channel、local publish guard 和 npm provenance publish 串起来，但仍不替代未来 release-prep 审批或 npm-side Trusted Publisher 设置。
- 首个 npm package version 的 registry 事实是 `next: 0.4.0-rc.1` 与 `latest: 0.4.0-rc.1` 同时存在；`npm dist-tag rm aw-installer latest` 对唯一版本返回 `E400 Bad Request`。P0-020 registry smoke 验证后，面向 RC 试用的主路径可以使用裸 `npx aw-installer`，需要显式证明 RC channel 时使用 `aw-installer@next`。

## Release Channels

| channel | npm dist-tag | version form | purpose |
|---|---|---|---|
| `latest` | `latest` | stable semver, for example `1.2.3` | 默认稳定发布 |
| `next` | `next` | prerelease semver with `alpha`, `beta`, or `rc`, for example `1.3.0-beta.1` | 预发布验证 |
| `canary` | `canary` | prerelease semver containing `canary`, for example `1.3.0-canary.20260427` | 短期实验验证 |

真实 publish 时，release channel 必须与 npm dist-tag 一致。release channel 可由 `AW_INSTALLER_RELEASE_GIT_TAG=v<package.version>` 推导，也可由 `AW_INSTALLER_RELEASE_CHANNEL` 显式给出。未显式设置 npm dist-tag 时，npm 默认按 `latest` 处理，因此非 `latest` channel 必须显式传入对应 tag。

Npm 的 `latest` tag 是默认安装解析入口：未指定版本或 tag 的 `npm install <pkg>`、`npm exec --package <pkg>`、`npx <pkg>` 会解析 `latest`。`next` 是普通 dist-tag，常被项目用作 upcoming / prerelease stream；除 `latest` 外，npm 本身不赋予其他 tag 特殊语义。见 npm 官方 `dist-tag` 文档：`https://docs.npmjs.com/cli/v8/commands/npm-dist-tag/`。

## Publish Readiness Gate

真实 publish 必须同时满足：

- package name is the approved unscoped public package identity `aw-installer`.
- package version is valid semver and is not `0.0.0-local` or any `-local` version.
- package metadata has `awInstallerRelease.realPublishApproval=approved`, changed only inside the explicit real-publish approval worktrack.
- `CI=true`.
- `AW_INSTALLER_PUBLISH_APPROVED=1`.
- derived or explicit release channel is one of `latest`, `next`, or `canary`.
- npm dist-tag matches the derived or explicit release channel.
- `AW_INSTALLER_RELEASE_GIT_TAG` equals `v<package.version>`.
- GitHub Release body includes `aw-installer-publish-approved: v<package.version>`.
- latest channel uses stable versions only.
- next channel uses `alpha`, `beta`, or `rc` prerelease versions.
- canary channel includes a `canary` prerelease segment.

The guard intentionally allows publish dry-run before approval so maintainers can keep validating package surface without authorizing a release.

## Required Evidence Before Approval

Before setting `AW_INSTALLER_PUBLISH_APPROVED=1`, changing `awInstallerRelease.realPublishApproval` to `approved`, or running real `npm publish`, collect:

- clean worktree on the intended release checkpoint.
- root `npm pack --dry-run --json`.
- root `npm run publish:dry-run --silent`.
- root `.tgz` smoke from an isolated target repo.
- closeout gate evidence for the release-prep worktrack.
- release notes or changelog summary for the published version.
- rollback or deprecation plan, at minimum naming the npm dist-tag correction or deprecation path.

## Out Of Scope

- npm account setup, tokens, 2FA, or registry credential storage.
- npm Trusted Publisher settings mutation or the first future Trusted Publishing run; the repository-side workflow preflight is tracked in [aw-installer Release Operation Model](./aw-installer-release-operation-model.md), but npm-side setup remains a separate operator action.
- Runtime payload provenance, remote update, self-update, signature verification, or rollback implementation; those remain governed by [Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md).
- Running future `npm publish` outside an explicit approval worktrack.

## Operator Notes

Use dry-run before real publish approval and execution:

```bash
npm run publish:dry-run --silent
```

Real publish requires a separate approval boundary, an explicit tracked metadata-lock change, and explicit release metadata. The approved `P0-019` RC command shape is:

```text
CI=true
AW_INSTALLER_PUBLISH_APPROVED=1
AW_INSTALLER_RELEASE_GIT_TAG=v0.4.0-rc.1
npm publish --tag next
```

This command was used for `P0-019` and published `aw-installer@0.4.0-rc.1`. Registry evidence shows the approved `next` tag exists; because this is the only package version, npm also exposes `latest` for the same RC. Treat that `latest` alias as a registry default for the initial package, not as stable-release approval. P0-020 may use bare `npx aw-installer` as the current RC trial path after registry smoke evidence; use `aw-installer@next` when explicit RC-channel pinning is required.
