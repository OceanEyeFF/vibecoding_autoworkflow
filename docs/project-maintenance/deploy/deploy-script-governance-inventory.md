---
title: "Deploy Script Governance Inventory"
status: draft
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Deploy Script Governance Inventory

> 目的：保留 P0-052 后 deploy script surface 的短盘点，说明哪些 Python deploy 面已退出 package/runtime，哪些仍作为 repo-local reference / parity / governance tooling 保留。本页不授权删除代码、修改 package metadata、发布、改 tag、改 remote 或改 `.aw/` 控制面。

当前 deploy 合同 owner：

- wrapper 语义：[Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)
- payload provenance / update trust boundary：[Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)
- mapping 字段：[Deploy Mapping Spec](./deploy-mapping-spec.md)
- toolchain 近代码入口：[`toolchain/scripts/deploy/README.md`](../../../toolchain/scripts/deploy/README.md)

## 当前结论

- 迁移目标是替换 `aw-installer` package/runtime 执行路径上的 Python 依赖，不是清空仓库里的 Python。
- P0-052 已把 package/runtime `aw-installer` Python fallback、`aw-harness-deploy` Python alias，以及 root/local package runtime payload 中的 `adapter_deploy.py` / `harness_deploy.py` 移出分发面。
- `set-harness-goal-skill` skill payload 的 deploy helper 分发面使用 `scripts/deploy_aw.js`；`deploy_aw.py` 只保留为 repo-local reference。
- `adapter_deploy.py`、`harness_deploy.py`、`aw_scaffold.py` 与相关 Python tests 继续作为 repo-local reference / parity / governance tooling 保留。
- runtime no-Python 结论只以 package/local 或 registry-style `aw-installer` 目标执行路径是否需要 Python 为准；仓库中仍有 Python 工具不等于 runtime fallback 未替换。

## 当前分类

| Class | Paths |
| --- | --- |
| removed from package runtime | `toolchain/scripts/deploy/bin/aw-harness-deploy.js` alias、package runtime Python fallback、root package runtime `adapter_deploy.py` / `harness_deploy.py` payload |
| retain reference | `toolchain/scripts/deploy/adapter_deploy.py`、`toolchain/scripts/deploy/harness_deploy.py` |
| retain scaffold | `toolchain/scripts/deploy/aw_scaffold.py`、`toolchain/scripts/deploy/test_aw_scaffold.py` |
| retain runtime owner | `toolchain/scripts/deploy/bin/aw-installer.js`、`toolchain/scripts/deploy/test_aw_installer.js`、`path_safety_policy.json` |
| retain release / package governance | root `package.json`、deploy package metadata、publish helpers、npm pack / npx smoke helpers、release governance tests |
| split later | broad adapter parity tests、CLI/TUI integration tests、adapter contract tests、closeout gate checks |

## 保留的不变量

- `diagnose` 只读，可在报告 issue 时返回 `0`。
- `verify` 只读严格复验，发现 issue 必须失败。
- `update --yes` 只包装 `prune --all -> check_paths_exist -> install -> verify`。
- `prune --all` 只删除当前 backend 可识别、带有效 marker 的受管 install。
- source / target 必须分离；显式 GitHub source 不能变成 channel/self-update/rollback。
- `aw.marker` 只证明 live managed install，不是 source truth 或 remote provenance。
- no-Python runtime claim 必须有 package-local 或 registry-style smoke，并用 failing-Python sentinel 证明目标执行路径没有调用 Python。

## 停止线

- 不删除 repo-local `adapter_deploy.py`、`harness_deploy.py`、`aw_scaffold.py` 或 Python tests，除非有新的专项迁移范围。
- 不修改 release approval lock、version、tag、remote、npm dist-tag、GitHub Release 或 publish workflow，除非经过 release approval。
- 不把 `aw_scaffold.py` 的 `.aw_template` scaffold 语义并入 package/runtime Python removal scope。
- 不在本页继续维护 command surface、source trust、release 或 smoke 的长期规则；这些规则由上方 owner 页承接。
