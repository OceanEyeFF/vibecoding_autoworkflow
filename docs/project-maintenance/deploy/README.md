# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库的 operator-facing deploy / verify / maintenance 文档。这里解释 repo-local 与 global target 怎么装、怎么复验、怎么诊断 drift，但不承接 canonical skill 合同正文，也不恢复旧 `docs/operations/*` 的 backend 分叉结构。

这里适合放：

- 当前仓库的 deploy backend、target 和入口命令
- 首次安装与已有 mounts 的最小操作路径
- `verify`、drift、`--prune` 与 lifecycle 同步闭环
- 当前仍存在的 canonical skill source 如何同步到 repo-local / global target

这里不适合放：

- canonical skill 真相正文
- 按 `memory-side/`、`task-interface/` 再拆的 backend help 子树
- 已删除 harness skill/source 的历史部署细节
- research runner 或评测主流程

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我第一次给某个 backend 装 skill | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留首次 local/global install、target 对照和最小复验 |
| 我已有 mounts，只想更新或复验 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 按 `verify -> deploy -> verify` 做 |
| 我看到 drift / stale / `wrong-target-type` | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 这里集中解释错误信号、local/global drift 口径和 `--prune` |
| 我在新增、改名、删除 skill source | [skill-lifecycle.md](./skill-lifecycle.md) | 这里回答 source 改哪、deploy 跟什么、docs 何时同步 |
| 我只想看 `agents / claude / opencode` 差异 | [usage-help/README.md](../usage-help/README.md) | backend-specific 页面只保留 target、smoke verify 和限制 |

## 当前 source 边界

- 当前可部署 source 只在 `product/memory-side/` 与 `product/task-interface/`
- `adapter_deploy.py` 直接读取 `product/<partition>/adapters/<backend>/skills/`
- `docs/harness/` 继续承接 Harness doctrine，但当前不对应 repo 内独立的 harness skill/source 分区

## 页面职责

- [deploy-runbook.md](./deploy-runbook.md)
  quick start。回答首次安装、repo-local / global target 对照与最小复验。
- [skill-lifecycle.md](./skill-lifecycle.md)
  lifecycle。回答 add / update / rename / remove 的 source of truth、deploy follow-up 与 writeback。
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
  maintenance / diagnosis。回答只读 `verify`、drift 类型、`--prune` 边界，以及 local/global verify 的不同关注点。
- `usage-help/`
  backend-specific。只解释 `agents`、`claude`、`opencode` 的差异，不重复通用 deploy 流程。
