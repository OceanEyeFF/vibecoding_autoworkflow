# Prompt Templates Compatibility Shims

`docs/operations/prompt-templates/` 不再承接 canonical prompt 语义。它现在只保留旧路径兼容入口，用来把历史链接和 repo-local 使用提示回链到 `product/harness-operations/`。

当前定位：

- 保留历史路径与旧文件名，避免迁移期间断链
- 给 repo-local 审查、维护和知识回链提供稳定 shim
- 明确提醒读者：真正的 skill 语义、prompt body、bindings 与 wrappers 已迁到 `product/harness-operations/`

这里不再承担：

- canonical truth
- primary prompt semantics
- backend wrapper 源码
- repo-local state 样本

如果你在找的是 deploy / verify / maintenance，先读 [Deploy / Verify / Maintenance](../deploy/README.md)。
如果你在找的是 partition-specific usage help，先读 [Memory Side Usage Help](../memory-side/README.md) 或 [Task Interface Usage Help](../task-interface/README.md)。
如果你在找的是 Harness Operations 的 canonical source，先读 [Harness Operations Product Source](../../../product/harness-operations/README.md)。

当前 shim 映射：

- `execution-contract-template.md` -> [execution-contract-template](../../../product/harness-operations/skills/execution-contract-template/references/prompt.md)
- `task-planning-contract.md` -> [task-planning-contract](../../../product/harness-operations/skills/task-planning-contract/references/prompt.md)
- `simple-subagent-workflow.md` -> [simple-workflow](../../../product/harness-operations/skills/simple-workflow/references/prompt.md)
- `strict-subagent-workflow.md` -> [strict-workflow](../../../product/harness-operations/skills/strict-workflow/references/prompt.md)
- `task-list-subagent-workflow.md` -> [task-list-workflow](../../../product/harness-operations/skills/task-list-workflow/references/prompt.md)
- `review-loop-code-review.md` -> [review-loop-workflow](../../../product/harness-operations/skills/review-loop-workflow/references/prompt.md)
- `repo-governance-evaluation.md` -> [repo-governance-evaluation](../../../product/harness-operations/skills/repo-governance-evaluation/references/prompt.md)
- `harness-contract-template.md` -> [harness-contract-shape](../../../product/harness-operations/skills/harness-contract-shape/references/prompt.md)

使用顺序建议：

1. 先读 [docs/knowledge/README.md](../../knowledge/README.md)
2. 再读 [Harness Operations Product Source](../../../product/harness-operations/README.md)
3. 最后按对象进入对应 skill 的 `SKILL.md` 与 `references/prompt.md`

治理要求：

- shim 只能做兼容指针，不得再次定义 canonical 语义
- 如果 prompt 语义变化，先改 `product/harness-operations/`
- 如果旧路径映射变化，再回写本目录的 shim
- shim 文档仍需保留 `docs/knowledge/` 主线回链
