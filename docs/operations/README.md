# Operations

`docs/operations/` 只保存当前仓库的 repo-local runbook、部署说明、维护帮助和 compatibility prompt shims，不保存跨仓库通用真相。

`operations/` 不长期承载 `suspended` 文档；暂停中的共享 runbook 应转为 `superseded`，非共享 scratch 应移出 `docs/`。

当前路径簇按对象类型分成三组：

1. `deploy/`：deploy / verify / maintenance 的入口簇
2. `prompt-templates/`：`product/harness-operations/` 的 compatibility prompt shims
3. `memory-side/`、`task-interface/`：partition-specific usage help

当前主线索引：

- [deploy/README.md](./deploy/README.md)
- [prompt-templates/README.md](./prompt-templates/README.md)
- [memory-side/README.md](./memory-side/README.md)
- [task-interface/README.md](./task-interface/README.md)

**Autoresearch default operations entry**

- `autoresearch-minimal-loop.md`（最小闭环 runbook，日常进入点）
- `research-cli-help.md`（Research CLI 的直接帮助页）
- `tmp-exrepo-maintenance.md`（TMP exrepo 的当前维护说明）

这些文档构成 `autoresearch` 的 daily operations runbook / maintenance entry。开发记录与 closeout 专页都不再属于默认 operations 入口；只有在需复核 lineage / audit 时才按需进入对应的 `superseded` 叶子页。

**Closeout / lineage appendix（非默认入口）**

- `autoresearch-closeout-decision-rules.md`
- `autoresearch-artifact-hygiene.md`
- `autoresearch-closeout-entry-layering.md`
- `autoresearch-closeout-cleanup-and-retained-index.md`
- `autoresearch-closeout-acceptance-gate.md`

在需要审计 closeout 记录或追踪例外判定时，再按需进入上述叶子页；默认阅读顺序仍然以前面的 daily runbook 为准。

AI 默认阅读顺序以 [路径治理与 AI 告知](../knowledge/foundations/path-governance-ai-routing.md) 为准，并由 [Docs 文档治理基线](../knowledge/foundations/docs-governance.md) 约束文档层级。
本页只保留 repo-local 运维入口，不重复主线 `read_first/read_next/do_not_read_yet`。

这里适合放：

- deploy / verify / maintenance 的 cluster index
- repo-local compatibility prompt shims
- partition-specific usage help
- repo-local runbook 的最小入口

这里不适合放：

- 通用规则正文
- benchmark 结论
- 外部参考资料
- 直接把 execution template 写成 truth layer
