# Product

`product/` 是当前仓库第一块正式内容区：业务代码唯一源码根。

当前主线包括：

- `memory-side/skills/`：canonical skill 源码
- `memory-side/adapters/`：Claude 与 Codex/OpenAI 的 adapter 源码
- `memory-side/adapters/opencode/`：OpenCode adapter 源码
- `memory-side/manifests/`：后续全局安装或市场分发的元数据预留位
- `task-interface/skills/`：Task Interface canonical skill 源码
- `task-interface/adapters/`：Task Interface 的 Claude、Codex/OpenAI 与 OpenCode adapter 源码

规则：

- 业务源码只改这里，不直接改 `.claude/`、`.agents/` 或 `.opencode/`
- `.claude/`、`.agents/` 与 `.opencode/` 只作为 repo-local deploy target
- 本地或全局部署统一走 `toolchain/scripts/deploy/adapter_deploy.py`
