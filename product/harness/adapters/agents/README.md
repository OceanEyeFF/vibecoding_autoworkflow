# Harness Agents Adapters

`product/harness/adapters/agents/` 承接 `agents` backend 的 adapter source。

当前阶段：

- 已落当前 `agents` Harness skills 的 canonical-copy payload descriptor source
- payload 负责声明 `agents` target 应复制哪些 canonical skill 文件
- payload 不承接 deploy target runtime state

当前入口：

- [skills/README.md](./skills/README.md)：`agents` skill payload descriptor source

这里适合放：

- `agents` backend 的 payload descriptor
- backend-specific 的 payload 元数据
- 后续 B4 要消费的 source layer

这里不适合放：

- canonical skill truth
- repo-local / global deploy target
- install state、verify 结果或 runtime hash
