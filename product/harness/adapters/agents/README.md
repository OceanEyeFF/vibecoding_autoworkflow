# Harness Agents Adapters

`product/harness/adapters/agents/` 承接 `agents` backend 的 adapter source。

当前阶段：

- 只落 first-wave skills 的 thin-shell payload source
- payload 负责把 `agents` runtime entry 绑定回 canonical skill source
- payload 不复制 canonical workflow 正文，也不承接 deploy target runtime state

当前入口：

- [skills/README.md](./skills/README.md)：首发 `agents` skill payload source

这里适合放：

- `agents` backend 的 thin-shell wrapper
- backend-specific 的 payload 元数据
- 后续 B4 要消费的 source layer

这里不适合放：

- canonical skill truth
- repo-local / global deploy target
- install state、verify 结果或 runtime hash
