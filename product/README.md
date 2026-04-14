# Product

`product/` 是当前仓库第一块正式内容区，也是业务代码唯一源码根；这里承接 `Harness` 平台搭建与分发相关的业务源码。

当前主线包括：

- [harness/README.md](./harness/README.md)：Harness-first 源码叙事入口与目标分层
- [memory-side/README.md](./memory-side/README.md)：作为 Harness adjacent system 保留独立源码根
- [task-interface/README.md](./task-interface/README.md)：作为 Harness adjacent system 保留独立源码根
- [harness-operations/README.md](./harness-operations/README.md)：迁移期保留的 legacy Harness workflow 资产与 adapter source

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
- 新的 Harness ontology 先落到 `product/harness/`，旧 `product/harness-operations/` 先按可回收资产保留，不直接推翻
