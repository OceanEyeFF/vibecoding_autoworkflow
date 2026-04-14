# Memory Side

`Memory Side` 是 Harness 的 adjacent system，不是 Harness 本体。

当前 canonical 合同入口：

- [overview.md](./overview.md)
- [layer-boundary.md](./layer-boundary.md)
- [skill-agent-model.md](./skill-agent-model.md)
- [knowledge-base.md](./knowledge-base.md)
- [context-routing.md](./context-routing.md)
- [context-routing-rules.md](./context-routing-rules.md)
- [writeback-cleanup.md](./writeback-cleanup.md)
- [writeback-cleanup-rules.md](./writeback-cleanup-rules.md)
- [formats/README.md](./formats/README.md)

对应源码入口：

- [../../../../product/memory-side/README.md](../../../../product/memory-side/README.md)
- [../../../../product/memory-side/skills/README.md](../../../../product/memory-side/skills/README.md)
- [../../../../product/memory-side/skills/knowledge-base-skill/SKILL.md](../../../../product/memory-side/skills/knowledge-base-skill/SKILL.md)
- [../../../../product/memory-side/skills/context-routing-skill/SKILL.md](../../../../product/memory-side/skills/context-routing-skill/SKILL.md)
- [../../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md](../../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md)

迁移说明：

- legacy wrapper 仍保留在 [../../../deployable-skills/memory-side/README.md](../../../deployable-skills/memory-side/README.md)
- `docs/deployable-skills/memory-side/*` 现在只用于兼容旧路径，不再承接 canonical 正文
