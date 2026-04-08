# Harness Operations Adapters

`product/harness-operations/adapters/` 保存 `Harness Operations` 的后端 adapter 源码，用来把同一套 canonical skills 暴露给不同执行端。

当前主线：

- `agents/`：Codex / OpenAI adapter 源码
- `claude/`：Claude adapter 源码
- `opencode/`：OpenCode adapter 源码

路由权威以 `docs/knowledge/foundations/path-governance-ai-routing.md` 为准。
当 authority 已确认进入 backend wrapper layer 时，本目录只建议继续读取：

1. `product/harness-operations/README.md`
2. 对应 backend 下 skill 的 `SKILL.md`
3. 仅在确实需要接口元数据时，再读 backend metadata

这里适合放：

- backend wrapper 源码
- 后端适配说明

这里不适合放：

- 项目真相正文
- repo-local deploy target
- 运行期状态
