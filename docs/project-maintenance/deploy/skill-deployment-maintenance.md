---
title: "Skill Deployment 维护流"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Skill Deployment 维护流

> 目的：提供 deploy target 的只读诊断与恢复分流入口，只管理“先观察什么、怎么判断、何时转回三步重装”。

首次安装或完整重装见 [Deploy Runbook](./deploy-runbook.md)；payload / target / entry 合同见 [Deploy Mapping Spec](./deploy-mapping-spec.md)。

## 推荐维护循环

1. 先用 `diagnose --json` 拿机器可读摘要。
2. 再用 `verify` 做严格只读复验。
3. 如果需要恢复，回到 deploy runbook 执行三步重装。
4. 重装后再跑一次 `diagnose --json` 或 `verify`。

这个顺序只回答一件事：先判断问题类型，再决定是否重装。

## 只读命令角色

| 命令 | 职责 | 退出语义 |
| --- | --- | --- |
| `diagnose --json` | 输出 backend、target root、issue code、conflict / unrecognized 摘要 | 发现 issue 时仍可 `0` 退出 |
| `verify` | 严格复验 source 合法性、target root、live install 对齐、conflict / unrecognized / drift | 发现 issue 时非零退出 |

repo-local 示例：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py diagnose --backend agents --json
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

backend-specific target root override 见 [Codex Usage Help](../usage-help/codex.md) 和 [Claude Usage Help](../usage-help/claude.md)。

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

## 转出

- 已决定重装：回到 [Deploy Runbook](./deploy-runbook.md)。
- 需要正式字段或 trust boundary：看 [Deploy Mapping Spec](./deploy-mapping-spec.md) 和 [Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)。
- 需要 package / npx / tarball smoke 或 release：看 [Testing Runbooks](../testing/README.md) 和 [Governance](../governance/README.md)。
