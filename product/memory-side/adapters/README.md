# Memory Side Adapters

`product/memory-side/adapters/` 保存后端 adapter 源码，用来把同一套 canonical skill 语义暴露给不同执行端。

当前主线：

- `agents/`：Codex / OpenAI adapter 源码
- `claude/`：Claude adapter 源码
- `opencode/`：OpenCode adapter 源码

AI 先读什么：

1. `product/memory-side/README.md`
2. `docs/knowledge/memory-side/layer-boundary.md`
3. `docs/knowledge/memory-side/skill-agent-model.md`
4. 再选择 `agents/`、`claude/` 或 `opencode/` 进入对应 wrapper

暂时不要先读什么：

- 根目录 `.agents/`
- 根目录 `.claude/`
- 根目录 `.opencode/`
- `agents/openai.yaml` 这类 interface metadata，除非当前任务明确需要它

这里适合放：

- backend wrapper 源码
- 后端适配说明

这里不适合放：

- 项目真相正文
- repo-local deploy target
- benchmark 结果

说明：

- `product/memory-side/adapters/agents/` 是源码目录，不等于根目录 `.agents/`
