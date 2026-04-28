# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库面向操作者的 deploy 用法、deploy 行为说明和 release / distribution 边界。这里承接 backend target root 的 destructive reinstall model：先清理我方受管安装物，再检查冲突路径，最后只写入当前 source 声明的 live payload。canonical skill 真相仍在 `product/`，deploy target 不是 source of truth。

测试执行、registry npx smoke、本地 `.tgz` smoke、Codex / Claude 部署后行为检查已经移到 [Testing Runbooks](../testing/README.md)。

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我要给当前 backend 做一次完整重装 | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留 `prune --all` / `check_paths_exist` / `install` 三步主流程，`diagnose` 与 `verify` 作为只读辅助 |
| 我已有安装，想诊断 drift / conflict / unrecognized 目录 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 解释只读 `diagnose / verify`、冲突扫描和 destructive reinstall 恢复口径 |
| 我在改 skills 或 `.aw_template/` | [skill-lifecycle.md](./skill-lifecycle.md) | 说明 lifecycle 边界，以及为什么 deploy 不承接业务生命周期决策 |
| 我想看 canonical source 到 target entry 的正式映射 | [deploy-mapping-spec.md](./deploy-mapping-spec.md) | 定义 canonical source / backend payload source / target / diagnose / verify |
| 我想看 `npx aw-installer` 分发入口必须保持什么语义 | [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) | 定义 `aw-installer` CLI + TUI 双模式包装层合同 |
| 我想看 `aw-installer` 真实 npm 发布前需要满足什么条件 | [release-channel-contract.md](./release-channel-contract.md) | 定义 release channel、publish readiness guard、版本/tag/审批边界，并记录当前 registry 事实 |
| 我想在 npm publish 前确认 npx/package 文件、文档和证据不会发布后补救 | [aw-installer-npx-pre-publish-check.md](./aw-installer-npx-pre-publish-check.md) | 固定 packlist、metadata、dry-run、docs freshness 和 smoke 证据检查 |
| 我想看后续 npm 发布应采用哪种操作模型 | [aw-installer-release-operation-model.md](./aw-installer-release-operation-model.md) | 记录 GitHub Release `published` + npm Trusted Publishing 的发布模型与 repository-side workflow preflight |
| 我想给外部试用者一份可复制粘贴的 Codex / Claude Code 安装与 `.aw/` 初始化提示 | [aw-installer-public-quickstart-prompts.md](./aw-installer-public-quickstart-prompts.md) | 汇总 registry npx 主路径、Codex `agents` 主路径、Claude Code 兼容试用路径和 `.aw/` 初始化 prompt |
| 我想准备外部试用目标清单和反馈字段 | [aw-installer-external-trial-feedback.md](./aw-installer-external-trial-feedback.md) | 定义试用反馈字段、隐私边界和下一主要矛盾判定标准 |
| 我想看 `aw-installer` payload 从哪里来、`update` 信任边界在哪里 | [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md) | 定义 package payload、source/target root override、当前 update 边界与未来远程更新准入 |
| 我想看 `agents` canonical-copy payload source 怎么组织 | [agents-adapter-source.md](./agents-adapter-source.md) | 定义 `product/harness/adapters/agents/skills/` 的 payload descriptor 结构，以及 target 如何复制 canonical skill 内容 |
| 我想初始化 `.aw/` 样例并校验 `.aw_template` 最小结构 | [template-tooling-mvp.md](./template-tooling-mvp.md) | B2 的最小工作面，只做 `.aw_template -> .aw` 样例生成与前置校验 |
| 我想理解 `.aw_template/` 的模板消费边界 | [template-consumption-spec.md](./template-consumption-spec.md) | 定义 `.aw_template/` 中哪些内容属于 `.aw/` 运行管理面，哪些只是待迁移模板 |
| 我想把已有代码库接入 Harness 初始化流程 | [existing-code-adoption.md](./existing-code-adoption.md) | 定义 `.aw/repo/discovery-input.md` 作为只读事实输入，不作为 goal truth |

## 测试入口

