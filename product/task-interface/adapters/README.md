# Task Interface Adapters

`product/task-interface/adapters/` 保存 `Task Interface` 的后端 adapter 源码，用来把同一套 canonical `task-contract-skill` 暴露给不同执行端。

当前主线：

- `agents/`：Codex / OpenAI adapter 源码
- `claude/`：Claude adapter 源码
- `opencode/`：OpenCode adapter 源码

AI 先读什么：

1. `product/task-interface/README.md`
2. `docs/knowledge/foundations/partition-model.md`
3. `docs/knowledge/task-interface/task-contract.md`
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
- 运行期状态
