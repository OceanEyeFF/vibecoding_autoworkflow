---
title: "aw-installer Payload Provenance And Update Trust Boundary"
status: active
updated: 2026-04-27
owner: aw-kernel
last_verified: 2026-04-27
---
# aw-installer Payload Provenance And Update Trust Boundary

> 目的：固定 `aw-installer` 在发布前后都必须保持的 payload provenance 与 update trust boundary。本文定义“payload 从哪里来、命令写到哪里、哪些覆盖是可信输入、哪些远程更新能力尚未实现”。

本页属于 [Deploy Runbooks](./README.md) 系列。入口语义见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)，真实 npm 发布准入见 [aw-installer Release Channel Contract](./release-channel-contract.md)。

## 一、当前 provenance 模型

当前根目录 `package.json` 是 `aw-installer` 的 self-contained package envelope。它通过 `files` packlist 明确打包以下 payload 与 wrapper：

- `product/harness/skills`
- `product/harness/adapters/agents/skills`
- `toolchain/scripts/deploy/adapter_deploy.py`
- `toolchain/scripts/deploy/harness_deploy.py`
- `toolchain/scripts/deploy/bin/aw-installer.js`
- `toolchain/scripts/deploy/bin/aw-harness-deploy.js`
- `toolchain/scripts/deploy/bin/check-root-publish.js`
- `toolchain/scripts/deploy/README.md`

这些文件是当前 `.tgz` 内可执行 deploy payload 的来源。`.aw/`、`.agents/`、`.claude/`、`.opencode/`、`.autoworkflow/` 和其他 repo-local runtime state 不属于 package payload。

`product/harness/adapters/agents/skills/` 中的 payload descriptor 是 `agents` backend 的 deploy source。`install --backend agents` 只复制 descriptor 声明的 canonical skill 内容，不从 target root 反向生成 source truth。

## 二、source root 与 target root

`aw-installer` Node bin 只负责调用同包内的 Python wrapper。实际 source / target 解析由 `adapter_deploy.py` 承接：

- 未设置 `AW_HARNESS_REPO_ROOT` 时，source root 是 package 解压根或当前 checkout 中的 repo root。
- 设置 `AW_HARNESS_REPO_ROOT` 时，source root 显式指向该 checkout，并保持旧的 repo-local 行为。
- 未设置 `AW_HARNESS_TARGET_REPO_ROOT` 且未设置 `AW_HARNESS_REPO_ROOT` 时，target repo root 是命令运行时的当前工作目录。
- 设置 `AW_HARNESS_TARGET_REPO_ROOT` 时，target repo root 显式指向该目录。
- `--agents-root` 只覆盖当前命令的 `agents` target root，不改变 source root。

因此，pre-release `.tgz` 试用路径的可信边界是：payload 来自 `.tgz`，写入目标是 operator 当前所在项目的 `.agents/skills`。这也是 root `.tgz` smoke 必须清空 `AW_HARNESS_REPO_ROOT` 并在临时 target repo 中执行的原因。

## 三、命令信任边界

| 命令 | Payload 来源 | Target 行为 | Trust boundary |
|---|---|---|---|
| `diagnose --backend agents --json` | 读取当前 source 与 target 状态 | 只读 | 可返回 0 并报告 issue；用于观察，不是安装成功证明 |
| `verify --backend agents` | 读取当前 source 与 target 状态 | 只读 | 严格复验；发现 source、target、payload、marker、drift 或 conflict 问题时失败 |
| `install --backend agents` | 复制当前 source 声明的 live payload | 写入 resolved target root | 必须先通过 source contract 与 target conflict 检查；不做远程 fetch |
| `update --backend agents` | 读取当前 source 声明的 live payload | 只输出 dry-run plan | 不写入；暴露将删除、将写入和 blocking issue 摘要 |
| `update --backend agents --yes` | 复制当前 source 声明的 live payload | 显式 destructive reinstall | 只包装 `prune --all -> check_paths_exist -> install -> verify`；不做远程 fetch、增量更新或自动回滚 |
| `prune --all --backend agents` | 不读取新 payload | 删除当前 backend 可识别受管目录 | 只删除带可识别 `aw.marker` 且属于当前 backend 的目录 |
| `check_paths_exist --backend agents` | 读取当前 source 声明的目标路径 | 只读冲突扫描 | 失败时不得写业务文件 |

`aw.marker` 是 target runtime marker，只证明目录是当前 backend 的受管 live install。它不是 source truth、不是历史版本记录，也不是可信远程 provenance 证明。

## 四、当前禁止项

当前 `aw-installer` 不实现以下能力：

- 从 registry、GitHub release、HTTP endpoint 或任意远程地址动态获取 deploy payload。
- 根据 dist-tag、release channel 或 latest 指针自动选择新 payload。
- 在 `update --yes` 内执行远程检查、下载、验签、升级自身 package 或替换 source root。
- 维护 archive/history、旧版本保活、增量 patch、自动回滚或 target-to-source 反向同步。
- 将 `.agents/`、`.claude/`、`.opencode/` 或 `.aw/` runtime state 当作 package payload 或 canonical source。

真实 npm 发布只改变 operator 获取 package 的方式，不改变本文定义的 payload/source/target 边界。

## 五、未来远程更新准入条件

任何未来 remote/channel-based update worktrack 必须先补齐以下合同与证据，不能直接扩展当前 `update --yes`：

- 明确 remote manifest schema、payload digest、签名或等价完整性验证机制。
- 明确 release channel 到 payload artifact 的解析规则，并与 release-channel contract 对齐。
- 明确失败恢复策略，包括下载失败、验签失败、写入失败、verify 失败和部分写入后的 operator 恢复路径。
- 明确 dry-run 输出中必须展示 remote artifact identity、digest、channel、source root、target root、将删除路径和将写入路径。
- 补充 package/tarball smoke、deploy regression、PR-baseline CodeReview 和 closeout gate 证据。

在这些条件满足前，`update` 只能表示“用当前可信 source payload 重装当前 target root”。

## 六、验证要求

涉及本文边界的后续改动至少应验证：

- `npm pack --dry-run --json` 的 root packlist仍只包含显式 package payload。
- 根 `.tgz` smoke 不设置 `AW_HARNESS_REPO_ROOT`，并证明 package 内 source payload 与临时 target repo 分离。
- `diagnose`、`verify` 仍是只读命令。
- `update --backend agents` 默认只输出 dry-run plan。
- `update --backend agents --yes` 仍执行 destructive reinstall，并在写入后运行严格 `verify`。
- 文档同步 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)、[Deploy Runbook](./deploy-runbook.md) 和本页。
