# Memory Side Usage Help

`docs/operations/memory-side/` 只保存 `Memory Side` 在当前仓库里的 repo-local 使用帮助，不保存 `Memory Side` 的主线真相正文。

建议阅读顺序：

1. [Deploy / Verify / Maintenance](../deploy/README.md)
2. [Codex Memory Side Repo-local Adapter 部署帮助](./codex-deployment-help.md)
3. [Claude Memory Side Repo-local Adapter 适配帮助](./claude-adaptation-help.md)
4. [OpenCode Memory Side Repo-local Adapter 部署帮助](./opencode-deployment-help.md)

这组页面适合回答：

- 这个 partition 怎么部署到不同 backend
- repo-local target 怎么验
- smoke verify 是否支持
- 哪些地方是 backend-specific 使用帮助

这组页面不适合回答：

- `Memory Side` 的 canonical truth
- canonical skill 的语义正文
- 任何 deploy target 自身的实现细节

相关入口：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
