---
title: "Distribution Entrypoint Contract"
status: active
updated: 2026-04-30
owner: aw-kernel
last_verified: 2026-04-30
---
# Distribution Entrypoint Contract

> 目的：为 reusable install/update/verify/diagnose 分发入口固定最小合同。目标分发形态是 Node/npm/npx 上的 `aw-installer`，当前 RC 试用入口收敛到 `aw-installer@next`；本文定义该包装层必须保持的语义，并记录当前 RC registry 入口边界。

本页属于 [Deploy Runbooks](./README.md) 系列。当前可执行入口仍是仓库内脚本：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py
```

当前还提供一个本地薄包装入口，供后续 package runner 复用同一命令面：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py
```

当前根目录 `package.json` 是 `aw-installer` 的 npm/npx 分发包络。它从根目录打包 `product/harness/skills`、`product/harness/adapters/agents/skills`、`product/harness/adapters/claude/skills` 与 `toolchain/scripts/deploy/` wrapper，使 `.tgz` 或 registry package 中的 source payload 可以脱离源码 checkout 被读取。当前 checkout 的 RC candidate 是 `0.4.1-rc.2`；当前 npm registry 事实仍是 `next=0.4.0-rc.3`、`latest=0.4.0-rc.1`。

`toolchain/scripts/deploy/package.json`、`bin/aw-installer.js` 和 `bin/aw-harness-deploy.js` 仍保留为本地 npm-style scaffold。`aw-installer` 是主 bin，`aw-harness-deploy` 是兼容别名。`aw-installer --help` / `--version` 由 Node wrapper 直接处理；deploy modes 仍调用同一个 Python wrapper。`0.4.1-rc.2` 在 Windows 上按 `py -3`、`python`、`python3` 尝试 Python launcher，在 Linux/macOS 上按 `python3`、`python` 尝试；wrapper 不接受 `PYTHON`/`PYTHON3` 环境变量覆盖。

根 package packlist 检查在仓库根目录执行 `npm pack --dry-run --json`。本地 scaffold packlist 检查仍在 `toolchain/scripts/deploy/` package root 内执行 `npm pack --dry-run --json`。

CI 必须显式设置 Node 后运行本地 package smoke、本地 scaffold pack dry-run、根 package pack dry-run、根 package publish dry-run、本地 scaffold tarball smoke，以及根 `.tgz` 的 `aw-installer --help`、`aw-installer --version`、`aw-installer tui` 非交互 guard、只读 `diagnose`、`update --json` dry-run、`install --backend agents`、安装后的 `verify --backend agents` 和显式 `update --backend agents --yes` apply smoke。根 `.tgz` smoke 不设置 `AW_HARNESS_REPO_ROOT`，用于证明 package 内 source payload 与当前工作目录 target root 已分离。

根 package `publishConfig.registry` 必须固定为 `https://registry.npmjs.org/`，避免真实 release 或 dry-run 被本机 npm mirror 配置改写。`npm run publish:dry-run --silent` 是发布前检查，不代表已经授权执行 `npm publish`。根 package 的 `prepublishOnly` guard 允许 `--dry-run`，但真实 publish 必须通过 [aw-installer Release Channel Contract](./release-channel-contract.md) 中定义的版本、channel、dist-tag、CI、审批和 git tag 准入。

`AW_HARNESS_REPO_ROOT` 是 source checkout override。设置它时，source root 与默认 target repo root 保持旧的 repo-local 行为；未设置它时，packaged wrapper 从 package 解压根读取 source payload，并默认把当前工作目录作为用户项目 target repo root。`AW_HARNESS_TARGET_REPO_ROOT` 可显式覆盖 target repo root。

`aw-installer` 的 package payload provenance、source/target root 解析和 `update` trust boundary 由 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md) 固定。`0.4.0-rc.3` 允许 `update --source github --github-repo OWNER/REPO --github-ref REF` 显式使用 GitHub source archive 作为本次 source root；包装层不得把 channel 解析、自升级、验签或自动回滚悄悄并入当前 `update --yes`。

`--github-repo` 的默认值可以由 `AW_INSTALLER_GITHUB_REPO` 或 GitHub Actions 的 `GITHUB_REPOSITORY` 提供；两者都不存在时才回退到上游仓库。可移植脚本和 fork 验证应显式传 `--github-repo`，避免误读上游 source archive。

## 一、范围

本文定义 `aw-installer` 分发入口的外层合同：

