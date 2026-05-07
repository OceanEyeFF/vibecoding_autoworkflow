---
title: "Distribution Entrypoint Contract"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---
# Distribution Entrypoint Contract

> 目的：明确 `aw-installer` 作为 deploy 分发入口必须保持的 wrapper 语义。

本页只管理 `aw-installer` 命令不变量、CLI/TUI 不分叉语义与 backend 暴露口径；release channel、trust boundary、mapping 见相邻文档。

## 当前 package/runtime surface

- bin surface 是 `aw-installer`，当前支持 `agents`、`claude` 与 `bundle`；`bundle` 作为聚合 enum 值，等价于在两个 distribution 上同时执行同一 verb；未支持 backend 或命令变体显式失败
- CLI 是稳定脚本接口；TUI 只能是同一合同上的交互层

## 命令面合同

| mode | 必须保持的语义 |
| --- | --- |
| `diagnose` | 只读状态摘要；可返回 `0` 并报告 issue |
| `verify` | 只读严格复验；发现 issue 时失败 |
| `prune --all` | 只删除当前 backend 可识别的受管目录 |
| `check_paths_exist` | 写入前全量冲突扫描；失败时零业务写入 |
| `install` | 只写当前 source 声明的 live payload |
| `update` | 默认只输出 dry-run plan；`--yes` 才执行 `prune -> check_paths_exist -> install -> verify` |

wrapper 可以改变启动方式，不能改变这些 deploy 语义。

### Aggregate Mode Clauses

当 `--backend bundle` 时，以下追加条款生效：

| mode | aggregate 追加语义 |
| --- | --- |
| `diagnose` | 顺序执行 agents 与 claude 诊断，合并输出；exit 0 |
| `verify` | 顺序执行 agents 与 claude 复验，合并 issue；任一失败则 aggregate exit 1 |
| `prune --all` | 顺序 agents -> claude 删除；前置阶段任一失败即停，不做跨根回滚 |
| `check_paths_exist` | 合并双根冲突扫描；任一根有冲突则 aggregate exit 1 |
| `install` | 写前 all-or-nothing 预扫描（双根 check_paths_exist）；写时 each-independent；agents 成功 claude 失败不回滚 agents |
| `update` | dry-run 分别输出 agents 与 claude plan；`--yes` 顺序 apply，partial-completion 不回滚 |

`--backend bundle --source github` 显式拒绝；`bundle` 仅支持 `--source package`。

## CLI / TUI 不变量

- TUI 不得拥有独立于 CLI 的 install/update 语义；所有 mutating TUI 动作必须映射到明确的 CLI mode
- 非交互环境不得隐式启动 TUI；`--json` 只属 CLI 机器输出，不得混入交互渲染
- `diagnose` 不是安装成功证明；严格失败信号只能来自 `verify`
- wrapper 不得把 deploy target 当成 source of truth
- aggregate 模式下所有 stderr/stdout 输出必须带 `[backend=<name>]` 前缀；TUI 必须保留同前缀，不得为 bundle 引入独立子菜单或独立事务执行流

## 停止线

如果问题已进入 release channel、payload source 设计、target root trust boundary 或 operator 执行步骤，本页只提供链接，不继续展开。
