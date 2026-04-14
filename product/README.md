# Product

`product/` 是当前仓库第一块正式内容区，也是业务代码唯一源码根；这里承接 `Harness` 平台搭建与分发相关的业务源码。

当前主线包括：

- [memory-side/README.md](./memory-side/README.md)：支撑 `Harness` 的 `Memory Side` 内部实现面与源码入口
- [task-interface/README.md](./task-interface/README.md)：支撑 `Harness` 的 `Task Interface` 内部实现面与源码入口
- [harness-operations/README.md](./harness-operations/README.md)：承接 `Harness` 平台搭建与分发的源码入口

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