- 分发包装层可以改变 operator 如何启动命令，但不能改变 deploy 语义。
- CLI 是稳定的脚本化合同；TUI 是同一合同上的交互式操作层。
- `npx aw-installer@next` 是当前 RC 用户入口；裸 `npx aw-installer` 仍解析到 `latest=0.4.0-rc.1`，`aw-harness-deploy` 只是兼容别名。
- 当前 `agents` backend 的 source / target / payload / marker 合同仍以 [Deploy Mapping Spec](./deploy-mapping-spec.md) 为准。
- 当前 `claude` backend 只作为 compatibility lane 准入 `set-harness-goal-skill` payload；边界见 [Claude Adapter Source](./claude-adapter-source.md)。
- 当前 destructive reinstall 主流程仍以 [Deploy Runbook](./deploy-runbook.md) 为准。

本文不定义：

- npm 发布账户、registry 凭证或 release workflow；release channel 与 publish readiness 准入见 [aw-installer Release Channel Contract](./release-channel-contract.md)。
- channel-based 远程更新、payload manifest、签名/验签、自升级或自动回滚；这些能力必须先满足 [Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md) 的准入条件。
- 具体 TUI framework、按键模型、配色或终端渲染实现。
- 完整 Claude Harness skill set 分发或新的非 `agents` / `claude` backend。
- `adapter_deploy.py` 内部实现。
- 新的 install/update 策略。

## 二、当前与目标入口

