# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库的 repo-local deploy runbook 与维护说明。

这里适合放：

- 当前仓库的 deploy backend 总览
- repo-local / global target 的动作入口
- skill mounts 的维护、诊断与生命周期闭环

这里不适合放：

- canonical skill 真相正文
- backend 专属 runtime 细节
- research runner 或评测主流程

## 按任务进入

| 你要做什么 | 先看哪里 | 说明 |
|---|---|---|
| 首次本地挂载 skill | [deploy-runbook.md](./deploy-runbook.md) | 只看 Quick Start、target 对照和最小命令 |
| 首次全局安装 | [deploy-runbook.md](./deploy-runbook.md) | 先确认 global target，再执行最小安装步骤 |
| 日常同步已有 mounts | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 重点看 `verify -> deploy -> verify` |
| 排查 drift、stale target、坏链路 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 重点看故障信号、`--prune` 边界和处理顺序 |
| 新增 skill | [skill-lifecycle.md](./skill-lifecycle.md) | 看 `Add` 模板，确认 source、deploy 和 verify |
| 更新已有 skill | [skill-lifecycle.md](./skill-lifecycle.md) | 看 `Update` 模板，不必翻 maintenance 诊断细节 |
| 删除或重命名 skill | [skill-lifecycle.md](./skill-lifecycle.md) | 看 `Rename / Remove` 模板和 `--prune` 语义 |
| 只想看 backend 特有差异 | [usage-help/codex.md](../usage-help/codex.md)、[usage-help/claude.md](../usage-help/claude.md)、[usage-help/opencode.md](../usage-help/opencode.md) | 这些页面只保留 backend 特有 target、smoke verify 和限制 |

## 文档分工

- [deploy-runbook.md](./deploy-runbook.md)：首次安装、最小更新、backend / target 总览
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)：`verify`、drift、stale target、`--prune`、故障诊断
- [skill-lifecycle.md](./skill-lifecycle.md)：`add / update / rename / remove` 生命周期闭环
- `usage-help/`：backend 特有差异，不重复通用 deploy 流程
