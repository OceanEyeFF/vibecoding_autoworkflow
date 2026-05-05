---
title: "Deploy Runbook"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Deploy Runbook

> 目的：固定首次安装、完整重装和 destructive reinstall 的 operator 主流程。

本页只管理三步执行路径和停止线。诊断分流见 [Skill Deployment 维护流](./skill-deployment-maintenance.md)；mapping 合同见 [Deploy Mapping Spec](./deploy-mapping-spec.md)；wrapper 语义见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)。

## 什么时候看这页

- 首次给某个 backend 安装当前受管 payload。
- 已有安装，但决定按当前 source 做一次完整重装。
- 只想确认 deploy 主流程是哪三步。

## 主流程

repo-local 参考入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
```

如果当前 backend 需要显式 target root override，就在三条命令上附加对应参数。backend-specific 参数口径见 [Codex Usage Help](../usage-help/codex.md) 和 [Claude Usage Help](../usage-help/claude.md)。

package / local wrapper 必须保持同一 deploy 语义；包装层命令面由 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 管理。

## 三步停止线

| 步骤 | 管什么 | 停止线 |
| --- | --- | --- |
| `prune --all` | 只删除当前 backend 可识别、带有效 `aw.marker` 的受管目录 | 无 marker、marker 不可识别、foreign 或用户目录一律不碰 |
| `check_paths_exist` | 基于当前 live bindings 做写入前冲突扫描 | 任一路径已存在就失败；不写业务文件，也不替 operator 判断是否覆盖 |
| `install --backend <backend>` | 只写当前 source 声明的 live payload | source contract 非法、重复 `target_dir` 或冲突未清理时，必须写入前失败 |

## 常见恢复口径

| 现象 | 处理口径 |
| --- | --- |
| `check_paths_exist` 报冲突 | 先手工清理冲突目录，再从 `prune --all` 重跑 |
| `install` 在写入前失败 | 先修 source contract，再从 `prune --all` 重跑 |
| 想确认重装后是否干净 | 转到 [Skill Deployment 维护流](./skill-deployment-maintenance.md) 跑 `diagnose` 或 `verify` |

## 转出

- drift / conflict / unrecognized 的具体含义：看 [Skill Deployment 维护流](./skill-deployment-maintenance.md)。
- source / payload / target 字段合同：看 [Deploy Mapping Spec](./deploy-mapping-spec.md)。
- source root / target root / GitHub source 边界：看 [Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)。
- pack、tarball smoke、registry smoke 或 release：看 [Testing Runbooks](../testing/README.md) 和 [Governance](../governance/README.md)。