当前已验证入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py <mode> --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py <mode> --backend claude
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py <mode> --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/harness_deploy.py <mode> --backend claude
```

当前本地 package scaffold 入口：

```bash
aw-installer <mode> --backend agents
aw-installer <mode> --backend claude
```

兼容别名仍可调用同一 wrapper：

```bash
aw-harness-deploy <mode> --backend agents
```

目标 Node/npm/npx 用户入口。Package identity 已批准为 unscoped `aw-installer`；当前 registry 主试用入口是 `aw-installer@next` selector：

```bash
npx aw-installer@next
npx aw-installer@next tui
npx aw-installer@next --version
npx aw-installer@next diagnose --backend agents --json
npx aw-installer@next verify --backend agents
npx aw-installer@next install --backend agents
npx aw-installer@next update --backend agents
npx aw-installer@next update --backend agents --yes
npx aw-installer@next update --backend agents --source github --github-ref <ref-containing-current-payload>
npx aw-installer@next diagnose --backend claude --json
npx aw-installer@next update --backend claude
npx aw-installer@next install --backend claude
npx aw-installer@next verify --backend claude
```

Bare `npx aw-installer` currently resolves to the older rc1 package because npm exposes it through `latest`; do not use that as current RC or stable-release evidence. `npx aw-installer@next ...` remains the explicit published RC pin. Before `0.4.1-rc.2` is published, `next` resolves to the currently published prerelease selector, observed as `0.4.0-rc.3` on 2026-04-29; checkout evidence must use a local `.tgz` or source checkout. `npx aw-installer@next` 在交互式终端中可以进入 TUI；`npx aw-installer@next tui` 显式启动当前最小交互 shell。脚本和 CI 必须使用显式 CLI subcommand。非交互环境不得隐式启动 TUI，也不得要求方向键、全屏渲染或人工输入才能完成 CLI subcommand。

所有入口都必须投影到同一组 mode：

| mode | 当前语义 | 未来包装层约束 |
|---|---|---|
| `diagnose` | 只读状态投影；`--json` 输出机器可读摘要；发现 issue 时仍可 0 退出 | 保持只读、非严格失败信号，不替代 `verify` |
| `verify` | 只读严格复验；发现 source、target、payload、marker、drift 或 conflict 问题时失败 | 保持只读、严格失败信号 |
| `prune --all` | 删除当前 backend 可识别且属于我方的受管安装目录 | 仍必须显式触发，不能静默并入只读命令 |
| `check_paths_exist` | 写入前全量冲突扫描；发现冲突时失败且不写业务文件 | 保持零业务写入边界 |
| `install` | 只写当前 source 声明的 live payload | 不接管 archive/history、增量修复或旧版本保活 |
| `update` | 默认输出 dry-run plan；显式 `--yes` 后按 `prune --all -> check_paths_exist -> install -> verify` 执行 | 只能作为三步 destructive reinstall 的显式 one-shot 包装，不得引入新安装策略 |

## 三、CLI + TUI 双模式合同

- CLI subcommands 是机器可读、可脚本化、可在 CI 中复验的稳定接口。
- TUI 只负责引导 operator 选择 backend、查看诊断、确认 update plan 或启动已定义的 CLI 等价动作。当前本地 scaffold 已提供最小 `tui` shell，不包含 full-screen framework；主入口是 guided update flow，按 `diagnose -> update dry-run plan -> explicit yes -> update --yes` 映射到现有 CLI wrapper。
- TUI 不得拥有独立于 CLI 的 deploy 语义；每一个 mutating TUI 动作都必须映射到一个明确的 CLI mode 和参数集合。
- TUI 中的 destructive action 必须展示等价 dry-run plan，并要求显式确认；不能把 `update --yes`、`prune --all` 或 `install` 藏在默认启动流程里。
- TUI 不能把 `opencode` 展示为已支持 deploy backend。Claude skills distribution 只能作为 slower compatibility lane 的受控入口展示，且必须说明当前只覆盖 `set-harness-goal-skill`，不能覆盖当前 `agents` 主合同。
- CLI 和 TUI 的输出边界要清楚：`--json` 只属于 CLI 机器输出；TUI 可以展示同一数据，但不能让机器可读输出混入交互渲染。

## 四、必须保持的不变量

- `diagnose` 和 `verify` 都是只读入口。
- `diagnose` 是状态观察，不是安装成功证明；需要严格失败信号时使用 `verify`。
- mutating install 仍由 `prune --all -> check_paths_exist -> install` 三步表达。
- `check_paths_exist` 失败时不得写入业务文件。
- `install` 不得跳过 source contract 校验、target path 冲突校验或 payload identity 校验。
- deploy target 不是 source of truth；包装层不得从 `.agents/`、`.claude/` 或 `.opencode/` 反向生成 canonical source。
- backend 支持列表必须来自实际实现；包装层不得把 `opencode` 或完整 Claude Harness skill set 写成已支持 deploy backend。当前 `claude` 只能作为受控 `set-harness-goal-skill` compatibility backend 暴露。

## 五、`update` 的准入条件

`update` 已按以下准入答案实现；后续包装层必须保持同一边界：

- `update` 只能是 `prune --all -> check_paths_exist -> install --backend <backend> -> verify --backend <backend>` 的 one-shot 包装，不得引入增量修复、archive/history、旧版本保活或 target-to-source 反向同步。
- `update` 默认只输出 dry-run plan；只有显式传入 `--yes` 才会变更 target root。
- `update --source github` 只在本次命令中把 GitHub source archive 作为 source root；target root 仍来自当前工作目录、`AW_HARNESS_TARGET_REPO_ROOT` 或 backend root override。
- `update` 必须在执行前暴露 target root、将删除的受管 install paths、将写入的 target paths，以及当前 conflict / unrecognized / foreign 摘要；`--json` 只用于 dry-run plan，以保证机器可读输出不会混入写入日志。
- `update` 在 source contract 非法、target root 类型错误、坏链路、待写入路径 conflict，或 planned / known AW target path 被 unrecognized / foreign 内容占用时必须停止；target root 下无关用户目录不属于 `update` 阻塞项，旧的同 backend 受管目录可以由 `prune --all` 清理；`check_paths_exist` 失败时不得写业务文件。
- `update` 必须复用 `diagnose` 的状态摘要和 `verify` 的严格失败信号：执行前可给出只读摘要，执行后必须跑等价严格复验并把 issue 作为失败信号。
- `update` 不承诺自动回滚。恢复语义落在 [Skill Deployment 维护流](./skill-deployment-maintenance.md)：修正 source 或 target 后重新运行显式三步主流程，或在未来实现中重新运行同等 one-shot 包装。
- `update` 的 help、README、package smoke 和 closeout coverage 必须验证它不绕过三步 destructive reinstall 不变量。

## 六、包装层验收标准

未来任一分发包装 worktrack 至少应验证：

- wrapper help 或 README 不声称未实现 backend 可用。
- wrapper 的 `diagnose`、`verify` 与 repo-local 脚本在同一 fixture 上给出等价状态。
- wrapper 的 mutating command 不绕过 `check_paths_exist` 的零业务写入边界。
- wrapper 保留 backend target root override 入口，或明确声明当前不支持 override。
- wrapper 文档清楚区分当前已实现命令和未来保留命令。
- CLI/TUI 双模式实现必须证明 TUI 调用的是同一 CLI/deploy contract，而不是第二套 install/update 逻辑。
- 非交互 CLI smoke 必须能在没有 TUI 的环境中运行。

## 七、当前停止线

当前仓库只承诺 repo-local deploy scripts、本地 npm-style `aw-installer` scaffold、带 guided update flow 的最小 `tui` shell、root package envelope 和 `agents` backend。`harness_deploy.py`、`bin/aw-installer.js` 与 `bin/aw-harness-deploy.js` 都是本地薄包装入口，不是已发布 package，也不是 full-screen TUI framework。进入真实 release 前必须同时满足本文的入口语义与 [aw-installer Release Channel Contract](./release-channel-contract.md) 的发布准入。
