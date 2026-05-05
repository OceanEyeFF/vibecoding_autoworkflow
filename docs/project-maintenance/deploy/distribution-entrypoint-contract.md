---
title: "Distribution Entrypoint Contract"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# Distribution Entrypoint Contract

> 目的：固定 `aw-installer` 作为 deploy 分发入口必须保持的 wrapper 语义。

本页属于 [Deploy Runbooks](./README.md)。

## 本页管理什么

- `aw-installer` 必须保持的命令不变量
- CLI / TUI 不能分叉的语义
- package/runtime 当前支持的 backend 暴露口径

## 本页不管理什么

- release channel 与 publish 准入：见 [aw-installer Release Channel Governance](../governance/aw-installer-release-channel-governance.md)
- source root / target root / GitHub source archive trust boundary：见 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)
- canonical source 到 target 的正式映射：见 [Deploy Mapping Spec](./deploy-mapping-spec.md)

## 当前 package/runtime surface

- bin surface 是 `aw-installer`
- 当前 package/runtime 支持 `agents` 与 `claude`
- 未支持的 backend 或命令变体必须显式失败
- CLI 可以作为稳定脚本接口，TUI 只能是同一合同上的交互层

## 命令面合同

| mode | 必须保持的语义 |
| --- | --- |
| `diagnose` | 只读状态摘要；可返回 `0` 并报告 issue |
| `verify` | 只读严格复验；发现 issue 时失败 |
| `prune --all` | 只删除当前 backend 可识别的受管目录 |
| `check_paths_exist` | 写入前全量冲突扫描；失败时零业务写入 |
| `install` | 只写当前 source 声明的 live payload |
| `update` | 默认只输出 dry-run plan；`--yes` 才执行 `prune -> check_paths_exist -> install -> verify` |

wrapper 可以改变启动方式，但不能改变这些 deploy 语义。

## CLI / TUI 双模式

- CLI 是稳定脚本化接口
- TUI 只是同一合同上的交互层
- TUI 不得拥有独立于 CLI 的 install / update 语义
- 所有 mutating TUI 动作都必须映射到明确的 CLI mode
- 非交互环境不得隐式启动 TUI
- `--json` 只属于 CLI 机器输出，不得混入交互渲染

## 必须保持的不变量

- `diagnose` 与 `verify` 都是只读命令
- `diagnose` 不是安装成功证明；严格失败信号只能来自 `verify`
- mutating install 仍然表达为 `prune --all -> check_paths_exist -> install`
- `update --yes` 只能是这条链路的 one-shot 包装
- `check_paths_exist` 失败时不得写业务文件
- wrapper 不得把 deploy target 当成 source of truth

## 与其他页面的边界

- source / target 根解析、GitHub source archive、allowed source kinds 由 [aw-installer Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md) 管理
- target entry、payload descriptor、required payload files 由 [Deploy Mapping Spec](./deploy-mapping-spec.md) 管理
- operator 执行步骤由 [Deploy Runbook](./deploy-runbook.md) 管理

## 停止线

如果问题已经进入 release channel、payload source 设计或 target root trust boundary，本页不再展开。
