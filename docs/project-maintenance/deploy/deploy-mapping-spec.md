---
title: "Deploy Mapping Spec"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Deploy Mapping Spec

> 目的：定义 destructive reinstall model 下 `canonical source -> backend payload source -> target entry -> verify` 的最小映射合同。

本页只管理映射链路、payload descriptor 最小字段，以及 deploy 命令依赖这些字段做什么。operator 步骤见 [Deploy Runbook](./deploy-runbook.md)；wrapper 入口语义见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)；source / target trust boundary 见 [Payload Provenance And Update Trust Boundary](./payload-provenance-trust-boundary.md)。

## 映射链路

`canonical source -> backend payload source -> payload descriptor -> target entry -> verify`

- `canonical source` 是唯一 truth，owner 在 `product/harness/skills/`。
- `backend payload source` 是后端分发载体，owner 在 `product/harness/adapters/<backend>/skills/`。
- `payload descriptor` 只描述分发与校验所需的最小信息。
- `target entry` 是 target root 下的 live install 落点，不回写 source。

## 最小字段

| 字段 | 最小要求 |
| --- | --- |
| `canonical_dir` | 相对 repo root 的安全路径，能唯一定位 canonical source |
| `skill_id` | 在 canonical source、payload descriptor、target entry 之间保持稳定身份 |
| `target_dir` | 相对 target root 的安全路径；live bindings 内必须唯一 |
| `target_entry_name` | 能唯一标识运行时入口 |
| `required_payload_files` | 显式列出严格复验所需的最小文件 |
| policy fields | 显式声明 copy / frontmatter transform / legacy cleanup 等策略 |

`canonical_dir`、`target_dir`、`target_entry_name` 和 `required_payload_files` 都必须是安全相对路径，不能跳出各自根目录。

## 当前稳定 target 命名

| backend | 当前稳定 `target_dir` 约定 |
| --- | --- |
| `agents` | `aw-{skill_id}` |
| `claude` | `{skill_id}` |

backend-specific payload 细节属于 adapter 源，不在本页展开。

## 命令读取面

- `check_paths_exist` 只读取当前 source 声明的目标路径，用于写入前冲突扫描。
- `diagnose` 与 `verify` 读取同一套映射信息，但退出语义不同。
- `install` 只写当前 descriptor 声明的 live payload。

最小读取项：

- source 是否合法，例如是否出现重复 `target_dir`。
- target entry 与 `required_payload_files` 是否存在且类型正确。
- payload descriptor 身份字段是否与当前 binding 一致。
- live install 是否与当前 source 对齐。

## 不变量

- target entry 与 runtime payload 都不是 source of truth。
- live bindings 内 `target_dir` 必须唯一，不能靠覆盖顺序解决冲突。
- 映射合同服务于 destructive reinstall，不承接 archive、history 或 release channel 语义。
- backend-specific 实现细节应写在 adapter 近代码说明，不在 deploy 主线重复展开。
