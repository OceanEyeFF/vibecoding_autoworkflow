# Deploy Runbooks

`docs/project-maintenance/deploy/` 只包含 deploy 主路径与部署后维护。发布治理、外部试用治理和 backend 使用说明已逐步迁出。测试执行、本地 `.tgz` smoke、registry `npx` smoke、Codex/Claude 部署后行为观察统一放在 [Testing Runbooks](../testing/README.md)。

## 单一管理原则

| 文档 | 只管理什么 | 不再管理什么 |
| --- | --- | --- |
| [deploy-runbook.md](./deploy-runbook.md) | 首次安装与完整重装的三步主流程 | 诊断分流、发布流程、pack/smoke 细节 |
| [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) | `diagnose`/`verify` 与恢复分流 | 首次安装、发布、testing 执行 |
| [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) | `aw-installer` CLI/TUI 包装层语义 | operator runbook、发布步骤 |
| [deploy-mapping-spec.md](./deploy-mapping-spec.md) | canonical source/payload/target 映射合同 | operator 执行步骤、release 流程 |
| [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md) | payload source kind、source/target root、GitHub source trust boundary | release channel、任意 remote update |
| [existing-code-adoption.md](./existing-code-adoption.md) | 既有代码库接入 Harness 时的 `.aw/repo/discovery-input.md` 生成边界 | artifact 正文、skill workflow 实现 |
| [template-consumption-spec.md](./template-consumption-spec.md) | legacy `.aw_template/` 的 deploy 边界 | scaffold 命令面（已移除）、artifact 合同 |

## 按问题进入

| 问题 | 入口 |
| --- | --- |
| 首次安装或完整重装 | [deploy-runbook.md](./deploy-runbook.md) |
| 已有安装，判断 drift/conflict/unrecognized | [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) |
| 确认 canonical source 到 target 的正式映射 | [deploy-mapping-spec.md](./deploy-mapping-spec.md) |
| 确认 package/CLI/TUI 必须保持的语义 | [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md) |
| 查看 payload provenance 与 update trust boundary | [payload-provenance-trust-boundary.md](./payload-provenance-trust-boundary.md) |
| 既有代码库接入 Harness | [existing-code-adoption.md](./existing-code-adoption.md) |
| 确认 `.aw_template/` 的 deploy 边界 | [template-consumption-spec.md](./template-consumption-spec.md) |
| 改 skills 或 `.aw_template/` 后的 operator 决策 | [Usage Help](../usage-help/README.md) |
| package/registry smoke 或部署后行为观察 | [Testing Runbooks](../testing/README.md) |
| 发布准入、发布顺序或试用治理 | [Governance](../governance/README.md) |

## 当前主线口径

安装主流程、wrapper、mapping、trust boundary 由各自合同页承接；deploy target 不是 source of truth；release/testing/usage help 不在 deploy 下留副本。

## 不再承接的内容

不再保存一次性 release approval、historical smoke evidence、Codex/Claude 行为测试副本、registry `npx` smoke runbook 副本、以及多页面双主线说明。

## 历史参考

- [deploy-script-governance-inventory.md](./deploy-script-governance-inventory.md) (superseded) — Python deploy 面删除前的盘点与设计边界
