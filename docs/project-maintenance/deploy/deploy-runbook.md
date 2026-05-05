---
title: "Deploy Runbook"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Deploy Runbook

> 目的：固定当前 deploy 主流程，只管理“首次安装 / 完整重装 / destructive reinstall”的执行路径。

本页属于 [Deploy Runbooks](./README.md)。

## 本页管理什么

- 三步主流程：`prune --all -> check_paths_exist -> install --backend <backend>`
- 什么时候应该直接重装，而不是继续猜测修补
- 这三步各自的停止线

## 本页不管理什么

- `diagnose` / `verify` 的故障分流细节：见 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- canonical source / payload / target contract：见 [deploy-mapping-spec.md](./deploy-mapping-spec.md)
- package / CLI / TUI 包装层语义：见 [distribution-entrypoint-contract.md](./distribution-entrypoint-contract.md)
- 发布准入、packlist、registry smoke：见 [aw-installer Pre-Publish Governance](../governance/aw-installer-pre-publish-governance.md)、[Governance](../governance/README.md)、[Testing Runbooks](../testing/README.md)

## 什么时候看这页

- 首次给某个 backend 安装当前受管 payload
- 已有安装，但决定按当前 source 做一次完整重装
- 你只想知道 deploy 主流程到底是哪三步

## 主流程

repo-local 参考入口：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
```

如果当前 backend 需要显式 target root override，就在三条命令上附加对应参数。参数口径见 [Codex Usage Help](../usage-help/codex.md) 和 [Claude Usage Help](../usage-help/claude.md)。

package / local wrapper 必须保持同一语义，但包装层命令面由 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md) 管理，而不是本页。

## 三步各管什么

### 1. `prune --all`

- 只删除当前 backend 受管、且带可识别 `aw.marker` 的目录
- 无 marker、marker 不可识别或 foreign 目录一律不碰
- 这是显式清场步骤，不负责保留旧版本、副本或历史目录

### 2. `check_paths_exist`

- 基于当前 live bindings 解析目标路径
- 只要任一路径已存在，就列出冲突并失败退出
- 这一步不写业务文件，也不替 operator 判断“能不能覆盖”

### 3. `install --backend <backend>`

- 只写当前 source 声明的 live payload
- 如果 source contract 非法，例如重复 `target_dir`，必须在写入前失败
- 如果冲突路径未清理完，也必须在写入前失败

## 只读辅助命令

本页不把 `diagnose` / `verify` 作为主流程，但它们仍然是常用辅助命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py diagnose --backend agents --json
PYTHONDONTWRITEBYTECODE=1 python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

- `diagnose` 只读输出状态摘要，发现 issue 时仍以 `0` 退出
- `verify` 做严格只读复验，发现 issue 时非零退出
- 如何根据 issue 决定恢复路径，由 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md) 管理

## 停止线

出现以下情况时，不要继续在本页硬做：

- 你需要判断 drift / conflict / unrecognized 的具体含义
- 你需要区分 source 问题、target 问题还是 live install 问题
- 你需要发布、pack、tarball smoke 或 registry smoke

分别转到：

- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- [aw-installer Pre-Publish Governance](../governance/aw-installer-pre-publish-governance.md)
- [Governance](../governance/README.md)
- [npx Command Test Execution](../testing/npx-command-test-execution.md)

## 常见恢复口径

| 现象 | 处理口径 |
| --- | --- |
| `check_paths_exist` 报冲突 | 先手工清理冲突目录，再从 `prune --all` 重跑 |
| `install` 在写入前失败 | 先修 source contract，再从 `prune --all` 重跑 |
| 想确认重装后是否干净 | 转到 maintenance 页跑 `diagnose` 或 `verify` |

## 相关文档

- [Skill Deployment 维护流](./skill-deployment-maintenance.md)
- [Deploy Mapping Spec](./deploy-mapping-spec.md)
- [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)
- [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)
