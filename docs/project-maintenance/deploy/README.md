# Deploy Runbooks

`docs/project-maintenance/deploy/` 只承接 deploy 主路径与部署后维护。发布治理、外部试用治理和 backend 使用说明已逐步迁出。

测试执行、本地 `.tgz` smoke、registry `npx` smoke、Codex / Claude 部署后行为观察统一放在 [Testing Runbooks](../testing/README.md)。

## 单一管理原则

| 文档 | 只管理什么 | 不再管理什么 |
| --- | --- | --- |
| [deploy-runbook.md](./deploy-runbook.md) | 首次安装与完整重装的三步主流程 | 诊断分流、发布流程、pack / smoke 细节 |
| [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | `diagnose` / `verify` 与恢复分流 | 首次安装、发布、testing 执行 |
| [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) | `aw-installer` CLI / TUI 包装层语义 | operator runbook、发布步骤 |
| [deploy-mapping-spec.md](./deploy-mapping-spec.md) | canonical source / payload / target 映射合同 | operator 执行步骤、release 流程 |
| [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md) | payload source kind、source/target root、GitHub source trust boundary | release channel、任意 remote update |
| [existing-code-adoption.md](./existing-code-adoption.md) | 既有代码库接入 Harness 时的 `.aw/repo/discovery-input.md` 生成边界 | artifact 正文、skill workflow 实现 |
| [template-consumption-spec.md](./template-consumption-spec.md) | legacy `.aw_template/` 的 deploy 边界 | `aw_scaffold.py` 命令面、artifact 合同 |

## 按问题进入

| 问题 | 入口 | 说明 |
| --- | --- | --- |
| 我要给当前 backend 做首次安装或完整重装 | [deploy-runbook.md](./deploy-runbook.md) | 只保留三步主流程和停止线 |
| 我已有安装，想判断 drift / conflict / unrecognized 怎么处理 | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | 只管理只读诊断与恢复分流 |
| 我想确认 canonical source 到 target 的正式映射 | [deploy-mapping-spec.md](./deploy-mapping-spec.md) | 正式合同页 |
| 我想确认 package / CLI / TUI 必须保持什么语义 | [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) | 包装层合同页 |
| 我想看 payload provenance 与 update trust boundary | [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md) | source / target / remote source 边界 |
| 我要把已有代码库接入 Harness 初始化流程 | [existing-code-adoption.md](./existing-code-adoption.md) | 只看 operator-facing adoption 生成边界 |
| 我想确认 `.aw_template/` 还能不能当 deploy source | [template-consumption-spec.md](./template-consumption-spec.md) | 只看 legacy scaffold 边界 |
| 我在改 skills 或 `.aw_template/` 后，想知道 operator 该怎么处理 | [Usage Help](../usage-help/README.md) | source 变更后的 operator 决策已迁到 usage-help |
| 我需要 package / registry smoke 或部署后行为观察 | [Testing Runbooks](../testing/README.md) | 测试执行统一入口 |
| 我想确认发布准入、发布顺序或试用治理 | [Governance](../governance/README.md) | 发布治理已迁出 deploy |

## 当前主线口径

- 安装主流程、wrapper 语义、mapping 和 trust boundary 分别由上表合同页承接。
- deploy target 不是 source of truth；canonical truth 仍在 `product/`。
- release、testing、usage help 不在 deploy 下保留副本。

## 不再承接的内容

`docs/project-maintenance/deploy/` 不再保存：

- 一次性 release approval package
- historical smoke evidence
- Codex / Claude 行为测试记录副本
- registry `npx` smoke runbook 副本
- 同一主题在多个页面的双主线说明
