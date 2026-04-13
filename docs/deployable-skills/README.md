# Deployable Skills

`docs/deployable-skills/` 是当前仓库 deployable skills 的 canonical truth 主线，负责承载稳定规则、分层合同、格式与能力边界。

当前子层与模块入口：

- [harness-operations/README.md](./harness-operations/README.md)：`Harness Operations`
- [memory-side/README.md](./memory-side/README.md)：`Knowledge Base / Context Routing / Writeback & Cleanup`
- [task-interface/README.md](./task-interface/README.md)：`Task Contract`

当前结构化承接入口：

- [harness-operations/Harness指导思想.md](./harness-operations/Harness指导思想.md)
- [memory-side/formats/context-routing-output-format.md](./memory-side/formats/context-routing-output-format.md)
- [memory-side/formats/writeback-cleanup-output-format.md](./memory-side/formats/writeback-cleanup-output-format.md)
- [task-interface/task-contract.md](./task-interface/task-contract.md)

先建立治理边界，再进入子层：

- [AGENTS.md](../../AGENTS.md)

建议阅读顺序由 [AGENTS.md](../../AGENTS.md) 统一定义。
本页只保留 deployable skills 的模块入口，避免重复 `read_first/read_next/do_not_read_yet` 的主线合同。

这里适合放：

- 当前有效的技能合同正文
- 稳定阅读入口
- 输出格式、规则与能力边界说明
- 跨 backend 可复用的能力边界

这里不适合放：

- repo-local runbook
- 模块专属 repo-local references/runbooks
- 项目级治理流程
- 阶段性研究记录
- 外部参考资料
- 未准入主线的想法
