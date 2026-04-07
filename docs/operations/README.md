# Operations

`docs/operations/` 只保存当前仓库的 repo-local runbook、部署说明和维护帮助，不保存跨仓库通用真相。

当前主线：

- `autoresearch-artifact-hygiene.md`
- `autoresearch-closeout-cleanup-and-retained-index.md`
- `autoresearch-closeout-entry-layering.md`
- `autoresearch-closeout-acceptance-gate.md`
- `autoresearch-minimal-loop.md`
- `autoresearch-closeout-decision-rules.md`
- `deploy-runbook.md`
- `branch-pr-governance.md`
- `review-verify-handbook.md`
- `path-governance-checks.md`
- `prompt-templates/README.md`
- `research-cli-help.md`
- `skill-deployment-maintenance.md`
- `tmp-exrepo-maintenance.md`
- `memory-side/codex-deployment-help.md`
- `memory-side/claude-adaptation-help.md`
- `memory-side/opencode-deployment-help.md`
- `task-interface/codex-deployment-help.md`
- `task-interface/claude-adaptation-help.md`
- `task-interface/opencode-deployment-help.md`

AI 默认阅读顺序以 [路径治理与 AI 告知](../knowledge/foundations/path-governance-ai-routing.md) 为准，并由 [Docs 文档治理基线](../knowledge/foundations/docs-governance.md) 约束文档层级。
本页只保留 repo-local 运维入口，不重复主线 `read_first/read_next/do_not_read_yet`。

这里适合放：

- 本仓库统一 deploy runbook
- 本仓库部署步骤
- repo-local 维护说明
- repo-local prompt / contract 模板
- runner 或 adapter 的使用帮助
- `prompt-templates/` 下模板必须回链 `docs/knowledge/` 主线入口

这里不适合放：

- 通用规则正文
- benchmark 结论
- 外部参考资料
