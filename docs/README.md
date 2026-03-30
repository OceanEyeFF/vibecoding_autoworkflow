# docs 文档入口

> 本目录用于承载项目的补充文档与可复用运行模板。

## 目录导航

- `analysis/`：分析结论与失败模式沉淀。
- `operations/`：运行手册（runbook）与执行模板。

## Prompt Templates（repo-side contract）

用于给 Codex / Claude / 其他 Code Agent 提供最小可执行、可审计的执行流程约束：

- [轻量版：simple-subagent-workflow](operations/prompt-templates/simple-subagent-workflow.md)
- [严格版：strict-subagent-workflow](operations/prompt-templates/strict-subagent-workflow.md)
- [执行合同模板：execution-contract-template](operations/prompt-templates/execution-contract-template.md)
- [代码审查闭环：review-loop-code-review](operations/prompt-templates/review-loop-code-review.md)
- [任务规划合同：task-planning-contract](operations/prompt-templates/task-planning-contract.md)
- [多任务执行：task-list-subagent-workflow](operations/prompt-templates/task-list-subagent-workflow.md)
