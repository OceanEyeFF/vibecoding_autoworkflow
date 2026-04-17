# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库面向操作者的 deploy / verify / maintenance 文档。这里承接的是 backend target root 的 destructive reinstall model：先清理我方受管安装物，再检查冲突路径，最后只写入当前 source 声明的 live payload。canonical skill 真相仍在 `product/`，`.aw_template/` 也不是 deploy payload source。

这里适合放：

- backend target root、入口命令与主流程
- `prune --all -> check_paths_exist -> install --backend agents` 的操作口径
- 只读 `verify` 的诊断闭环
- canonical source 到 backend payload / target entry 的映射合同
- `.aw_template/` 的 `.aw/` 使用合同与边界

这里不适合放：

- canonical skill 真相正文
- archive / history / old-version keepalive 方案
- 旧 `local/global` deploy mode 的主流程说明
- research runner 或评测主流程

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我要给当前 backend 做一次完整重装 | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留 `prune --all` / `check_paths_exist` / `install` 三步主流程，`verify` 作为辅助复验 |
| 我想看 canonical source 到 target entry 的正式映射 | [deploy-mapping-spec.md](./deploy-mapping-spec.md) | 最小 deploy 合同，定义 canonical source / backend payload source / manifest / target / verify |
| 我想看 B1 的过渡性 manifest 读取面和边界 | [skill-manifest-schema.md](./skill-manifest-schema.md) | B1 只固定 canonical read-surface schema 与首发冻结投影；不是 deploy 主流程正文 |
| 我想看 `agents` thin-shell payload source 怎么组织 | [agents-adapter-source.md](./agents-adapter-source.md) | 定义 `product/harness/adapters/agents/skills/` 的 payload source 结构与 thin-shell 约束 |
| 我想看首发实现阶段到底只承接哪些 skill 和分支子集 | [first-wave-skill-freeze.md](./first-wave-skill-freeze.md) | 前瞻性实现约束；回答首发纳入哪些 canonical skills 与可达分支子集 |
| 我想初始化 `.aw/` 样例并校验 `.aw_template` 最小结构 | [template-tooling-mvp.md](./template-tooling-mvp.md) | B2 的最小工作面，只做 `.aw_template -> .aw` 样例生成与前置校验 |
| 我已有安装，想诊断 drift / conflict / unrecognized 目录 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 解释只读 `verify`、冲突扫描和 destructive reinstall 恢复口径 |
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
- `verify --backend agents` 保留为只读辅助命令，用于检查 source 合法性、target root 状态、live install 对齐，以及 conflict / unrecognized 情形
- 不再承接这些主线语义：
  - `retired-target-dir`
  - `prune --outdated`
  - archive / history
  - 增量修复
  - 旧版本保活
  - “确认新目录可用再删旧目录”
  - `local/global` deploy modes
- `aw.marker` 是 runtime-generated artifact，只用于标识“这是当前 backend 受管的 live install 目录”；它不是 source truth，也不是历史接管记录
- deploy target 不是 source of truth。skills / manifests / payload source 的正式 owner 仍在 `product/`
- 当前 B2 初始化工具只处理 `.aw_template -> .aw` 样例，不消费 `manifest`、不生成 payload，也不写入 deploy target
- `docs/harness/` 继续承接 Harness doctrine；deploy 文档只定义 operator-facing deploy 合同
- `.aw_template/` 的 `.aw/` 目录结构、管理文档模板和待迁移模板边界见 [template-consumption-spec.md](./template-consumption-spec.md)

## 页面职责

- [deploy-runbook.md](./deploy-runbook.md)
  quick start。回答 destructive reinstall 主流程和最小复验。
- [skill-lifecycle.md](./skill-lifecycle.md)
  lifecycle。回答为什么 deploy 不承接 add / update / rename / remove 的业务同步决策。
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
  maintenance / diagnosis。回答只读 `verify`、冲突扫描、drift 与恢复路径。
- [deploy-mapping-spec.md](./deploy-mapping-spec.md)
  mapping contract。回答 canonical source / backend payload source / manifest / target / verify 的最小正式规则。
- [skill-manifest-schema.md](./skill-manifest-schema.md)
  manifest schema。回答 B1 的过渡性 manifest 读取面与冻结投影。
- [agents-adapter-source.md](./agents-adapter-source.md)
  adapter source。回答 `agents` thin-shell payload source 目录、descriptor 与 runtime marker 边界。
- [first-wave-skill-freeze.md](./first-wave-skill-freeze.md)
  first-wave freeze。回答首发 skill 范围与支持分支子集；它是前瞻性约束，不是 deploy 行为说明。
- [template-consumption-spec.md](./template-consumption-spec.md)
  template contract。回答 `.aw_template/` 中哪些内容属于 `.aw/` 运行管理面，哪些只是待迁移模板。
- [template-tooling-mvp.md](./template-tooling-mvp.md)
  template tooling。回答 B2 当前提供的最小生成 / 校验面。
