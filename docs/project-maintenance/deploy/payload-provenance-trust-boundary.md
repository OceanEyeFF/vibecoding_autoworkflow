---
title: "aw-installer Payload Provenance And Update Trust Boundary"
status: active
updated: 2026-05-05
owner: aw-kernel
last_verified: 2026-05-05
---
# aw-installer Payload Provenance And Update Trust Boundary

> 目的：固定 `aw-installer` 的 payload 从哪里来、命令写到哪里、哪些 source override 可信、哪些远程更新能力当前已准入。

本页属于 [Deploy Runbooks](./README.md)。

## 本页管理什么

- 允许哪些 source kind
- source root 与 target root 的分离边界
- `update` 当前可以信任哪些远程输入

## 本页不管理什么

- wrapper 命令语义：见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)
- release channel / publish 准入：见 [aw-installer Release Channel Governance](../governance/aw-installer-release-channel-governance.md)
- canonical source 到 target entry 的字段合同：见 [Deploy Mapping Spec](./deploy-mapping-spec.md)

## 当前允许的 payload 来源

当前 `aw-installer` 只允许以下 source kinds：

1. package-local payload
2. checkout-local payload
3. 显式 `--source github` 的 GitHub source archive

不允许：

- registry / dist-tag 自动解析出新的 remote payload
- 任意 HTTP URL
- target root 反向生成 source truth
- 隐式 self-update、自动回滚、增量 patch

`.aw/`、`.agents/`、`.claude/`、`.autoworkflow/` 都不是 package payload。

## Source Root 与 Target Root

解析规则：

- 未设置 `AW_HARNESS_REPO_ROOT` 时，source root 来自 package 解压根或当前 checkout
- 设置 `AW_HARNESS_REPO_ROOT` 时，source root 显式指向该 checkout
- 未设置 `AW_HARNESS_TARGET_REPO_ROOT` 时，target repo root 默认是当前工作目录
- 设置 `AW_HARNESS_TARGET_REPO_ROOT` 时，target repo root 显式指向该目录
- `--agents-root` / `--claude-root` 只覆盖对应 backend 的 target root，不改变 source root

必须保持：

- source root 和 target root 必须分离
- target root 不是 source of truth
- package / `.tgz` smoke 必须证明 package payload 与临时 target repo 分离

## 命令写入边界

| 命令 | 允许读取什么 | 允许写入什么 |
| --- | --- | --- |
| `diagnose` | 当前 source + target 状态 | 不写入 |
| `verify` | 当前 source + target 状态 | 不写入 |
| `check_paths_exist` | 当前 source 声明的目标路径 | 不写入 |
| `install` | 当前 source 声明的 live payload | 只写 resolved target root |
| `update --json` | 当前 source 声明的 live payload | 不写入，只输出 dry-run plan |
| `update --yes` | 当前 source 声明的 live payload | 只执行显式 destructive reinstall |
| `prune --all` | 不读取新 payload | 只删除当前 backend 可识别受管目录 |

`aw.marker` 只证明“这是当前 backend 的受管 live install 目录”，不是 source truth，也不是远程 provenance 证明。

## GitHub Source 准入

`update --source github` 当前只支持显式 GitHub archive source，例如：

```bash
aw-installer update --backend agents --source github --github-repo OWNER/REPO --github-ref REF --json
aw-installer update --backend agents --source github --github-repo OWNER/REPO --github-ref REF --yes
```

准入规则：

- 只支持 `OWNER/REPO + ref`，不支持任意 URL
- archive 必须包含当前 required Harness payload source
- GitHub source root 只在本次命令中生效，不变成长期 source truth
- target root 仍来自当前工作目录、`AW_HARNESS_TARGET_REPO_ROOT` 或 backend root override
- dry-run 必须暴露 `source_kind=github` 与 `source_ref`
- `--yes` 仍然只执行同一条 destructive reinstall 链路
- 如果 selected ref 缺少 required payload source，命令必须失败，不能回退到 package-local source

## 当前不承接的能力

当前 `aw-installer` 不实现：

- channel-based remote update
- registry 或 GitHub Release 自动选包
- signature / verification-based remote provenance chain
- 自动回滚
- target-to-source 反向同步

未来如果要加入上述能力，必须先补独立合同与验证证据，不能直接扩展当前 `update --yes`。

## Operator 不变量

- 远程 source 只能显式进入，不能通过 channel 自动解析
- source provenance 与 deploy target 必须始终分离
- `update --json` 只输出 plan，`update --yes` 只执行既有 destructive reinstall 链路
