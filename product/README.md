# Product

`product/` 是当前仓库第一块正式内容区，也是业务代码唯一源码根；这里承接 `Harness` 平台搭建与分发相关的业务源码。

当前主线包括：

- [harness/README.md](./harness/README.md)：`Harness` 的最小可执行源码根，承接后续 `operator -> skill -> subagent` 实现层

受控辅助层：

- [.aw_template/README.md](./.aw_template/README.md)：repo-local execution template layer，承接可复制的 Harness artifact 模板，不承接 canonical truth

`docs/harness/` 继续承接 Harness doctrine 与运行协议真相层。
`product/harness/` 只承接 Harness executable source。
`memory-side` 与 `task-interface` 当前只保留在 `docs/harness/adjacent-systems/` 的合同层，不再保留 repo 内独立源码根。

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
- 新的 Harness ontology 仍落在 `docs/harness/`
- 新的 Harness executable source 应进入 `product/harness/`
- `.aw_template/` 只承接 execution templates，不是第四个源码根
