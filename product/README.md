# Product

`product/` 是当前仓库第一块正式内容区：业务代码唯一源码根。

当前主线包括：

- [memory-side/README.md](./memory-side/README.md)：Memory Side canonical skill 与 adapter 源码入口
- [task-interface/README.md](./task-interface/README.md)：Task Interface canonical skill 与 adapter 源码入口
- [harness-operations/README.md](./harness-operations/README.md)：Harness Operations canonical skill、adapter 与 manifests 入口

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
