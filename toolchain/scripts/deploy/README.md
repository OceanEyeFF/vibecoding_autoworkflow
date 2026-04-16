# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：激活并复验当前 `agents` runtime target root
- `aw_scaffold.py`：从 `product/.aw_template/` 生成 `.aw/` 运行样例，并校验模板最小结构
- `product/harness/adapters/agents/skills/`：B3 的 `agents` thin-shell payload source；当前仍由文档和契约测试约束，尚未进入 `adapter_deploy.py` 同步逻辑

最小维护流：

1. 先跑 `verify`
2. 再跑 `local` 或 `global` endpoint
3. 最后再跑一次 `verify`

`.aw_template` 相关最小流：

1. 先跑 `python3 toolchain/scripts/deploy/aw_scaffold.py validate --profile first-wave-minimal`
2. 再跑 `python3 toolchain/scripts/deploy/aw_scaffold.py generate --profile first-wave-minimal --output-root /tmp/demo-aw`
3. 如需覆盖已有样例，再显式加 `--force`

额外说明：

- `verify` 由 `adapter_deploy.py verify` 提供，用于检查缺失 root、错误路径类型和坏链路
- 当前接口只实现 `agents`
- 当前 B3 payload source 已存在，但 deploy 脚本仍只管理 target root；内容同步留给 B4
- `claude` 与 `opencode` 后续如需恢复，应先重定义 contract 再实现

回归测试入口：

```bash
python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

当前测试覆盖：

- local / global 首次激活到空 root
- 已有 root 的重复激活
- `verify` 的 missing / broken symlink / wrong root type 结构错误
- `.aw_template` 到 `.aw/` 的首发 profile 生成
- `.aw_template` 的最小结构校验与 overwrite guard
