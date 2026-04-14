# Memory Side Knowledge

`docs/deployable-skills/memory-side/` 当前只保留迁移期兼容角色。

新的 Harness-first 入口已经迁到：

- [../../harness/adjacent-systems/memory-side/README.md](../../harness/adjacent-systems/memory-side/README.md)

当前这里仍保留：

- superseded 正文副本
- 旧路径引用仍依赖的兼容 wrapper
- [../../../product/memory-side/skills/README.md](../../../product/memory-side/skills/README.md)
- [../../../product/memory-side/skills/knowledge-base-skill/SKILL.md](../../../product/memory-side/skills/knowledge-base-skill/SKILL.md)
- [../../../product/memory-side/skills/context-routing-skill/SKILL.md](../../../product/memory-side/skills/context-routing-skill/SKILL.md)
- [../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md](../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md)

迁移约束：

- `Memory Side` 现在被表述为 Harness 的 adjacent system，而不是 Harness 本体
- 新的总纲、上位 ontology 与入口导航不再写回这里
- 在旧路径仍然存在期间，必须显式回链到新的 adjacent-system 入口

当前 legacy wrapper 入口包括：

- [overview.md](./overview.md)
- [layer-boundary.md](./layer-boundary.md)
- [knowledge-base.md](./knowledge-base.md)
- [context-routing.md](./context-routing.md)
- [context-routing-rules.md](./context-routing-rules.md)
- [writeback-cleanup.md](./writeback-cleanup.md)
- [writeback-cleanup-rules.md](./writeback-cleanup-rules.md)
- [skill-agent-model.md](./skill-agent-model.md)
- [formats/README.md](./formats/README.md)
- [formats/context-routing-output-format.md](./formats/context-routing-output-format.md)
- [formats/writeback-cleanup-output-format.md](./formats/writeback-cleanup-output-format.md)
