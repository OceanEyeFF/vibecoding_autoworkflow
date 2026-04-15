# Deploy Runbooks

`docs/project-maintenance/deploy/` 只保存当前仓库的 operator-facing deploy / verify / maintenance 文档。这里现在只解释 runtime target root 怎么激活、怎么复验、怎么诊断 root 层 drift，不承接 canonical skill 合同正文，也不定义 skills 与 `.aw_template/` 的映射结构。

这里适合放：

- 当前仓库的 deploy backend、target root 和入口命令
- runtime target root 的最小激活与复验路径
- `verify` 与 root drift 的诊断闭环
- 当前哪些 backend 已实现，哪些暂不实现

这里不适合放：

- canonical skill 真相正文
- skills 与 `.aw_template/` 的业务映射方案
- 尚未实现 backend 的安装细节
- research runner 或评测主流程

## 按问题进入

| 你要回答什么问题 | 先看哪里 | 说明 |
|---|---|---|
| 我第一次激活当前 runtime target root | [deploy-runbook.md](./deploy-runbook.md) | Quick Start，只保留 local/global root 激活与最小复验 |
| 我已有 root，只想复验 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 按 `verify -> endpoint -> verify` 做 |
| 我看到 drift / `wrong-target-root-type` | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 这里集中解释 root 级错误信号和恢复口径 |
| 我在改 skills 或 `.aw_template/` | [skill-lifecycle.md](./skill-lifecycle.md) | 这里说明当前 deploy 不承接这些业务变化 |
| 我想看 backend 当前实现状态 | [deploy-runbook.md](./deploy-runbook.md) | 这里只保留 `agents` 已实现、`claude/opencode` 暂未实现的状态说明 |

## 当前执行边界

- 当前 deploy 工具只实现 `agents`
- 当前 deploy 工具只管理 target root，不复制或比对 skill 内容
- `docs/harness/` 继续承接 Harness doctrine；deploy 文档不定义 `.aw_template/` 与 canonical skills 的最终映射关系
- `adapter_deploy.py` 只保留 runtime endpoint，不承接 skills/source 的业务同步

## 页面职责

- [deploy-runbook.md](./deploy-runbook.md)
  quick start。回答首次激活、repo-local / global target 对照与最小复验。
- [skill-lifecycle.md](./skill-lifecycle.md)
  lifecycle。回答为什么当前 deploy 不承接 add / update / rename / remove 的业务同步。
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
  maintenance / diagnosis。回答只读 `verify`、root drift 类型，以及 local/global verify 的不同关注点。
