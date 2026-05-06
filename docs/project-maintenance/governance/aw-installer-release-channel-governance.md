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

2026-05-07 已核对 npm registry：

- `latest` -> `4.4.0`，`gitHead=2a68869d558bd538d9e9867f94b574caa797fdaf`
- `next` -> `4.4.1-rc.1`，`gitHead=f41599b27220c7c9719fe0ad3c6bb94606197727`

当前 checkout 的 root `package.json` 绑定 `approvedVersion=4.4.1`、`approvedGitTag=v4.4.1`、`approvedChannel=latest`。`4.4.1` 在发布前 registry 查询为未发布；发布后必须用 registry 查询结果回写 `latest` 事实。

## Channel 对应关系

| channel | npm dist-tag | version form |
| --- | --- | --- |
| `latest` | `latest` | stable semver，例如 `1.2.3` |
| `next` | `next` | `alpha` / `beta` / `rc` prerelease |
| `canary` | `canary` | 含 `canary` 段的 prerelease |

stable operator-facing selector 使用默认 `aw-installer`；RC 试用 selector 必须显式使用 `aw-installer@next`。

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
