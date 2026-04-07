# Memory Side Adapters

`product/memory-side/adapters/` 保存后端 adapter 源码，用来把同一套 canonical skill 语义暴露给不同执行端。

当前主线：

- `agents/`：Codex / OpenAI adapter 源码
- `claude/`：Claude adapter 源码
- `opencode/`：OpenCode adapter 源码

路由权威以 `docs/knowledge/foundations/path-governance-ai-routing.md` 为准。
当 authority 已确认进入 backend wrapper layer 时，本目录只建议继续读取：

1. `product/memory-side/README.md`
2. 对应 backend 下的目标 skill `SKILL.md`
3. 仅在确实需要接口元数据时，再读 `agents/openai.yaml` 之类 backend metadata

这里适合放：

- backend wrapper 源码
- 后端适配说明

这里不适合放：

- 项目真相正文
- repo-local deploy target
- benchmark 结果

说明：

- `product/memory-side/adapters/agents/` 是源码目录，不等于根目录 `.agents/`
