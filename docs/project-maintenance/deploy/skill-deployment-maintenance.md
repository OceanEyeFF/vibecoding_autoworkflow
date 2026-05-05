---
title: "Skill Deployment 维护流"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Skill Deployment 维护流

> 目的：提供 deploy target 的只读诊断与恢复分流入口，只管理“先观察什么、怎么判断、何时转回三步重装”。

本页属于 [Deploy Runbooks](./README.md)。

## 本页管理什么

- `diagnose` 与 `verify` 的角色分工
- 常见故障信号的分流口径
- 什么时候应回到 [deploy-runbook.md](./deploy-runbook.md) 做完整重装

## 本页不管理什么

- 首次安装或完整重装的三步执行细节：见 [deploy-runbook.md](./deploy-runbook.md)
- payload / target / entry 的正式合同：见 [deploy-mapping-spec.md](./deploy-mapping-spec.md)
- 发布前检查、merge PR、GitHub Release、registry smoke：见相关 release / testing 文档

## 推荐维护循环

默认顺序：

1. 先用 `diagnose --json` 拿机器可读摘要
2. 再用 `verify` 做严格只读复验
3. 如果需要恢复，回到 deploy runbook 执行三步重装
4. 重装后再跑一次 `diagnose --json` 或 `verify`

这个顺序只回答一件事：先判断问题类型，再决定是否重装，不在 maintenance 页面直接接管安装流程。

## 只读命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py diagnose --backend agents --json
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

如果 backend 需要显式 target root override，就在命令上附加对应参数。参数口径见 [Codex Usage Help](../usage-help/codex.md) 和 [Claude Usage Help](../usage-help/claude.md)。

## 两个命令的职责

### `diagnose --json`

- 只读状态摘要
- 输出 backend、target root、issue code、conflict / unrecognized 摘要
- 即使发现 issue，也以 `0` 退出
- 适合 operator 先观察，或给外层自动化消费

### `verify`

- 只读严格复验
- 检查 source 合法性、target root 结构、live install 对齐状态
- 检查 conflict / unrecognized / drift
- 发现 issue 时非零退出

## 信号分流

| 信号或症状 | 优先处理方式 |
| --- | --- |
| `missing-target-root` | 直接回到 deploy runbook，执行三步重装 |
| `wrong-target-root-type` | 先修正 target root 形态，再执行三步重装 |
| `broken-target-root-symlink` | 删除坏链路后执行三步重装 |
| `duplicate target_dir` | 这是 source contract 问题，先修 source，不要在 target 侧硬修 |
| `payload-contract-invalid` / `missing-canonical-source` / `missing-backend-payload-source` | 回到 source 层修 contract 或缺件，再执行三步重装 |
| `check_paths_exist` 冲突清单 | 先手工清理占位目录，再执行三步重装 |
| `unrecognized-target-directory` | 不让脚本猜测处理；先人工确认保留、改名或删除 |
| `target-payload-drift` / `missing-target-entry` / `missing-required-payload` | 默认按完整重装恢复，除非你已经确认是更上游的 source 问题 |

## 停止线

出现下面任一情况时，本页只负责分流，不继续展开：

- 你已经决定重装
- 你需要 payload/source/target 的正式边界
- 你需要 package / npx / tarball smoke
- 你在做 release candidate 或真实 publish

分别转到：

- [deploy-runbook.md](./deploy-runbook.md)
- [deploy-mapping-spec.md](./deploy-mapping-spec.md)
- [npx Command Test Execution](../testing/npx-command-test-execution.md)
- [aw-installer Pre-Publish Governance](../governance/aw-installer-pre-publish-governance.md)

## 相关文档

- [Deploy Runbook](./deploy-runbook.md)
- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)
