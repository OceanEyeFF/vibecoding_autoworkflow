# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：为 `agents` 提供 destructive reinstall workflow、只读 `diagnose` 和只读 `verify`
- `harness_deploy.py`：稳定的薄包装入口，保留 `adapter_deploy.py` 语义，供后续 package / npx-style wrapper 复用
- `package.json` + `bin/aw-harness-deploy.js`：本地 npm-style package scaffold，只调用 `harness_deploy.py`，不表示 package 已发布
- `aw_scaffold.py`：从 `product/.aw_template/` 生成 `.aw/` 运行样例，并校验模板最小结构，包括 `Engineering Node Map`、`Repo Analysis` 与 `Node Type` 协议字段
- `product/harness/adapters/agents/skills/`：`agents` canonical-copy payload descriptor source，由 `install --backend agents` 消费

最小维护流：

1. 如需机器可读状态摘要，先跑 `diagnose --backend agents --json`
2. `prune --all --backend agents`
3. `check_paths_exist --backend agents`
4. `install --backend agents`
5. 如需只读复验，再跑 `diagnose --backend agents --json` 或 `verify --backend agents`

`.aw_template` legacy scaffold profile 相关最小流：

1. 先跑 `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/aw_scaffold.py validate --profile first-wave-minimal`
2. 再跑 `PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/aw_scaffold.py generate --profile first-wave-minimal --output-root /tmp/demo-aw`
3. 如需覆盖已有样例，再显式加 `--force`

额外说明：

- `prune --all` 只删除带可识别、且属于当前 backend 的受管 `aw.marker` 目录
- `check_paths_exist` 基于当前 source 声明的 live bindings 全量列出冲突路径；命令失败时不允许有业务写入
- `install --backend agents` 只写当前 source 声明的 live payload；若存在重复 `target_dir`、路径冲突或其他 source 非法情形，必须在写入前失败
- `diagnose` 由 `adapter_deploy.py diagnose --json` 提供，用于输出 backend、target root、受管安装数量、issue code 与 unrecognized / conflict 摘要；发现 issue 时仍返回 0
- `verify` 由 `adapter_deploy.py verify` 提供，用于检查 source 合法性、target root 状态、live install 对齐，以及 conflict / unrecognized 情形
- `harness_deploy.py` 当前只作为本地薄包装入口存在，不表示 package / npx 发布渠道已经实现
- `update` 当前不是可用命令；未来若实现，只能包装同一三步 destructive reinstall，不得绕过 `check_paths_exist` 或 `verify` 语义
- `npm --prefix toolchain/scripts/deploy run smoke --silent` 只验证本地 package scaffold 的 bin 能打开当前 help，不发布或安装 package
- 如需检查 package packlist，在 `toolchain/scripts/deploy/` 目录内运行 `npm pack --dry-run --json`；不要从仓库根用 `--prefix` 跑 `pack`
- 从打包后的 `.tgz` 执行非 help 命令时，使用 `AW_HARNESS_REPO_ROOT=<repo-root>` 指向真实 source checkout；否则脚本会从 package 解压路径解析 source root
- 当前接口只实现 `agents`
- 不再承接 `local/global` deploy modes、`prune --outdated`、archive/history、增量修复或旧版本保活
- `claude` 与 `opencode` 后续如需恢复，应先重定义 contract 再实现

回归测试入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
```

GitHub CI 的 `Governance Checks` workflow 也会运行同一组 deploy regression tests，避免 deploy 工具回归只停留在本地验证。

相关回归应覆盖：

- `prune --all` 只删除带 marker 的受管目录，不删除 foreign / unrecognized 目录
- `check_paths_exist` 在多个冲突路径同时存在时全量列出并非零退出
- `install --backend agents` 在干净 target root 上成功写入 live payload
- `install --backend agents` 在重复 `target_dir` 或既有冲突路径下写入前失败
- `diagnose --backend agents --json` 在发现 issue 时仍以 0 退出，并输出结构化摘要
- `verify` 的 missing / broken symlink / wrong root type 结构错误
- `verify` 的 source drift、missing payload files、target payload drift 与 conflict / unrecognized 目录
- `.aw_template` 到 `.aw/` 的 legacy scaffold profile 生成
- `.aw_template` 的最小结构校验与 overwrite guard
- `.aw_template` 的 `Engineering Node Map` / `Node Type` 字段漂移校验
