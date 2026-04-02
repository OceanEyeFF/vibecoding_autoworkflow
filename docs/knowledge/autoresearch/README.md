# Autoresearch Knowledge

`docs/knowledge/autoresearch/` 固定当前仓库里 `autoresearch` 这个 repo 模块的稳定入口，不新增 partition，也不重写现有 `operations / analysis / toolchain` 的职责边界。

当前主线：

- [overview.md](./overview.md)

建议阅读顺序：

1. [overview.md](./overview.md)
2. [../../../toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)
3. 按任务进入 `docs/operations/`：
   - [../../operations/autoresearch-minimal-loop.md](../../operations/autoresearch-minimal-loop.md)
   - [../../operations/research-cli-help.md](../../operations/research-cli-help.md)
   - [../../operations/tmp-exrepo-maintenance.md](../../operations/tmp-exrepo-maintenance.md)
   - [../../operations/autoresearch-closeout-decision-rules.md](../../operations/autoresearch-closeout-decision-rules.md)
4. 只有任务明确涉及阶段合同、当前规划或 closeout 追踪时，再进入 `docs/analysis/` 中的 `autoresearch-*.md`

这里适合放：

- `autoresearch` 的模块边界
- 稳定入口与跨层映射
- “去哪一层找什么”的主线说明

这里不适合放：

- repo-local 运行步骤细节
- 阶段性 task plan 正文
- `.autoworkflow/` 运行态本体
- `toolchain/` 实现细节复制件
