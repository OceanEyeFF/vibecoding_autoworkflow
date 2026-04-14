# Product

`product/` 是当前仓库第一块正式内容区，也是业务代码唯一源码根；这里承接 `Harness` 平台搭建与分发相关的业务源码。

当前主线包括：

- [memory-side/README.md](./memory-side/README.md)：作为 Harness adjacent system 保留独立源码根
- [task-interface/README.md](./task-interface/README.md)：作为 Harness adjacent system 保留独立源码根

当前不再保留独立的 `product/harness/` 或 `product/harness-operations/` 源码分区。
Harness doctrine 继续承接在 `docs/harness/`，可执行 skill source 只保留上述两个 adjacent-system 分区。

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
- 新的 Harness ontology 落在 `docs/harness/`，不要再为 Harness doctrine 新开 `product/` 分区
