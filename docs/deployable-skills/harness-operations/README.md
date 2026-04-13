# Harness Operations Knowledge

`docs/deployable-skills/harness-operations/` 固定 `Harness Operations` 的 doctrine、控制面边界与可复用合同，不直接承载 repo-local runtime 绑定或部署步骤。

当前主线入口：

- [Harness指导思想.md](./Harness指导思想.md)

Canonical skill package 入口：

- [../../../product/harness-operations/README.md](../../../product/harness-operations/README.md)
- [../../../product/harness-operations/skills/README.md](../../../product/harness-operations/skills/README.md)
- [../../../product/harness-operations/skills/harness-standard.md](../../../product/harness-operations/skills/harness-standard.md)

建议阅读顺序：

1. [Harness指导思想.md](./Harness指导思想.md)
2. 只有需要看 canonical skill source 时，再进入 [../../../product/harness-operations/skills/README.md](../../../product/harness-operations/skills/README.md)
3. 只有需要看 repo-local runtime 与 deploy 时，再进入 [../../project-maintenance/README.md](../../project-maintenance/README.md)

补充入口：

- 如果需要上游执行基线，先读 [../task-interface/task-contract.md](../task-interface/task-contract.md)
- 如果需要 canonical source 总入口，先读 [../../../product/harness-operations/README.md](../../../product/harness-operations/README.md)

这里适合放：

- `Harness Operations` 的 doctrine 与控制面定义
- `Repo / Worktrack` 分层合同
- `Gate / Evidence / Authority` 的通用语义

这里不适合放：

- repo-local state file 细节
- adapter deploy runbook
- 单次任务临时流程记录
