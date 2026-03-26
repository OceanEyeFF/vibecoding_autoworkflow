# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：把 `product/` 下的 adapter 源码部署到 repo-local mount 或全局技能目录，并提供 deploy target 校验与清理能力

最小维护流：

1. 先跑 `verify`
2. 再跑 `local` 或 `global` 部署
3. 最后再跑一次 `verify`

额外说明：

- `verify` 用于检查缺失 mount、陈旧 target、坏链路和错误路径类型
- `--prune` 用于在部署时清理已经没有 source 对应关系的 target
- 该目录只负责部署维护，不负责 research runner
