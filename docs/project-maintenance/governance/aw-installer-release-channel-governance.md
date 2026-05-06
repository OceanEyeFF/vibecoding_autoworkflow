---
title: "aw-installer Release Channel Governance"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# aw-installer Release Channel Governance

> 目的：定义 `aw-installer` 进入真实 npm release channel 前必须满足的发布准入规则，并记录当前 registry 事实。

本页属于 [Governance](./README.md) 路径簇。

管理 release channel/dist-tag 对应关系、publish 准入条件与当前 registry 事实；不管理 pre-publish tuple/packlist/doc freshness、smoke 执行、发布流程顺序与 wrapper/payload 边界。

## 当前 registry 事实

2026-05-06 已核对 npm registry：

- `latest` -> `4.4.0`，`gitHead=2a68869d558bd538d9e9867f94b574caa797fdaf`
- `next` -> `4.4.0-rc.0`，`gitHead=0a1a281a75af3937c4c92b18134db08e8e1b2097`

当前 checkout 的 root `package.json` 已绑定待发布 candidate `approvedVersion=4.4.1-rc.0`、`approvedGitTag=v4.4.1-rc.0`、`approvedChannel=next`。`4.4.1-rc.0` 仍需经过 pre-publish、merge PR、GitHub Release、publish workflow 与 registry verification 后才可写入 published registry fact；不得复用已发布版本。

## Channel 对应关系

| channel | npm dist-tag | version form |
| --- | --- | --- |
| `latest` | `latest` | stable semver，例如 `1.2.3` |
| `next` | `next` | `alpha` / `beta` / `rc` prerelease |
| `canary` | `canary` | 含 `canary` 段的 prerelease |

RC 试用 operator-facing selector 必须显式使用 `aw-installer@next`；裸 `aw-installer` 仍按 `latest` 解析。

## 真实 Publish 准入

必须同时满足：package name 为 `aw-installer`，version 是合法 semver（非 `-local`），tuple（`approvedVersion`/`approvedGitTag`/`approvedChannel`）一致，`AW_INSTALLER_RELEASE_GIT_TAG=v<version>`，GitHub Release body 含 `aw-installer-publish-approved: v<version>`，`CI=true`，`AW_INSTALLER_PUBLISH_APPROVED=1`，channel/dist-tag 一致（`latest`仅 stable，`next`仅 alpha/beta/rc，`canary`仅含 canary 的 prerelease）。`npm run publish:dry-run --silent` 不构成 publish 授权。

## 审批锁

publish 前 root `package.json` 必须绑定唯一 approval lock：

```json
{
  "realPublishApproval": "approved",
  "approvedVersion": "<package.version>",
  "approvedGitTag": "v<package.version>",
  "approvedChannel": "<latest|next|canary>"
}
```

approval lock 只能在显式 release-approval worktrack 中修改。

## 相关文档

- [aw-installer Release Standard Flow](./aw-installer-release-standard-flow.md)
- [aw-installer Release Operation Model](./aw-installer-release-operation-model.md)
- [aw-installer Pre-Publish Governance](./aw-installer-pre-publish-governance.md)
- [npx Command Test Execution](../testing/npx-command-test-execution.md)
