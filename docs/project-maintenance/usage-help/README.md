# Usage Help

`docs/project-maintenance/usage-help/` 只保存按 backend 聚合的 repo-local 使用帮助。这里不再按 `memory-side/` 或 `task-interface/` 再拆子树；每页只回答这个 backend 自己的 target、override 参数、smoke verify 口径和当前限制。

这里适合放：

- backend 特有的 global target 路径
- backend 特有的 root override 参数
- backend 特有的 smoke verify 口径
- backend 当前支持边界

这里不适合放：

- 通用 local / global deploy 流程
- 通用 source-of-truth 解释
- skill lifecycle 与 drift 诊断正文

## 按 backend 进入

| backend | 页面 | 主要差异 |
|---|---|---|
| `agents` | [codex.md](./codex.md) | `CODEX_HOME` / `--agents-root`、稳定 smoke verify |
| `claude` | [claude.md](./claude.md) | `~/.claude/skills` / `--claude-root`、稳定 smoke verify |
| `opencode` | [opencode.md](./opencode.md) | XDG target root、仅 `sync verify`，无稳定 smoke verify |

## 和 Deploy 文档的分工

- 通用 deploy 入口：看 [deploy/README.md](../deploy/README.md)
- 首次安装与最小更新：看 [deploy-runbook.md](../deploy/deploy-runbook.md)
- drift、`--prune`、故障诊断：看 [skill-deployment-maintenance.md](../deploy/skill-deployment-maintenance.md)
- `add / update / rename / remove`：看 [skill-lifecycle.md](../deploy/skill-lifecycle.md)
