# Deploy Scripts

本目录保存部署和安装入口。

当前主线：

- `adapter_deploy.py`：保留 Python reference/fallback CLI 语义，为 `agents` 提供 destructive reinstall workflow、只读 `diagnose` 和只读 `verify`，并为 `claude` 提供受控的完整 Harness skill payload compatibility backend
- `harness_deploy.py`：稳定的薄包装入口，保留 `adapter_deploy.py` 语义，供目标 `aw-installer` package / npx wrapper 复用
- `path_safety_policy.json`：JS/Python deploy 入口共享的 target/source root 安全策略配置，避免 wrapper 与 Python reference path 漂移
- `package.json` + `bin/aw-installer.js` + `bin/aw-harness-deploy.js`：本地 npm-style package scaffold；`aw-installer` 是主 bin，直接承接 help/version、`agents` package/local 的 diagnose、update dry-run、check_paths_exist、verify、install、prune --all、update --yes composition 与 selected invalid-variant failures；当前 checkout/local package 还直接承接 `claude` package/local 的 diagnose human/JSON、update dry-run human/JSON、check_paths_exist、verify、install、prune --all、update --yes，并支持 `--claude-root`；`agents` 的显式 GitHub-source update JSON/human dry-run 与 `--yes` apply（`update --backend agents --source github ...`）也由 Node-owned 路径承接。release/package metadata、Python runtime retirement 与其他未迁移 deploy paths 仍 fallback 到 `harness_deploy.py` / Python reference。fallback 环境只透传 deploy 所需变量、代理和证书设置，`aw-harness-deploy` 是兼容别名，不表示 package 已发布
- `aw_scaffold.py`：从 `product/.aw_template/` 生成 `.aw/` 运行样例，并校验模板最小结构，包括 `Engineering Node Map`、`Repo Analysis` 与 `Node Type` 协议字段
- `product/harness/adapters/agents/skills/`：`agents` canonical-copy payload descriptor source，由 `install --backend agents` 消费
- `product/harness/adapters/claude/skills/`：`claude` compatibility payload descriptor source，当前承接受控的完整 Harness skill payload set

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
- `install --backend agents` 只写当前 source 声明的 live payload；若存在重复 `target_dir`、planned target path 冲突或其他 source 非法情形，必须在写入前失败且不调用 Python fallback；无关用户内容不属于 planned path conflict
- `diagnose` 用于输出 backend、target root、受管安装数量、issue code 与 unrecognized / conflict 摘要；发现 issue 时仍返回 0。`agents` package/local human/JSON 支持 `--agents-root`，`claude` package/local human/JSON 支持 `--claude-root`，这些当前 checkout/local package 路径均由 Node-owned wrapper 直接承接
- `verify` 用于检查 source 合法性、target root 状态、live install 对齐，以及 conflict / unrecognized 情形。`agents` 与 `claude` package/local read-only verify 当前由 Node-owned wrapper 直接承接；TUI agents verify action 也复用对应 Node-owned路径
- `harness_deploy.py` 当前只作为 Python fallback/reference 的薄包装入口存在；根目录 `package.json` 是 self-contained `aw-installer` package envelope，本地 package scaffold 仍暴露 `aw-installer` bin，但不表示 npm release channel 已发布
- 目标分发入口是 `npx aw-installer`，并应支持 CLI + TUI 双模式；当前提供 root package envelope、CLI surface 和最小 `tui` shell，TUI guided update flow 只能作为同一 deploy 合同上的交互式引导层
- `update --backend agents --json` 与 `update --backend claude --json` 在 package/local source dry-run 场景下由 Node-owned 路径输出 plan；`update --backend agents --source github` 在显式 GitHub source archive 场景下也由 Node-owned 路径承接 JSON/human dry-run 和 `--yes` apply，并保留 `backend`、`source_kind`、`source_ref`、`source_root`、`target_root`、`operation_sequence`、`managed_installs_to_delete`、`planned_target_paths`、`issues` 与 `blocking_issues` 等字段。human-readable `update --backend agents|claude` 是 package/local 只读 dry-run。`update --backend agents|claude --yes` 在 package/local source 场景下由 Node-owned 路径执行同一 `prune --all -> check_paths_exist -> install -> verify` composition；GitHub-source apply 也保持同一 destructive reinstall composition、blocking preflight、post-apply verify 和 recovery hint 语义
- `npm --prefix toolchain/scripts/deploy run smoke --silent` 只验证本地 package scaffold 的 bin 能打开当前 help，不发布或安装 package；`aw-installer --version` 是同一 Node wrapper 上的非交互 package metadata probe
- 如需检查目标 package envelope，在仓库根目录运行 `npm pack --dry-run --json`；本地 scaffold packlist 仍在 `toolchain/scripts/deploy/` 目录内运行；根 `.tgz` smoke 应在临时 target repo 中覆盖 help/version/TUI non-interactive guard/diagnose/update dry-run/install/verify/update apply
- 如需检查发布前包面，在仓库根目录运行 `npm run publish:dry-run --silent`；这只验证 npmjs publish dry-run，不上传 package；root package 的 `prepublishOnly` guard 会拒绝不满足 release-channel 准入的真实 publish，包括 local version、缺少 CI/审批信号、channel 与 dist-tag 不匹配或缺少匹配 git tag
- 从根 package `.tgz` 执行非 help 命令时，不设置 `AW_HARNESS_REPO_ROOT` 即可从 package 内读取 source payload，并把当前工作目录作为 target repo root；`AW_HARNESS_REPO_ROOT` 仍保留为 source checkout override，`AW_HARNESS_TARGET_REPO_ROOT` 可显式覆盖 target repo root。当前 `update` 只使用该 package、checkout source payload，或显式 GitHub source archive；不做 channel 解析、自升级、验签或自动回滚；完整边界见 `docs/project-maintenance/deploy/payload-provenance-trust-boundary.md`
- 当前接口实现 `agents` 主路径，并提供受控的完整 Harness skill set `claude` compatibility backend；不要把 `claude` 写成阻塞 `agents` 主线的稳定/默认分发路径
- 不再承接 `local/global` deploy modes、`prune --outdated`、archive/history、增量修复或旧版本保活
- Claude skills 分发当前仍是慢车道兼容项，不阻塞 `aw-installer` 主线

回归测试入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s toolchain/scripts/deploy -p 'test_*.py'
npm --prefix toolchain/scripts/deploy test --silent
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
