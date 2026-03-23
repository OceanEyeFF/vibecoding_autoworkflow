# Operations

`docs/operations/` 只保存当前仓库的 repo-local runbook、部署说明和维护帮助，不保存跨仓库通用真相。

当前主线：

- `path-governance-checks.md`
- `memory-side/codex-deployment-help.md`
- `memory-side/claude-adaptation-help.md`
- `task-interface/codex-deployment-help.md`
- `task-interface/claude-adaptation-help.md`

AI 先读什么：

1. `docs/knowledge/foundations/root-directory-layering.md`
2. `docs/knowledge/foundations/partition-model.md`
3. 对应 partition 的知识主线，例如 `memory-side/` 或 `task-interface/`
4. 目标主题下的操作说明

暂时不要先读什么：

- `docs/reference/`
- `docs/archive/`
- `.agents/`
- `.claude/`

这里适合放：

- 本仓库部署步骤
- repo-local 维护说明
- runner 或 adapter 的使用帮助

这里不适合放：

- 通用规则正文
- benchmark 结论
- 外部参考资料
