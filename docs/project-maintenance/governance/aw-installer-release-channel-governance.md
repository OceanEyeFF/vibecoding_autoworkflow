---
title: "aw-installer Release Channel Governance"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---
# aw-installer Release Channel Governance

> 目的：定义 `aw-installer` 进入真实 npm release channel 前必须满足的发布准入规则，并记录当前 registry 事实。

本页属于 [Governance](./README.md) 路径簇。

管理 release channel/dist-tag 对应关系、publish 准入条件与当前 registry 事实；不管理 pre-publish tuple/packlist/doc freshness、smoke 执行、发布流程顺序与 wrapper/payload 边界。

## 当前 registry 事实

2026-05-07 已核对 git tag 与远程 release-line：

- `latest` -> `4.4.1`，`gitTag=v4.4.1=363c708`
- `next` -> `4.4.1-rc.1`，`gitTag=v4.4.1-rc.1=3b6b7f0`
- 历史 tag 也在仓库中：`v4.4.0=2a68869`、`v4.4.0-rc.0=0a1a281`、`v4.4.1-rc.0=827efea`

注意：上述 `latest`/`next` 由 release-line 上的 git tag 与 master/develop-main 推导而来，npm registry 的实际 dist-tag 写入由 publish workflow 完成；此页跟随 release commit 同步事实。

当前活跃工程分支 `develop-aw@be787c7` 的 root `package.json` 仍绑定 candidate `approvedVersion=4.4.1-rc.0`、`approvedGitTag=v4.4.1-rc.0`、`approvedChannel=next`，落后于已发布的 4.4.1 stable（位于 origin/master）。develop-aw 上的 approval lock 不可在常规工作中复用，必须先经 release-approval worktrack 与 develop-aw↔release-line 协调。

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
