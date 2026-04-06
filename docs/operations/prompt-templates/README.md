# Prompt Templates

`docs/operations/prompt-templates/` 承接当前仓库可复用的 repo-local prompt / contract 模板。

这些模板的定位：

- 约束执行流程、边界和验证
- 给 repo-local harness 或人工协作提供统一结构
- 作为 `docs/knowledge/` 主线真相的消费层，不替代 knowledge 层规则正文

当前模板：

- `execution-contract-template.md`
- `task-planning-contract.md`
- `simple-subagent-workflow.md`
- `strict-subagent-workflow.md`
- `task-list-subagent-workflow.md`
- `review-loop-code-review.md`
- `repo-governance-evaluation.md`
- `harness-contract-template.md`

使用顺序建议：

1. 先读 `docs/knowledge/README.md`
2. 再读对应 foundations / partition 文档
3. 需要固定执行结构时，再进入本目录选择模板

这里不适合放：

- canonical truth
- deploy target 下的 skill 源码
- repo-local state 样本
