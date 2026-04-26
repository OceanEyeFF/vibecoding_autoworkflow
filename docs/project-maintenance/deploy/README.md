# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库面向操作者的 deploy / diagnose / verify / maintenance 文档。这里承接的是 backend target root 的 destructive reinstall model：先清理我方受管安装物，再检查冲突路径，最后只写入当前 source 声明的 live payload。canonical skill 真相仍在 `product/`，`.aw_template/` 也不是 deploy payload source。

这里适合放：

- backend target root、入口命令与主流程
- `prune --all -> check_paths_exist -> install --backend agents` 的操作口径
- 只读 `diagnose / verify` 的状态观察与诊断闭环
- canonical source 到 backend payload / target entry 的映射合同
- 未来 reusable distribution entrypoint 的语义边界
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
| 我想看未来 package/npx 风格分发入口必须保持什么语义 | [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) | 定义 reusable install/update/verify/diagnose 包装层合同；不表示 packaging 已实现 |
| 我想看 `agents` canonical-copy payload source 怎么组织 | [agents-adapter-source.md](./agents-adapter-source.md) | 定义 `product/harness/adapters/agents/skills/` 的 payload descriptor 结构，以及 target 如何复制 canonical skill 内容 |
| 我想初始化 `.aw/` 样例并校验 `.aw_template` 最小结构 | [template-tooling-mvp.md](./template-tooling-mvp.md) | B2 的最小工作面，只做 `.aw_template -> .aw` 样例生成与前置校验 |
| 我想把已有代码库接入 Harness 初始化流程 | [existing-code-adoption.md](./existing-code-adoption.md) | 定义 `.aw/repo/discovery-input.md` 作为只读事实输入，不作为 goal truth |
| 我已有安装，想诊断 drift / conflict / unrecognized 目录 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 解释只读 `diagnose / verify`、冲突扫描和 destructive reinstall 恢复口径 |
| 我在改 skills 或 `.aw_template/` | [skill-lifecycle.md](./skill-lifecycle.md) | 说明 lifecycle 边界，以及为什么 deploy 不承接业务生命周期决策 |
| 我想看 backend 当前实现状态 | [deploy-runbook.md](./deploy-runbook.md) | 当前只保留 `agents` 已实现；其他 backend 不写成稳定 operator 流程 |

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
- 未来 reusable package / npx-style wrapper 必须保持 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 中定义的只读、严格复验和三步 destructive reinstall 语义；当前尚未实现包装层或 `update` 命令
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
  distribution entrypoint contract。回答未来 reusable install/update/verify/diagnose 包装层必须保持哪些 deploy 语义，以及哪些 packaging 行为尚未实现。
- [agents-adapter-source.md](./agents-adapter-source.md)
  adapter source。回答 `agents` canonical-copy payload descriptor、copied skill files 与 runtime marker 边界。
- [template-consumption-spec.md](./template-consumption-spec.md)
  template contract。回答 `.aw_template/` 中哪些内容属于 `.aw/` 运行管理面，哪些只是待迁移模板。
- [template-tooling-mvp.md](./template-tooling-mvp.md)
  template tooling。回答 B2 当前提供的最小生成 / 校验面。
- [existing-code-adoption.md](./existing-code-adoption.md)
  existing code adoption。回答既有代码库接入 Harness 初始化时，`discovery-input.md` 的生成目标、非 goal truth 边界，以及它和 snapshot / goal / control 的关系。
