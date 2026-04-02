# Knowledge

`docs/knowledge/` 是当前仓库的 canonical truth 主线，负责承载稳定规则、分层合同和能力边界。

当前子层与模块入口：

- `foundations/`：跨分区基础合同与根级边界
- `memory-side/`：`Knowledge Base / Context Routing / Writeback & Cleanup`
- `task-interface/`：`Task Contract`
- `autoresearch/`：当前仓库 `autoresearch` repo 模块的稳定入口与跨层映射

先建立治理边界，再进入子层：

- [foundations/path-governance-ai-routing.md](./foundations/path-governance-ai-routing.md)
- [foundations/docs-governance.md](./foundations/docs-governance.md)

建议阅读顺序：

1. [foundations/README.md](./foundations/README.md)
2. [memory-side/README.md](./memory-side/README.md)
3. [task-interface/README.md](./task-interface/README.md)
4. 任务明确涉及 `autoresearch` 时，再读 [autoresearch/README.md](./autoresearch/README.md)

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
