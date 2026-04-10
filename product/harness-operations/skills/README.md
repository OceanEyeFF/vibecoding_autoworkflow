# Harness Operations Skills

`product/harness-operations/skills/` 是 `Harness Operations` 的 canonical skill 源码入口，不是 deploy target。

当前主线：

- `execution-contract-template/`
- `harness-contract-shape/`
- `repo-governance-evaluation/`
- `review-loop-workflow/`
- `simple-workflow/`
- `strict-workflow/`
- `task-list-workflow/`
- `task-planning-contract/`

路由权威以 `AGENTS.md` 为准。
当 authority 已确认进入 canonical skill source layer 时，本目录只建议继续读取：

1. `product/harness-operations/README.md`
2. 对应 skill 的 `SKILL.md`
3. 对应 skill 的 `references/entrypoints.md`

这里适合放：

- Harness Operations canonical skill 源码
- skill 的最小 references

这里不适合放：

- repo-local 挂载结果
- 后端专属 interface metadata
- 运行期状态
