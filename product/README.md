# Product

`product/` 是当前仓库第一块正式内容区，也是业务代码唯一源码根；这里承接 `Harness` 平台搭建与分发相关的业务源码。

当前主线包括：

- [harness/README.md](./harness/README.md)：`Harness` 的最小可执行源码根，承接后续 `operator -> skill -> subagent` 实现层
- [memory-side/README.md](./memory-side/README.md)：作为 Harness adjacent system 保留独立源码根
- [task-interface/README.md](./task-interface/README.md)：作为 Harness adjacent system 保留独立源码根

`docs/harness/` 继续承接 Harness doctrine 与运行协议真相层。
`product/harness/` 只承接新的 Harness executable source，不等于回填旧 `product/harness-operations/`。

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
- 新的 Harness ontology 仍落在 `docs/harness/`
- 新的 Harness executable source 应进入 `product/harness/`
