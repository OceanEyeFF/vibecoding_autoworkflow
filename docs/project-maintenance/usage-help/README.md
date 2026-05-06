# Usage Help

`docs/project-maintenance/usage-help/` 保存新 operator 推荐使用路径，以及按 backend 聚合的使用帮助：target root 解析、override 参数、验证口径、部署后使用、source 变更后 operator 决策。不再按 `memory-side/` 或 `task-interface/` 拆子目录。

## 推荐入口

- [recommended-usage.md](./recommended-usage.md)：新用户先读，按推荐顺序完成 backend 选择、readiness / install check、Harness 初始化、bounded worktrack 推进、SubAgent 使用、verify/gate/closeout 和审批边界确认。

## 按 backend 进入

| backend | 页面 | 主要差异 |
|---|---|---|
| `agents` | [codex.md](./codex.md) | 默认 `.agents/skills/`、copy-paste quickstart、source 变更决策、Codex Harness manual run |
| `claude` | [claude.md](./claude.md) | Claude runtime 路径、copy-paste quickstart、source 变更决策、冷启动 runbook |

## 和 Deploy 文档的分工

- 通用 deploy 入口：[deploy/README.md](../deploy/README.md)
- destructive reinstall 主流程：[deploy-runbook.md](../deploy/deploy-runbook.md)
- 外部试用复制粘贴路径：直接看当前 backend 的 usage-help 页面
- 外部试用反馈模板：[trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 与 [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)
- registry npx 验证、反馈日志与多临时 workdir 验证：[npx Command Test Execution](../testing/npx-command-test-execution.md)
- drift、冲突扫描、故障诊断：[skill-deployment-maintenance.md](../deploy/skill-deployment-maintenance.md)
- add/update/rename/remove：看当前 backend 的 usage-help 页面

当前 public/near-public trial 主路径仍是 `agents` backend；Claude Code 可安装完整 Harness skill payload，但仍作为 Claude 适配 lane。
