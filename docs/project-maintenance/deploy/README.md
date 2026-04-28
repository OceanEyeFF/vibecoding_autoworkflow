# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库面向操作者的 deploy / diagnose / verify / maintenance 文档。这里承接的是 backend target root 的 destructive reinstall model：先清理我方受管安装物，再检查冲突路径，最后只写入当前 source 声明的 live payload。canonical skill 真相仍在 `product/`，`.aw_template/` 也不是 deploy payload source。

这里适合放：

- backend target root、入口命令与主流程
- `prune --all -> check_paths_exist -> install --backend agents` 的操作口径
- 只读 `diagnose / verify` 的状态观察与诊断闭环
- canonical source 到 backend payload / target entry 的映射合同
- 目标 `npx aw-installer` reusable distribution entrypoint 的语义边界
- `aw-installer` package payload provenance、source/target root 与 update trust boundary
- `.aw_template/` 的 `.aw/` 使用合同与边界

这里不适合放：

- canonical skill 真相正文
- archive / history / old-version keepalive 方案
- 旧 `local/global` deploy mode 的主流程说明
- 非 deploy / diagnose / verify 主流程

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我要给当前 backend 做一次完整重装 | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留 `prune --all` / `check_paths_exist` / `install` 三步主流程，`diagnose` 与 `verify` 作为只读辅助 |
| 我想在临时 repo 里手动跑多轮 `Codex` harness 观察真实执行 | [codex-harness-manual-runbook.md](./codex-harness-manual-runbook.md) | 固定题目、临时 repo 初始化、隔离 deploy、逐轮监督与观察产物收集 |
| 我想用 Claude Code 做项目级 skill entry smoke / 冷启动测试 | [claude-harness-test-runbook.md](./claude-harness-test-runbook.md) | 临时 repo、`.claude/skills/` 项目级安装、Claude 非交互读取与最小 `.aw/` 冷启动 |
| 我想看已完成的 `continuous-autonomy` 手动观察证据 | [codex-harness-manual-run-continuous-2026-04-23.md](./codex-harness-manual-run-continuous-2026-04-23.md) | 记录 2026-04-23 到 2026-04-24 round-000 到 round-060 的连续 worktrack 推进、108 tests / 20 tests 复验结果，以及 budget 用尽与未用尽两种 stable handback 结论 |
| 我想看 canonical source 到 target entry 的正式映射 | [deploy-mapping-spec.md](./deploy-mapping-spec.md) | 最小 deploy 合同，定义 canonical source / backend payload source / target / diagnose / verify |
| 我想看 `npx aw-installer` 分发入口必须保持什么语义 | [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) | 定义 `aw-installer` CLI + TUI 双模式包装层合同；不表示 package 或 release channel 已实现 |
| 我想看 `aw-installer` 真实 npm 发布前需要满足什么条件 | [release-channel-contract.md](./release-channel-contract.md) | 定义 release channel、publish readiness guard、版本/tag/审批边界；不授权真实 publish |
| 我想准备 `aw-installer` release-candidate 证据包 | [aw-installer-release-candidate-prep.md](./aw-installer-release-candidate-prep.md) | 固定 RC prep checkpoint、证据 bundle、release notes 与 rollback/deprecation plan；不授权真实 publish |
| 我想审查第一条 `aw-installer` RC 发布审批包 | [aw-installer-rc-approval-package.md](./aw-installer-rc-approval-package.md) | 固定 `0.4.x` 版本线、`0.4.0-rc.1` 候选、`next` channel、证据路径与回滚计划；不授权真实 publish |
| 我想复核 `aw-installer` 非 publish 发布演练结果 | [aw-installer-release-rehearsal.md](./aw-installer-release-rehearsal.md) | 记录 pack、publish dry-run、publish guard、`0.4.0-rc.1 -> next` 推导和 two-target tarball smoke；不授权真实 publish |
| 我想准备外部试用目标清单和反馈字段 | [aw-installer-external-trial-feedback.md](./aw-installer-external-trial-feedback.md) | 定义自有仓库与论坛志愿者试用模板、反馈字段、隐私边界和下一主要矛盾判定标准；不包含公开招募文案 |
| 我想给外部试用者一份可复制粘贴的 Codex / Claude Code 安装与 `.aw/` 初始化提示 | [aw-installer-public-quickstart-prompts.md](./aw-installer-public-quickstart-prompts.md) | 汇总 registry npx 主路径、Codex `agents` 主路径、Claude Code 兼容试用路径和 `.aw/` 初始化 prompt |
| 我想复核发布前文档治理状态与剩余 blocker 分类 | [aw-installer-pre-release-docs-governance-verification.md](./aw-installer-pre-release-docs-governance-verification.md) | 记录 quickstart、feedback、smoke、RC、usage-help 路由的最终文档治理验证；区分 docs blocker 与 approval blocker |
| 我想在隔离目标仓库验证本地 `.tgz` | [aw-installer-external-target-smoke.md](./aw-installer-external-target-smoke.md) | 提供 two-target tarball smoke 操作脚本和汇报模板；不授权真实 publish |
| 我想在多个临时 workdir / 临时 clone 中验证 packaged installer 不串台 | [aw-installer-multi-temp-workdir-smoke.md](./aw-installer-multi-temp-workdir-smoke.md) | 提供三目标 smoke 脚本，覆盖空临时 repo 与两个批准目标 repo 的临时 clone；不 push、不发布 npm |
| 我想验证已发布 registry 包的 npx 路径并生成反馈日志 | [aw-installer-registry-npx-smoke.md](./aw-installer-registry-npx-smoke.md) | 提供 Windows PowerShell / Linux bash / macOS bash 可运行的 Node smoke runner，并为每个目标生成 `aw-installer-npx-run.log` |
| 我想看 `aw-installer` payload 从哪里来、`update` 信任边界在哪里 | [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md) | 定义 package payload、source/target root override、当前 update 边界与未来远程更新准入 |
| 我想看 `agents` canonical-copy payload source 怎么组织 | [agents-adapter-source.md](./agents-adapter-source.md) | 定义 `product/harness/adapters/agents/skills/` 的 payload descriptor 结构，以及 target 如何复制 canonical skill 内容 |
| 我想初始化 `.aw/` 样例并校验 `.aw_template` 最小结构 | [template-tooling-mvp.md](./template-tooling-mvp.md) | B2 的最小工作面，只做 `.aw_template -> .aw` 样例生成与前置校验 |
| 我想把已有代码库接入 Harness 初始化流程 | [existing-code-adoption.md](./existing-code-adoption.md) | 定义 `.aw/repo/discovery-input.md` 作为只读事实输入，不作为 goal truth |
| 我已有安装，想诊断 drift / conflict / unrecognized 目录 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 解释只读 `diagnose / verify`、冲突扫描和 destructive reinstall 恢复口径 |
| 我在改 skills 或 `.aw_template/` | [skill-lifecycle.md](./skill-lifecycle.md) | 说明 lifecycle 边界，以及为什么 deploy 不承接业务生命周期决策 |
| 我想看 backend 当前实现状态 | [deploy-runbook.md](./deploy-runbook.md) | 当前只保留 `agents` 已实现；其他 backend 不写成稳定 operator 流程 |

