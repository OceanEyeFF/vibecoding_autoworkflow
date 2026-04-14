# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库的 operator-facing deploy / verify / maintenance 文档。这里解释 repo-local 与 global target 怎么装、怎么复验、怎么诊断 drift，但不承接 canonical skill 合同正文，也不恢复旧 `docs/operations/*` 的 backend 分叉结构。

这里适合放：

- 当前仓库的 deploy backend、target 和入口命令
- 首次安装与已有 mounts 的最小操作路径
- `verify`、drift、stale、`--prune` 与 lifecycle 同步闭环
- `harness-operations` 的特殊 build/deploy/verify 模型

这里不适合放：

- canonical skill 真相正文
- 按 `memory-side/`、`task-interface/` 再拆的 backend help 子树
- research runner 或评测主流程

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我第一次给某个 backend 装 skill | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留首次 local/global install、target 对照和最小复验 |
| 我已有 mounts，只想更新或复验 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 先看 `build` 何时需要，再按 `verify -> deploy -> verify` 做 |
| 我看到 drift / stale / `wrong-target-type` / `missing-build-source` | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 这里集中解释错误信号、local/global drift 口径和 `--prune` |
| 我在新增、改名、删除 skill source | [skill-lifecycle.md](./skill-lifecycle.md) | 这里回答 source 改哪、deploy 跟什么、docs 何时同步 |
| 我只想看 `agents / claude / opencode` 差异 | [usage-help/README.md](../usage-help/README.md) | backend-specific 页面只保留 target、smoke verify 和限制 |

## 当前迁移状态

- Harness-first ontology 已迁到 [../../harness/README.md](../../harness/README.md) 与 [../../../product/harness/README.md](../../../product/harness/README.md)
- 当前实际 deploy/build source 仍保留在 `product/harness-operations/`
- 因此本目录继续描述 `harness-operations` 的 deploy 行为，但不把它再写成 Harness 本体定义

## 页面职责

- [deploy-runbook.md](./deploy-runbook.md)
  quick start。回答首次安装、repo-local / global target 对照、harness 为什么要先 build。
- [skill-lifecycle.md](./skill-lifecycle.md)
  lifecycle。回答 add / update / rename / remove 的 source of truth、deploy follow-up 与 writeback。
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
  maintenance / diagnosis。回答只读 `verify`、drift 类型、`--prune` 边界，以及 local/global verify 的不同关注点。
- `usage-help/`
  backend-specific。只解释 `agents`、`claude`、`opencode` 的差异，不重复通用 deploy 流程。

## Harness 特殊模型

`harness-operations` 不是普通 thin-wrapper source：

- canonical source 在 `product/harness-operations/skills/<skill>/prompt.md`
- shared body 在 `product/harness-operations/skills/harness-standard.md`
- backend source 在 `product/harness-operations/adapters/<backend>/skills/<skill>/header.yaml`
- `build` 负责组装最终 `SKILL.md`
- `local` / `global` deploy 会为 harness 自动刷新当前 backend 的 assembled source
- `verify` 保持只读，不自动 build

首次安装先看 [deploy-runbook.md](./deploy-runbook.md)；已有 mounts 的 drift 与 build-source 问题看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)。
