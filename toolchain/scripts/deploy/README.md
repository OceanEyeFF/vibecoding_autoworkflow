# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：为 `agents` 提供 destructive reinstall workflow 和只读 `verify`
- `aw_scaffold.py`：从 `product/.aw_template/` 生成 `.aw/` 运行样例，并校验模板最小结构
- `product/harness/adapters/agents/skills/`：`agents` canonical-copy payload descriptor source，由 `install --backend agents` 消费

最小维护流：

1. `prune --all --backend agents`
2. `check_paths_exist --backend agents`
3. `install --backend agents`
4. 如需只读复验，再跑 `verify --backend agents`

`.aw_template` 相关最小流：

1. 先跑 `python3 toolchain/scripts/deploy/aw_scaffold.py validate --profile first-wave-minimal`
2. 再跑 `python3 toolchain/scripts/deploy/aw_scaffold.py generate --profile first-wave-minimal --output-root /tmp/demo-aw`
3. 如需覆盖已有样例，再显式加 `--force`

额外说明：

- `prune --all` 只删除带可识别、且属于当前 backend 的受管 `aw.marker` 目录
- `check_paths_exist` 基于当前 source 声明的 live bindings 全量列出冲突路径；命令失败时不允许有业务写入
- `install --backend agents` 只写当前 source 声明的 live payload；若存在重复 `target_dir`、路径冲突或其他 source 非法情形，必须在写入前失败
- `verify` 由 `adapter_deploy.py verify` 提供，用于检查 source 合法性、target root 状态、live install 对齐，以及 conflict / unrecognized 情形
- 当前接口只实现 `agents`
- 不再承接 `local/global` deploy modes、`prune --outdated`、archive/history、增量修复或旧版本保活
- `claude` 与 `opencode` 后续如需恢复，应先重定义 contract 再实现

回归测试入口：

```bash
python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

相关回归应覆盖：

- `prune --all` 只删除带 marker 的受管目录，不删除 foreign / unrecognized 目录
- `check_paths_exist` 在多个冲突路径同时存在时全量列出并非零退出
- `install --backend agents` 在干净 target root 上成功写入 live payload
- `install --backend agents` 在重复 `target_dir` 或既有冲突路径下写入前失败
- `verify` 的 missing / broken symlink / wrong root type 结构错误
- `verify` 的 source drift、missing payload files、target payload drift 与 conflict / unrecognized 目录
- `.aw_template` 到 `.aw/` 的首发 profile 生成
- `.aw_template` 的最小结构校验与 overwrite guard
