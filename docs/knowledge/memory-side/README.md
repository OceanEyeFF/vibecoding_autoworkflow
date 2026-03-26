# Memory Side Knowledge

`docs/knowledge/memory-side/` 固定 `Memory Side` 的通用合同层，不直接描述 repo-local 部署步骤。

当前主线：

- [overview.md](./overview.md)
- [layer-boundary.md](./layer-boundary.md)
- [knowledge-base.md](./knowledge-base.md)
- [context-routing.md](./context-routing.md)
- [context-routing-rules.md](./context-routing-rules.md)
- [writeback-cleanup.md](./writeback-cleanup.md)
- [writeback-cleanup-rules.md](./writeback-cleanup-rules.md)
- [skill-agent-model.md](./skill-agent-model.md)
- [formats/context-routing-output-format.md](./formats/context-routing-output-format.md)
- [formats/writeback-cleanup-output-format.md](./formats/writeback-cleanup-output-format.md)
- [prompts/knowledge-base-adapter-prompt.md](./prompts/knowledge-base-adapter-prompt.md)
- [prompts/context-routing-adapter-prompt.md](./prompts/context-routing-adapter-prompt.md)
- [prompts/writeback-cleanup-adapter-prompt.md](./prompts/writeback-cleanup-adapter-prompt.md)
- [skills/knowledge-base-skill.md](./skills/knowledge-base-skill.md)
- [skills/context-routing-skill.md](./skills/context-routing-skill.md)
- [skills/writeback-cleanup-skill.md](./skills/writeback-cleanup-skill.md)

建议阅读顺序：

1. [overview.md](./overview.md)
2. [layer-boundary.md](./layer-boundary.md)
3. [knowledge-base.md](./knowledge-base.md)
4. [context-routing.md](./context-routing.md)
5. [writeback-cleanup.md](./writeback-cleanup.md)
6. [skill-agent-model.md](./skill-agent-model.md)

按主题下钻：

- `Knowledge Base`：先读 [knowledge-base.md](./knowledge-base.md)
- `Context Routing`：先读 [context-routing.md](./context-routing.md) 和 [context-routing-rules.md](./context-routing-rules.md)
- `Writeback & Cleanup`：先读 [writeback-cleanup.md](./writeback-cleanup.md) 和 [writeback-cleanup-rules.md](./writeback-cleanup-rules.md)
- 固定格式：读 `formats/`
- Prompt 合同：读 `prompts/`
- skill skeleton：读 `skills/`

这里不适合放：

- adapter 部署帮助
- research runner 使用说明
- repo-local mount 细节
