# Repo Evolution Workflow Source

这里承接 `repo-evolution` family 的正式 workflow source。

当前 extracted source：

- [standard-worktrack.workflow.md](./standard-worktrack.workflow.md)
- [task-batching.pattern.md](./task-batching.pattern.md)
- [review-repair.loop.md](./review-repair.loop.md)

当前阶段：

- legacy workflow prompt 仍保留在 `product/harness-operations/skills/`
- family 级稳定语义已开始回收到本目录
- profile/variant 约束继续放在 [../../profiles/README.md](../../profiles/README.md)

当前回收映射：

| legacy asset | 处理方式 | 当前定位 |
|---|---|---|
| `task-planning-contract` | `split` | 为 batching / task matrix 提供 planning contract |
| `task-list-workflow` | `downgrade` | `standard-worktrack.workflow.md` + `task-batching.pattern.md` + profile variant |
| `review-loop-workflow` | `deprecate` | `review-repair.loop.md` |

迁移约束：

- 在真正迁移 prompt/source 前，不要直接移动 deploy source
- backend-specific prompt 编排仍留在 legacy source
- family 级稳定语义优先在本目录沉淀，再决定后续 adapter/source 迁移
