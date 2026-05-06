---
title: "Deploy Mapping Spec"
status: active
updated: 2026-05-06
owner: aw-kernel
last_verified: 2026-05-06
---
# Deploy Mapping Spec

> 目的：定义 destructive reinstall model 下 `canonical source -> backend payload source -> target entry -> verify` 的最小映射合同。

本页只管理映射链路、payload descriptor 最小字段及命令依赖；operator 步骤、wrapper 语义、trust boundary 见相邻文档。

## 映射链路

`canonical source -> backend payload source -> payload descriptor -> target entry -> verify`；canonical source 是唯一 truth（`product/harness/skills/`），backend payload source 是分发载体（`adapters/<backend>/skills/`），payload descriptor 只描述分发所需信息，target entry 是 live install 落点且不回写 source。

## 最小字段

| 字段 | 最小要求 |
| --- | --- |
| `canonical_dir` | 相对 repo root 的安全路径，唯一定位 canonical source |
| `skill_id` | 在 canonical source、payload descriptor、target entry 间保持稳定身份 |
| `target_dir` | 相对 target root 的安全路径；live bindings 内必须唯一 |
| `target_entry_name` | 唯一标识运行时入口 |
| `required_payload_files` | 显式列出严格复验所需的最小文件 |
| policy fields | 显式声明 copy/frontmatter transform/legacy cleanup 等策略 |

`canonical_dir`、`target_dir`、`target_entry_name`、`required_payload_files` 都必须是安全相对路径，不跳出各自根目录。

## 当前稳定 target 命名

| backend | 当前稳定 `target_dir` 约定 |
| --- | --- |
| `agents` | `aw-{skill_id}` |
| `claude` | `{skill_id}` |

## 命令读取面

- `check_paths_exist` 只读取当前 source 声明的目标路径，用于写入前冲突扫描
- `diagnose` 与 `verify` 读取同一映射信息，退出语义不同
- `install` 只写当前 descriptor 声明的 live payload

最小读取项：source 是否合法（无重复 `target_dir`）、target entry 与 `required_payload_files` 存在且类型正确、payload descriptor 身份字段与当前 binding 一致、live install 与当前 source 对齐。

## 不变量

target entry 与 runtime payload 不是 source of truth；`target_dir` 必须唯一；映射合同只服务 destructive reinstall，不承接 archive/release channel；backend-specific 细节在 adapter 附码说明。