## 外部试用路由

外部试用者和维护者应按这个顺序进入，而不是从单个 `npx` 片段自行推断发布状态：

- 安装与 `.aw/` 初始化提示：先看 [aw-installer Public Quickstart Prompts](./aw-installer-public-quickstart-prompts.md)。当前 `aw-installer@0.4.0-rc.1` 已发布为 registry RC；registry npx smoke 已覆盖 bare package selector `aw-installer` 的本地多目标路径，必要时可用 `aw-installer@next` 显式 pin 到 RC channel。
- 反馈入口：用 [aw-installer External Trial Feedback Contract](./aw-installer-external-trial-feedback.md)、[trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 或 [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)。
- Registry npx smoke 与反馈日志：用 [aw-installer Registry npx Smoke](./aw-installer-registry-npx-smoke.md) 验证空临时 repo 与批准目标 repo 临时 clone 的 source/target 隔离，并生成可脱敏提交的 `aw-installer-npx-run.log`；不要写入非临时 checkout，不 push，不开 issue 或 PR。
- 本地包 smoke：用 [aw-installer Multi Temporary Workdir Smoke](./aw-installer-multi-temp-workdir-smoke.md) 验证当前 checkout 打出的 `.tgz`。
- 发布边界：RC 身份和证据包看 [aw-installer RC Approval Package](./aw-installer-rc-approval-package.md)，非 publish 演练看 [aw-installer Non-Publish Release Rehearsal](./aw-installer-release-rehearsal.md)。当前已发布的 RC 不是稳定 release；后续 publish、stable/latest 语义和自动化发布仍需单独审批。
- backend 边界：Codex 走 `agents` backend；Claude Code 仅是 compatibility trial lane，不是稳定 deploy backend。

## 当前执行边界

- 当前 deploy 工具只实现 `agents`
- operator-facing 主流程固定为三步：
  - `prune --all`
  - `check_paths_exist`
  - `install --backend agents`
- `prune --all` 只删除 resolved backend target root 下、带可识别且属于当前 backend 的受管 `aw.marker` 目录；无 marker、marker 不可识别或 foreign 目录一律不碰
- `check_paths_exist` 基于当前 source 声明的 live bindings 解析目标路径；只要任一路径已存在，就全量列出冲突并失败退出，不做任何业务写入
- `install --backend agents` 只写当前 source 声明的 live payload；若存在重复 `target_dir`、路径冲突或其他 source 非法情形，必须在写入前失败
- `diagnose --backend agents --json` 保留为只读状态摘要命令，用于输出 source / target / issue code / conflict / unrecognized 摘要，发现 issue 时仍以 0 退出
- `verify --backend agents` 保留为只读严格复验命令，用于检查 source 合法性、target root 状态、live install 对齐，以及 conflict / unrecognized 情形，发现 issue 时非零退出
- `update --backend agents` 默认只输出 dry-run plan；`update --backend agents --yes` 是同一三步 destructive reinstall 加严格复验的 one-shot 包装
- `update` 只阻塞占用 planned / known AW target path 的 unrecognized / foreign 内容；无关用户目录由 AW deploy 保持不动
- 本地 `harness_deploy.py` thin wrapper、根目录 `package.json` 的 self-contained `aw-installer` package envelope、`toolchain/scripts/deploy/package.json` 的本地 scaffold、`aw-installer tui` shell、`aw-harness-deploy` 兼容别名与目标 `npx aw-installer` wrapper 必须保持 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 中定义的只读、严格复验、三步 destructive reinstall，以及 CLI + TUI 双模式语义；当前 npm registry 已有 `aw-installer@0.4.0-rc.1` RC，裸 `aw-installer` package selector 解析到该 RC，`aw-installer@next` 可作为显式 RC pin。
- 后续真实 npm publish 还必须满足 [aw-installer Release Channel Contract](./release-channel-contract.md)；publish dry-run 和 root `.tgz` smoke 不等于发布授权
- `aw-installer` 的 payload provenance 与 update trust boundary 见 [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md)；当前 `update` 不做远程 fetch、channel 解析、验签、自升级或自动回滚
- 不再承接这些主线语义：
  - `retired-target-dir`
  - `prune --outdated`
  - archive / history
  - 增量修复
  - 旧版本保活
  - “确认新目录可用再删旧目录”
  - `local/global` deploy modes
- `aw.marker` 是 runtime-generated artifact，只用于标识“这是当前 backend 受管的 live install 目录”；它不是 source truth，也不是历史接管记录
- deploy target 不是 source of truth。skills / payload source 的正式 owner 仍在 `product/`
- Claude skills 分发当前只作为慢车道兼容项保留；Claude smoke/runbook 不能替代 `agents` deploy backend 合同，也不能把 `claude` 写成已实现 deploy backend
- 当前 B2 初始化工具只处理 `.aw_template -> .aw` 样例，不消费 payload descriptor、不生成 deploy payload，也不写入 deploy target
- Existing Code Project Adoption 的 `.aw/repo/discovery-input.md` 是只读事实输入，不是 `goal-charter.md` 的替代物；当前可通过 `set-harness-goal-skill/scripts/deploy_aw.py generate --adoption-mode existing-code-adoption` 在默认/profile 生成中渲染，具体 artifact/template 与确认边界见 [existing-code-adoption.md](./existing-code-adoption.md)
- `docs/harness/` 继续承接 Harness doctrine；deploy 文档只定义 operator-facing deploy 合同
- `.aw_template/` 的 `.aw/` 目录结构、管理文档模板和待迁移模板边界见 [template-consumption-spec.md](./template-consumption-spec.md)

## 页面职责

- [codex-harness-manual-runbook.md](./codex-harness-manual-runbook.md)
  manual harness runbook。回答如何在临时 repo 中准备隔离运行面、连续调用无交互 `Codex`，并监督每轮真实执行内容。
- [claude-harness-test-runbook.md](./claude-harness-test-runbook.md)
  Claude Harness test runbook。回答如何在临时 repo 中安装项目级 Claude skill entry，并做非交互读取 smoke 与最小 `.aw/` 冷启动验证。
- [codex-harness-manual-run-continuous-2026-04-23.md](./codex-harness-manual-run-continuous-2026-04-23.md)
  manual harness run evidence。记录同一条 `continuous-autonomy` 观察主线，包括 round-000 到 round-060、40 个 closed worktracks、后续 6 个 chartered worktracks、108 tests / 20 tests 复验，以及预算归零和未归零两种 stable handback。
- [deploy-runbook.md](./deploy-runbook.md)
  quick start。回答 destructive reinstall 主流程和最小复验。
- [skill-lifecycle.md](./skill-lifecycle.md)
  lifecycle。回答为什么 deploy 不承接 add / update / rename / remove 的业务同步决策。
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
  maintenance / diagnosis。回答只读 `diagnose / verify`、冲突扫描、drift 与恢复路径。
- [deploy-mapping-spec.md](./deploy-mapping-spec.md)
  mapping contract。回答 canonical source / backend payload source / target / diagnose / verify 的最小正式规则。
- [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md)
  distribution entrypoint contract。回答目标 `npx aw-installer` CLI + TUI 包装层必须保持哪些 deploy 语义，以及哪些 packaging / TUI / release 行为尚未实现。
- [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md)
  payload provenance / update trust boundary。回答 root package `.tgz` 中的 deploy payload 从哪里来、source/target root 怎么解析，以及当前 `update` 为什么只能重装当前可信 source payload。
- [aw-installer-release-candidate-prep.md](./aw-installer-release-candidate-prep.md)
  release-candidate prep。回答如何准备未来 `aw-installer` RC evidence bundle、release notes 和 rollback/deprecation plan；普通 prep 不授权真实 npm publish。
- [aw-installer-rc-approval-package.md](./aw-installer-rc-approval-package.md)
  RC approval package。回答第一条 `0.4.x` release-candidate 线如何命名、P0-019 如何发布 `aw-installer@0.4.0-rc.1`、registry evidence 是什么，以及 rollback/deprecation plan 如何表述。
- [aw-installer-release-rehearsal.md](./aw-installer-release-rehearsal.md)
  non-publish release rehearsal。回答 `aw-installer` 在真实 publish 前的 pack、publish dry-run、publish guard、candidate channel 推导和 two-target tarball smoke 是否可复现；不授权真实 npm publish。
- [aw-installer-external-trial-feedback.md](./aw-installer-external-trial-feedback.md)
  external trial feedback。回答如何为自有仓库和论坛志愿者试用准备匿名目标清单、命令反馈字段、operator confusion 分类和下一主要矛盾判定标准；不包含公开招募文案。
- [aw-installer-public-quickstart-prompts.md](./aw-installer-public-quickstart-prompts.md)
  public quickstart prompts。回答如何让外部试用者用 registry `npx aw-installer` 安装 AW artifacts，并通过 Codex 或 Claude Code 初始化 `.aw/`。
- [aw-installer-pre-release-docs-governance-verification.md](./aw-installer-pre-release-docs-governance-verification.md)
  pre-release docs governance verification。回答发布前文档路由是否一致、剩余 docs blocker 与 approval blocker 如何区分。
- [aw-installer-external-target-smoke.md](./aw-installer-external-target-smoke.md)
  external target smoke。回答如何用本地 `.tgz` 在两个隔离目标仓库中验证 packaged `aw-installer` help/version/TUI guard/diagnose/update/install/verify/update apply，并给出汇报模板。
- [aw-installer-multi-temp-workdir-smoke.md](./aw-installer-multi-temp-workdir-smoke.md)
  multi temporary workdir smoke。回答如何用 packaged `aw-installer` 在多个临时 workdir 或批准目标 repo 的临时 clone 中验证 source/target 隔离、默认 cwd 行为和跨 workdir 不串台。
- [aw-installer-registry-npx-smoke.md](./aw-installer-registry-npx-smoke.md)
  registry npx smoke。回答如何跨 Windows PowerShell、Linux bash、macOS bash 验证已发布 registry 包，并生成 feedback log。
- [agents-adapter-source.md](./agents-adapter-source.md)
  adapter source。回答 `agents` canonical-copy payload descriptor、copied skill files 与 runtime marker 边界。
- [template-consumption-spec.md](./template-consumption-spec.md)
  template contract。回答 `.aw_template/` 中哪些内容属于 `.aw/` 运行管理面，哪些只是待迁移模板。
- [template-tooling-mvp.md](./template-tooling-mvp.md)
  template tooling。回答 B2 当前提供的最小生成 / 校验面。
- [existing-code-adoption.md](./existing-code-adoption.md)
  existing code adoption。回答既有代码库接入 Harness 初始化时，`discovery-input.md` 的生成目标、非 goal truth 边界，以及它和 snapshot / goal / control 的关系。
