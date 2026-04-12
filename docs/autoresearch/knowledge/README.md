# Autoresearch Knowledge

`docs/autoresearch/knowledge/` 固定当前仓库里 `autoresearch` 这个 repo 模块的稳定知识入口，不重写 `project-maintenance / toolchain` 的职责边界。

当前默认入口只保留：

- [overview.md](./overview.md)
- [../runbooks/README.md](../runbooks/README.md)
- [../references/README.md](../references/README.md)
- [../../project-maintenance/README.md](../../project-maintenance/README.md)

建议阅读顺序：

1. [overview.md](./overview.md)
2. 如果任务是 autoresearch repo-local 运行或维护，先读 [../runbooks/README.md](../runbooks/README.md)。
3. 如果任务还没确定属于哪个 `docs/project-maintenance/` 路径簇，再回到 [../../project-maintenance/README.md](../../project-maintenance/README.md) 做总分流。
4. 如果任务涉及 research 合同或观测口径，再先回到 [../references/research-eval-contracts.md](../references/research-eval-contracts.md) 与 [../references/research-eval-observability.md](../references/research-eval-observability.md)。
5. 只有任务明确涉及实现或 CLI 内部接线时，再进入 [../../../toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)。

本页只做模块知识入口，不重复 `project-maintenance/` 或 `toolchain/` 的正文。

这里适合放：

- `autoresearch` 的模块边界
- 稳定入口与跨层映射
- “去哪一层找什么”的主线说明
- 稳定模块入口本身

这里不适合放：

- repo-local 运行步骤细节
- 阶段性 task plan 正文
- `.autoworkflow/` 运行态本体
- `toolchain/` 实现细节复制件
