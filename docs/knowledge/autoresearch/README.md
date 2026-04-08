# Autoresearch Knowledge

`docs/knowledge/autoresearch/` 固定当前仓库里 `autoresearch` 这个 repo 模块的稳定入口，不新增 partition，也不重写现有 `operations / analysis / toolchain` 的职责边界。

当前默认 active 入口：

- [overview.md](./overview.md)
- [../../operations/autoresearch-minimal-loop.md](../../operations/autoresearch-minimal-loop.md)
- [../../operations/research-cli-help.md](../../operations/research-cli-help.md)
- [../../operations/tmp-exrepo-maintenance.md](../../operations/tmp-exrepo-maintenance.md)
- [../../operations/autoresearch-development-log.md](../../operations/autoresearch-development-log.md)
- [../../analysis/README.md](../../analysis/README.md)

补充模板：

- [Module Entry 模板](../foundations/module-entry-template.md)

建议阅读顺序：

1. [overview.md](./overview.md)
2. 如果任务是 repo-local 运行或维护，再按需进入 `docs/operations/` 的 active runbook：
   - [../../operations/autoresearch-minimal-loop.md](../../operations/autoresearch-minimal-loop.md)
   - [../../operations/research-cli-help.md](../../operations/research-cli-help.md)
   - [../../operations/tmp-exrepo-maintenance.md](../../operations/tmp-exrepo-maintenance.md)
   - [../../operations/autoresearch-development-log.md](../../operations/autoresearch-development-log.md)
3. 如果任务涉及 phase contract、当前 task-plan 或历史研究，再先回到 [../../analysis/README.md](../../analysis/README.md) 做分流。
4. 只有任务明确涉及实现或 CLI 内部接线时，再进入 [../../../toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)。
5. 要复核 closeout lineage / audit 或查阅异常处理规则时，再进入：
   - [../../operations/autoresearch-closeout-decision-rules.md](../../operations/autoresearch-closeout-decision-rules.md)
   - [../../operations/autoresearch-artifact-hygiene.md](../../operations/autoresearch-artifact-hygiene.md)
   - [../../operations/autoresearch-closeout-entry-layering.md](../../operations/autoresearch-closeout-entry-layering.md)
   - [../../operations/autoresearch-closeout-cleanup-and-retained-index.md](../../operations/autoresearch-closeout-cleanup-and-retained-index.md)
   - [../../operations/autoresearch-closeout-acceptance-gate.md](../../operations/autoresearch-closeout-acceptance-gate.md)

closeout 专项页继续保留审计价值，但不属于“今天先读什么”的默认阅读面。

这里适合放：

- `autoresearch` 的模块边界
- 稳定入口与跨层映射
- “去哪一层找什么”的主线说明
- 复用 [Module Entry 模板](../foundations/module-entry-template.md) 的模块入口

这里不适合放：

- repo-local 运行步骤细节
- 阶段性 task plan 正文
- `.autoworkflow/` 运行态本体
- `toolchain/` 实现细节复制件
