# Memory Side Skills

`product/memory-side/skills/` 是 canonical skill 源码入口，不是 deploy target。

当前主线：

- `knowledge-base-skill/`
- `context-routing-skill/`
- `writeback-cleanup-skill/`

AI 先读什么：

1. `product/memory-side/README.md`
2. `docs/knowledge/memory-side/layer-boundary.md`
3. `docs/knowledge/memory-side/skill-agent-model.md`
4. 再进入目标 skill 的 `SKILL.md`

暂时不要先读什么：

- 根目录 `.agents/`
- 根目录 `.claude/`
- adapter wrapper，除非当前任务明确涉及后端适配

这里适合放：

- canonical skill 源码
- skill 的最小 references

这里不适合放：

- repo-local 挂载结果
- 后端专属 interface metadata
- 运行期状态
