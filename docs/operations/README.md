# Operations

`docs/operations/` 只保存当前仓库的 repo-local runbook、部署说明和维护帮助，不保存跨仓库通用真相。

当前主线：

- `autoresearch-minimal-loop.md`
- `autoresearch-closeout-decision-rules.md`
- `deploy-runbook.md`
- `path-governance-checks.md`
- `research-cli-help.md`
- `skill-deployment-maintenance.md`
- `tmp-exrepo-maintenance.md`
- `memory-side/codex-deployment-help.md`
- `memory-side/claude-adaptation-help.md`
- `memory-side/opencode-deployment-help.md`
- `task-interface/codex-deployment-help.md`
- `task-interface/claude-adaptation-help.md`
- `task-interface/opencode-deployment-help.md`

AI 先读什么：

1. `docs/knowledge/README.md`
2. `docs/knowledge/foundations/README.md`
3. `docs/knowledge/foundations/docs-governance.md`
4. 对应 partition 的知识主线，例如 `docs/knowledge/memory-side/README.md` 或 `docs/knowledge/task-interface/README.md`
5. `deploy-runbook.md` 或其他目标主题下的操作说明

暂时不要先读什么：

- `docs/reference/`
- `docs/archive/`
- `.agents/`
- `.claude/`
- `.opencode/`

这里适合放：

- 本仓库统一 deploy runbook
- 本仓库部署步骤
- repo-local 维护说明
- runner 或 adapter 的使用帮助

这里不适合放：

- 通用规则正文
- benchmark 结论
- 外部参考资料
