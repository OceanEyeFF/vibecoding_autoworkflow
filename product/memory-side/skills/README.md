# Memory Side Skills

`product/memory-side/skills/` 是 canonical skill 源码入口，不是 deploy target。

当前主线：

- `knowledge-base-skill/`
- `context-routing-skill/`
- `writeback-cleanup-skill/`

路由权威以 `AGENTS.md` 为准。
当 authority 已确认进入 canonical skill source layer 时，本目录只建议继续读取：

1. `product/memory-side/README.md`
2. 目标 skill 的 `SKILL.md`
3. 该 skill 的 `references/entrypoints.md`

这里适合放：

- canonical skill 源码
- skill 的最小 references

这里不适合放：

- repo-local 挂载结果
- 后端专属 interface metadata
- 运行期状态
