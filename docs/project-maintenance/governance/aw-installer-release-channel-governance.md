---
title: "aw-installer Release Channel Governance"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# aw-installer Release Channel Governance

> 目的：定义 `aw-installer` 进入真实 npm release channel 前必须满足的发布准入规则，并记录当前 registry 事实。

本页属于 [Governance](./README.md) 路径簇。

## 本页管理什么

- release channel 与 dist-tag 的对应关系
- 真实 publish 的最小准入条件
- 当前 registry 事实

## 本页不管理什么

- publish 前 tuple、packlist、docs freshness 与 approval lock：见 [aw-installer Pre-Publish Governance](./aw-installer-pre-publish-governance.md)
- local `.tgz` / registry smoke 执行：见 [npx Command Test Execution](../testing/npx-command-test-execution.md)
- merge PR、GitHub Release、publish workflow 顺序：见 [aw-installer Release Standard Flow](./aw-installer-release-standard-flow.md)
- wrapper 语义、payload/source/target 边界：见 `deploy/` 下的实现合同页

## 当前 registry 事实

- `next` 当前指向 `0.4.3-rc.2`
- `latest` 当前指向 `0.4.0-rc.1`
- 当前 checkout 的本地 candidate 是 `4.4.0-rc.0`
- 本地 candidate 在 publish workflow 成功前不是 registry artifact
- 已发布 npm version 不可复用；同一 immutable version 不得重复 publish

## Channel 对应关系

| channel | npm dist-tag | version form |
| --- | --- | --- |
| `latest` | `latest` | stable semver，例如 `1.2.3` |
| `next` | `next` | `alpha` / `beta` / `rc` prerelease |
| `canary` | `canary` | 含 `canary` 段的 prerelease |

对于 RC 试用，operator-facing selector 必须显式使用 `aw-installer@next`；裸 `aw-installer` 仍按 `latest` 解析。

## 真实 Publish 准入

真实 publish 必须同时满足：

- package name 是批准的 public identity：`aw-installer`
- package version 是合法 semver，且不是 `0.0.0-local` 或其他 `-local`
- `approvedVersion`、`approvedGitTag`、`approvedChannel` 与当前 tuple 完全一致
- `AW_INSTALLER_RELEASE_GIT_TAG` 等于 `v<package.version>`
- GitHub Release body 包含 `aw-installer-publish-approved: v<package.version>`
- `CI=true`
- `AW_INSTALLER_PUBLISH_APPROVED=1`
- channel 与 dist-tag 一致
- `latest` 只能用于 stable semver
- `next` 只能用于 `alpha` / `beta` / `rc`
- `canary` 只能用于含 `canary` 的 prerelease

`npm run publish:dry-run --silent` 只验证包面与 guard，不构成 publish 授权。

## 审批锁

真实 publish 前，root `package.json` 必须绑定唯一 approval lock：

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
