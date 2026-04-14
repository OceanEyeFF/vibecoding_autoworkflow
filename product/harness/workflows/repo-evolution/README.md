# Repo Evolution Workflow Source

这里预留给 `repo-evolution` family 的 workflow source。

当前阶段：

- legacy workflow 资产仍主要位于 `product/harness-operations/skills/`
- 新的 family/profile 语义以 `docs/harness/workflow-families/repo-evolution/` 为准

当前回收映射：

| legacy asset | 处理方式 | 当前定位 |
|---|---|---|
| `task-planning-contract` | `split` | workflow planning 输入，不再单独冒充上位 family |
| `task-list-workflow` | `downgrade` | repo-evolution family 下的 workflow/profile 变体 |
| `review-loop-workflow` | `deprecate` | legacy workflow asset，可回收其 staged review / gate 经验 |

迁移约束：

- 在真正迁移 prompt/source 前，不要直接移动 deploy source
- 先明确 family 语义，再决定哪些 legacy prompt 片段值得回收
