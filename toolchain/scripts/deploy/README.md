# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：激活并复验当前 `agents` runtime target root

最小维护流：

1. 先跑 `verify`
2. 再跑 `local` 或 `global` endpoint
3. 最后再跑一次 `verify`

额外说明：

- `verify` 由 `adapter_deploy.py verify` 提供，用于检查缺失 root、错误路径类型和坏链路
- 当前接口只实现 `agents`
- `claude` 与 `opencode` 后续如需恢复，应先重定义 contract 再实现

回归测试入口：

```bash
python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

当前测试覆盖：

- local / global 首次激活到空 root
- 已有 root 的重复激活
- `verify` 的 missing / broken symlink / wrong root type 结构错误