| 测试问题 | 入口 |
|---|---|
| Python 脚本、治理检查、closeout gate 怎么跑 | [Python Script Test Execution](../testing/python-script-test-execution.md) |
| registry npx、本地 `.tgz`、多临时 workdir smoke 怎么跑 | [npx Command Test Execution](../testing/npx-command-test-execution.md) |
| Codex 部署后 Harness 行为怎么观察 | [Codex Post-Deploy Behavior Tests](../testing/codex-post-deploy-behavior-tests.md) |
| Claude Code 项目级 skill entry 和冷启动怎么观察 | [Claude Post-Deploy Behavior Tests](../testing/claude-post-deploy-behavior-tests.md) |

## 当前执行边界

- 当前 deploy 工具只实现 `agents` backend。
- operator-facing 主流程固定为三步：
  - `prune --all`
  - `check_paths_exist`
  - `install --backend agents`
- `prune --all` 只删除 resolved backend target root 下、带可识别且属于当前 backend 的受管 `aw.marker` 目录；无 marker、marker 不可识别或 foreign 目录一律不碰。
- `check_paths_exist` 基于当前 source 声明的 live bindings 解析目标路径；只要任一路径已存在，就全量列出冲突并失败退出，不做任何业务写入。
- `install --backend agents` 只写当前 source 声明的 live payload；若存在重复 `target_dir`、路径冲突或其他 source 非法情形，必须在写入前失败。
- `diagnose --backend agents --json` 是只读状态摘要命令，用于输出 source / target / issue code / conflict / unrecognized 摘要，发现 issue 时仍以 0 退出。
- `verify --backend agents` 是只读严格复验命令，用于检查 source 合法性、target root 状态、live install 对齐，以及 conflict / unrecognized 情形，发现 issue 时非零退出。
- `update --backend agents` 默认只输出 dry-run plan；`update --backend agents --yes` 是同一三步 destructive reinstall 加严格复验的 one-shot 包装。
- `update` 只阻塞占用 planned / known AW target path 的 unrecognized / foreign 内容；无关用户目录由 AW deploy 保持不动。
- 本地 `harness_deploy.py` thin wrapper、根目录 `package.json` 的 self-contained `aw-installer` package envelope、`toolchain/scripts/deploy/package.json` 的本地 scaffold、`aw-installer tui` shell、`aw-harness-deploy` 兼容别名与目标 `npx aw-installer` wrapper 必须保持 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 中定义的只读、严格复验、三步 destructive reinstall，以及 CLI + TUI 双模式语义。
- 当前 registry 事实由 [aw-installer Release Channel Contract](./release-channel-contract.md) 承接：`next` 指向 `0.4.0-rc.2`，`latest` 仍指向 `0.4.0-rc.1`；`latest` 不代表稳定 release approval。
- 后续真实 npm publish 还必须满足 [aw-installer Release Channel Contract](./release-channel-contract.md)；发布操作模型见 [aw-installer Release Operation Model](./aw-installer-release-operation-model.md)。npm-side Trusted Publisher 设置、未来 publish、stable/latest 语义仍需单独审批。
- `aw-installer` 的 payload provenance 与 update trust boundary 见 [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md)；当前 `update` 不做远程 fetch、channel 解析、验签、自升级或自动回滚。
- `aw.marker` 是 runtime-generated artifact，只用于标识“这是当前 backend 受管的 live install 目录”；它不是 source truth，也不是历史接管记录。
- deploy target 不是 source of truth。skills / payload source 的正式 owner 仍在 `product/`。
- Claude skills 分发当前只作为慢车道兼容项保留；Claude smoke/runbook 不能替代 `agents` deploy backend 合同，也不能把 `claude` 写成已实现 deploy backend。
- 当前 B2 初始化工具只处理 `.aw_template -> .aw` 样例，不消费 payload descriptor、不生成 deploy payload，也不写入 deploy target。
- Existing Code Project Adoption 的 `.aw/repo/discovery-input.md` 是只读事实输入，不是 `goal-charter.md` 的替代物。
- `docs/harness/` 继续承接 Harness doctrine；deploy 文档只定义 operator-facing deploy 合同。

## 不再承接的内容

`docs/project-maintenance/deploy/` 不再保存一次性 release approval package、historical smoke evidence、review findings、Codex/Claude 行为测试记录或 npx smoke runbook 副本。可重复测试步骤在 [Testing Runbooks](../testing/README.md)；release 准入规则在 [release-channel-contract.md](./release-channel-contract.md)；历史事实如需审计，使用对应 worktrack 交接或 git 历史。
