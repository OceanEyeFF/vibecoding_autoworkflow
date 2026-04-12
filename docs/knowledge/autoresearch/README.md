# Autoresearch Knowledge

`docs/knowledge/autoresearch/` 固定当前仓库里 `autoresearch` 这个 repo 模块的稳定入口，不新增 partition，也不重写现有 `operations / toolchain` 的职责边界。

当前默认入口只保留：

- [overview.md](./overview.md)
- [../../operations/README.md](../../operations/README.md)

建议阅读顺序：

1. [overview.md](./overview.md)
2. 如果任务是 repo-local 运行或维护，再先回到 [../../operations/README.md](../../operations/README.md) 分流到当前 runbook。
3. 如果任务涉及 research 合同或观测口径，再先回到 [../../operations/references/research-eval-contracts.md](../../operations/references/research-eval-contracts.md) 与 [../../operations/references/research-eval-observability.md](../../operations/references/research-eval-observability.md)。
4. 只有任务明确涉及实现或 CLI 内部接线时，再进入 [../../../toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)。
5. 只有任务明确落到实现或 CLI 内部接线时，再进入 [../../../toolchain/scripts/research/README.md](../../../toolchain/scripts/research/README.md)。

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
