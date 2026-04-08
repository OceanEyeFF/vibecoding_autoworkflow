# Knowledge

`docs/knowledge/` 是当前仓库的 canonical truth 主线，负责承载稳定规则、分层合同和能力边界。

当前子层与模块入口：

- [foundations/README.md](./foundations/README.md)：跨分区基础合同与根级边界
- [memory-side/README.md](./memory-side/README.md)：`Knowledge Base / Context Routing / Writeback & Cleanup`
- [task-interface/README.md](./task-interface/README.md)：`Task Contract`
- [autoresearch/README.md](./autoresearch/README.md)：当前仓库 `autoresearch` repo 模块的稳定入口与跨层映射

  `autoresearch` 的默认 active 入口只保留 `docs/knowledge/autoresearch/overview.md`、`docs/operations/autoresearch-minimal-loop.md`、`docs/operations/research-cli-help.md`、`docs/operations/tmp-exrepo-maintenance.md` 与 `docs/analysis/README.md`；其他 closeout 规则页仅在复核 lineage / audit 时进入。

先建立治理边界，再进入子层：

- [foundations/path-governance-ai-routing.md](./foundations/path-governance-ai-routing.md)
- [foundations/docs-governance.md](./foundations/docs-governance.md)

建议阅读顺序由 [foundations/path-governance-ai-routing.md](./foundations/path-governance-ai-routing.md) 统一定义。
本页只保留 `knowledge/` 的模块入口，避免重复 `read_first/read_next/do_not_read_yet` 的主线合同。

这里适合放：

- 当前有效的规则正文
- 稳定阅读入口
- 分区边界和固定格式合同
- 当前仓库关键 repo 模块的入口页

这里不适合放：

- repo-local runbook
- 阶段性研究记录
- 外部参考资料
- 未准入主线的想法
