# Usage Help

`docs/project-maintenance/usage-help/` 只保存按 backend 聚合的 repo-local 使用帮助。

这里适合放：

- backend 特有的 global target 路径
- backend 特有的 smoke verify 口径
- backend 限制与参数差异

这里不适合放：

- 通用 local / global deploy 流程
- 通用 source-of-truth 解释
- skill 生命周期维护说明

## 按 backend 进入

| 你要看什么 | 先看哪里 | 说明 |
|---|---|---|
| Codex / OpenAI 侧差异 | [codex.md](./codex.md) | 看 `agents` backend 的 global target、smoke verify 和参数差异 |
| Claude 侧差异 | [claude.md](./claude.md) | 看 `claude` backend 的 global target、smoke verify 和参数差异 |
| OpenCode 侧差异 | [opencode.md](./opencode.md) | 看 `opencode` backend 当前支持边界和 XDG target 差异 |

## 和 Deploy 文档的分工

- 通用 deploy 入口：看 [deploy/README.md](../deploy/README.md)
- 首次安装与最小更新：看 [deploy-runbook.md](../deploy/deploy-runbook.md)
- drift、`--prune`、故障诊断：看 [skill-deployment-maintenance.md](../deploy/skill-deployment-maintenance.md)
- `add / update / rename / remove`：看 [skill-lifecycle.md](../deploy/skill-lifecycle.md)
