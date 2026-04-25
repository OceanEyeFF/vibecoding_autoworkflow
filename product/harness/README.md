# Harness Product Source

`product/harness/` 是 `Harness` 的最小可执行源码根，负责承接后续 `operator -> skill -> subagent` 的 repo-local 实现层。

它不是 [../../docs/harness/README.md](../../docs/harness/README.md) 的替代物。

当前入口：

- [skills/README.md](./skills/README.md)：后续的 Harness canonical executable source
- [adapters/README.md](./adapters/README.md)：后续的 backend wrapper source

当前阶段：

- [../../docs/harness/README.md](../../docs/harness/README.md) 继续承接 doctrine、scope、artifact、governance 与 workflow truth
- `product/harness/` 只先建立干净骨架
- `memory-side` 与 `task-interface` 继续作为 Harness adjacent systems 保留文档合同层

规则：

- 新的 Harness executable source 应落在这里，而不是写回 `docs/harness/`
- repo-local deploy target 仍然是 `.claude/skills/`、`.agents/skills/` 与 `.opencode/skills/`
