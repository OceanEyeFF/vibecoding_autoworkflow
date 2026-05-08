---
title: "Deploy Script Governance Inventory"
status: superseded
updated: 2026-05-08
owner: aw-kernel
last_verified: 2026-05-08
---
# Deploy Script Governance Inventory

> 目的：保留 Python deploy 面删除前的盘点和设计边界。本文已被 2026-05-08 的 Node-only deploy 实现取代；当前事实以 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)、[Deploy Runbook](./deploy-runbook.md) 与代码为准。

合同 owner：wrapper -> [Entrypoint Contract](./distribution-entrypoint-contract.md)；provenance/trust -> [Payload Provenance](./payload-provenance-trust-boundary.md)；mapping -> [Mapping Spec](./deploy-mapping-spec.md)；近代码 -> [toolchain/scripts/deploy/README.md](../../../toolchain/scripts/deploy/README.md)。

## 当前结论

本文的迁移 inventory 已完成其决策用途。Python deploy implementation 已删除，`aw-installer` 是当前 deploy runtime 入口（Node-only distribution）；release metadata、version bump、npm publish、tag、dist-tag、GitHub Release 或 remote mutation 仍属于 release boundary，需要新的显式审批和独立 gate。

## 当前分类

| Class | Paths |
| --- | --- |
| removed from package runtime | `toolchain/scripts/deploy/bin/aw-harness-deploy.js` alias、package runtime Python fallback、root package runtime `adapter_deploy.py`/`harness_deploy.py` payload |
| retain reference | `adapter_deploy.py`、`harness_deploy.py` |
| retain scaffold | `aw_scaffold.py`、`test_aw_scaffold.py` |
| retain runtime owner | `bin/aw-installer.js`、`test_aw_installer.js`、`path_safety_policy.json` |
| retain release/package governance | root `package.json`、deploy package metadata、publish helpers、npm pack/npx smoke helpers、release governance tests |
| split later | broad adapter parity tests、CLI/TUI integration tests、adapter contract tests、closeout gate checks |

## 保留的不变量

- `diagnose` 只读，报告 issue 时可返回 `0`
- `verify` 只读严格复验，发现 issue 必须失败
- `update --yes` 只包装 `prune --all -> check_paths_exist -> install -> verify`
- `prune --all` 只删除当前 backend 可识别、带有效 marker 的受管 install
- source/target 必须分离；显式 GitHub source 不能变成 channel/self-update/rollback
- `aw.marker` 只证明 live managed install，非 source truth 或 remote provenance
- no-Python runtime claim 必须有 package-local 或 registry-style smoke，并用 failing-Python sentinel 证明

## 停止线

- 不删除 repo-local `adapter_deploy.py`、`harness_deploy.py`、`aw_scaffold.py` 或 Python tests，除非新专项迁移
- 不修改 release approval lock、version、tag、remote、npm dist-tag、GitHub Release 或 publish workflow，除非经 release approval
- 不把 `aw_scaffold.py` 的 `.aw_template` scaffold 并入 package/runtime Python removal scope
- 本页不维护 command surface、source trust、release 或 smoke 的长期规则；由 owner 页承接
