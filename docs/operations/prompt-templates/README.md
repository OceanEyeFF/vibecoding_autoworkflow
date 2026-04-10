# Prompt Templates Compatibility Shims

`docs/operations/prompt-templates/` 只保留历史路径兼容入口，不承载 canonical prompt 语义。

canonical source 在：

- [product/harness-operations/README.md](../../../product/harness-operations/README.md)
- [docs/knowledge/README.md](../../knowledge/README.md)

当前 shim 映射：

- `execution-contract-template.md` -> [execution-contract-template](../../../product/harness-operations/skills/execution-contract-template/references/prompt.md)
- `task-planning-contract.md` -> [task-planning-contract](../../../product/harness-operations/skills/task-planning-contract/references/prompt.md)
- `simple-subagent-workflow.md` -> [simple-workflow](../../../product/harness-operations/skills/simple-workflow/references/prompt.md)
- `strict-subagent-workflow.md` -> [strict-workflow](../../../product/harness-operations/skills/strict-workflow/references/prompt.md)
- `task-list-subagent-workflow.md` -> [task-list-workflow](../../../product/harness-operations/skills/task-list-workflow/references/prompt.md)
- `review-loop-code-review.md` -> [review-loop-workflow](../../../product/harness-operations/skills/review-loop-workflow/references/prompt.md)
- `repo-governance-evaluation.md` -> [repo-governance-evaluation](../../../product/harness-operations/skills/repo-governance-evaluation/references/prompt.md)
- `harness-contract-template.md` -> [harness-contract-shape](../../../product/harness-operations/skills/harness-contract-shape/references/prompt.md)

如果你在找 deploy / verify / maintenance，请先读 [../deploy/README.md](../deploy/README.md)。
