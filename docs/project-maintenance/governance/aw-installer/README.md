---
title: "aw-installer Release Governance"
status: active
updated: 2026-05-17
owner: aw-kernel
last_verified: 2026-05-17
---
# aw-installer Release Governance

`docs/project-maintenance/governance/aw-installer/` 集中管理 aw-installer 的发布操作模型、渠道准入、发布流程、发布前就绪检查与外部试用治理。

上游入口见 [../README.md](../README.md) 发布治理分组。

## 目录

| 文档 | 只管理什么 |
| --- | --- |
| [aw-installer-release-operation-model.md](./aw-installer-release-operation-model.md) | 已选择的发布操作模型（GitHub Release + npm Trusted Publishing） |
| [aw-installer-release-channel-governance.md](./aw-installer-release-channel-governance.md) | npm 发布渠道准入规则与当前 registry 事实 |
| [aw-installer-release-standard-flow.md](./aw-installer-release-standard-flow.md) | 候选版本从 PR 合并到发布后验证的完整流程 |
| [aw-installer-pre-publish-governance.md](./aw-installer-pre-publish-governance.md) | 发布前必须满足的最小就绪边界 |
| [aw-installer-external-trial-governance.md](./aw-installer-external-trial-governance.md) | 外部试用的目标列表模板与反馈契约 |

## 按场景进入

| 场景 | 入口 |
| --- | --- |
| 确认当前发布模型 | [aw-installer-release-operation-model.md](./aw-installer-release-operation-model.md) |
| 发布前检查就绪状态 | [aw-installer-pre-publish-governance.md](./aw-installer-pre-publish-governance.md) |
| 执行候选版本发布 | [aw-installer-release-standard-flow.md](./aw-installer-release-standard-flow.md) |
| 管理 npm 渠道准入 | [aw-installer-release-channel-governance.md](./aw-installer-release-channel-governance.md) |
| 管理外部试用目标 | [aw-installer-external-trial-governance.md](./aw-installer-external-trial-governance.md) |
