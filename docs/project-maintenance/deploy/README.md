# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库面向操作者的部署 / 验证 / 维护文档。这里负责激活 runtime target root（运行时目标根目录）、复验和诊断，也负责 deploy 映射正式合同和 `.aw_template/` 的 `.aw/` 使用合同；canonical skill 本体仍在 `product/`，`.aw_template/` 不作为 deploy payload source（部署负载来源）。

这里适合放：

- 当前仓库的 deploy backend、target root 和入口命令
- runtime target root 的最小激活与复验路径
- `verify` 与 root drift（根目录偏离）的诊断闭环
- canonical source 到 target entry 的最小映射合同
- `.aw_template/` 的 `.aw/` 目录结构、管理文档模板与边界
- 当前哪些 backend 已实现，哪些暂不实现

这里不适合放：

- canonical skill 真相正文
- `.aw_template/` 的生成系统或运行细节
- 尚未实现 backend 的安装细节
- research runner 或评测主流程

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我第一次激活当前 runtime target root | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留 local/global root 激活与最小复验 |
| 我想看 canonical source 到 target entry 的正式映射 | [deploy-mapping-spec.md](./deploy-mapping-spec.md) | 最小 deploy 合同，定义 canonical source / backend payload source / manifest / target / verify |
| 我想看首发实现阶段到底只承接哪些 skill 和分支子集 | [first-wave-skill-freeze.md](./first-wave-skill-freeze.md) | 前瞻性实现约束；回答首发纳入哪些 canonical skills 与可达分支子集，不描述当前 deploy 已实现行为 |
| 我已有 root，只想复验 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 按 `verify -> endpoint -> verify` 做 |
| 我看到 drift / `wrong-target-root-type` | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 这里集中解释 root 级错误信号和恢复口径 |
| 我在改 skills 或 `.aw_template/` | [skill-lifecycle.md](./skill-lifecycle.md) | 这里说明 lifecycle（生命周期）边界；`.aw_template/` 不作为 deploy payload source |
| 我想看 backend 当前实现状态 | [deploy-runbook.md](./deploy-runbook.md) | 这里只保留 `agents` 已实现、`claude/opencode` 暂未实现的状态说明 |

## 当前执行边界

- 当前 deploy 工具只实现 `agents`
- 当前 deploy 工具只管理 target root，不复制或比对 skill 内容
- `docs/harness/` 继续承接 Harness doctrine；deploy 文档只定义 operator-facing（面向操作者）的 deploy 映射合同，不定义 skill doctrine
- `adapter_deploy.py` 只保留 runtime endpoint，不承接 skills/source 的业务同步
- `.aw_template/` 的 `.aw/` 目录结构、管理文档模板和待迁移模板边界见 [template-consumption-spec.md](./template-consumption-spec.md)

## 页面职责

- [deploy-runbook.md](./deploy-runbook.md)
  quick start。回答首次激活、repo-local / global target 对照与最小复验。
- [skill-lifecycle.md](./skill-lifecycle.md)
  lifecycle。回答为什么当前 deploy 不承接 add / update / rename / remove 的业务同步。
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
  maintenance / diagnosis。回答只读 `verify`、root drift 类型，以及 local/global verify 的不同关注点。
- [deploy-mapping-spec.md](./deploy-mapping-spec.md)
  mapping contract。回答 canonical source / backend payload source / manifest / target / verify 的最小正式规则。
- [first-wave-skill-freeze.md](./first-wave-skill-freeze.md)
  first-wave freeze。回答首发实现阶段的 skill 范围与支持分支子集；它是 B1-B4 的前瞻性约束，不是当前 deploy 行为说明。
- [template-consumption-spec.md](./template-consumption-spec.md)
  template contract。回答 `.aw_template/` 中哪些内容属于 `.aw/` 运行管理面，哪些只是待迁移模板，以及 owner 重定前的使用规则。
