# Usage Help

`docs/project-maintenance/usage-help/` 只保存按 backend 聚合的使用帮助。这里不再按 `memory-side/` 或 `task-interface/` 再拆子树；每页只回答这个 backend 自己的 target root 解析、override 参数、验证口径和当前限制。

这里适合放：

- backend 特有的 target root 解析方式
- backend 特有的 root override 参数
- backend 特有的验证口径
- backend 当前支持边界

这里不适合放：

- 通用三步 deploy 主流程
- 通用 source-of-truth 解释
- skill lifecycle 与 drift 诊断正文

## 按 backend 进入

| backend | 页面 | 主要差异 |
|---|---|---|
| `agents` | [codex.md](./codex.md) | 默认 `.agents/skills/` / 可选 `--agents-root`、deploy verify 与 Codex Harness manual run |
| `claude` | [claude.md](./claude.md) | Claude runtime 路径约定、稳定 smoke verify、临时 repo 冷启动 runbook；当前仓库不提供 `claude` deploy adapter CLI |
| `opencode` | [opencode.md](./opencode.md) | OpenCode runtime 路径约定、仅 `sync verify`；当前仓库不提供 `opencode` deploy adapter CLI |

## 和 Deploy 文档的分工

- 通用 deploy 入口：看 [deploy/README.md](../deploy/README.md)
- destructive reinstall 主流程：看 [deploy-runbook.md](../deploy/deploy-runbook.md)
- drift、冲突扫描、故障诊断：看 [skill-deployment-maintenance.md](../deploy/skill-deployment-maintenance.md)
- `add / update / rename / remove`：看 [skill-lifecycle.md](../deploy/skill-lifecycle.md)
