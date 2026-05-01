---
title: "aw-installer Payload Provenance And Update Trust Boundary"
status: active
updated: 2026-05-01
owner: aw-kernel
last_verified: 2026-05-01
---
# aw-installer Payload Provenance And Update Trust Boundary

> 目的：固定 `aw-installer` 在发布前后都必须保持的 payload provenance 与 update trust boundary。本文定义“payload 从哪里来、命令写到哪里、哪些覆盖是可信输入、哪些远程更新能力已经准入、哪些远程能力仍未实现”。

本页属于 [Deploy Runbooks](./README.md) 系列。入口语义见 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)，真实 npm 发布准入见 [aw-installer Release Channel Contract](./release-channel-contract.md)。

## 一、当前 provenance 模型

当前根目录 `package.json` 是 `aw-installer` 的 self-contained package envelope。它通过 `files` packlist 明确打包以下 payload 与 wrapper：

- `product/harness/skills`
- `product/harness/adapters/agents/skills`
- `product/harness/adapters/claude/skills`
- `toolchain/scripts/deploy/adapter_deploy.py`
- `toolchain/scripts/deploy/harness_deploy.py`
- `toolchain/scripts/deploy/bin/aw-installer.js`
- `toolchain/scripts/deploy/bin/aw-harness-deploy.js`
- `toolchain/scripts/deploy/bin/check-root-publish.js`
- `toolchain/scripts/deploy/README.md`

这些文件是当前 `.tgz` 内可执行 deploy payload 的来源。`.aw/`、`.agents/`、`.claude/`、`.autoworkflow/` 和其他 repo-local runtime state 不属于 package payload。

`product/harness/adapters/agents/skills/` 中的 payload descriptor 是 `agents` backend 的 deploy source。`install --backend agents` 只复制 descriptor 声明的 canonical skill 内容，不从 target root 反向生成 source truth。

`product/harness/adapters/claude/skills/` 中的 payload descriptor 是 `claude` backend 的 deploy source。当前准入完整 Harness skill set，写入 `<target_repo>/.claude/skills/<skill_id>/`，并把旧 `aw-<skill_id>` 目录作为 legacy managed target 处理。

## 二、source root 与 target root

`aw-installer` Node bin 当前直接承接 `--help`、`--version` 与 `diagnose --backend agents --json` 的只读路径；TUI 的 agents diagnose 展示也复用该 Node-owned JSON 路径。`update --backend agents --json` 在 package/local source dry-run 场景下也由 Node-owned 路径生成 plan JSON。该 dry-run JSON 必须继续暴露 `backend`、`source_kind`、`source_ref`、`source_root`、`target_root`、`operation_sequence`、`managed_installs_to_delete`、`planned_target_paths`、`issues` 与 `blocking_issues` 等字段。其他 deploy modes、不受支持的 diagnose / update 变体、`update --yes`、GitHub source update、Claude backend、`install`、`verify` 与 `prune` 仍调用同包内的 Python wrapper/reference path；fallback 环境只透传 deploy 所需变量，不全量继承 shell secrets。实际 source / target 解析必须保持与 `adapter_deploy.py` 的合同一致：

- 未设置 `AW_HARNESS_REPO_ROOT` 时，source root 是 package 解压根或当前 checkout 中的 repo root。
- 设置 `AW_HARNESS_REPO_ROOT` 时，source root 显式指向该 checkout，并保持旧的 repo-local 行为。
- 未设置 `AW_HARNESS_TARGET_REPO_ROOT` 且未设置 `AW_HARNESS_REPO_ROOT` 时，target repo root 是命令运行时的当前工作目录。
- 设置 `AW_HARNESS_TARGET_REPO_ROOT` 时，target repo root 显式指向该目录。
- `--agents-root` 只覆盖当前命令的 `agents` target root，不改变 source root。
- `--claude-root` 只覆盖当前命令的 `claude` target root，不改变 source root。
- `update --source github --github-repo OWNER/REPO --github-ref REF` 会把 GitHub source archive 解压到一次性临时目录，并只在本次 `update` 中把它作为 source root；target repo root 仍按 `AW_HARNESS_TARGET_REPO_ROOT` 或当前工作目录解析。未显式传 `--github-repo` 时，默认仓库依次来自 `AW_INSTALLER_GITHUB_REPO`、`GITHUB_REPOSITORY`，最后才回退到上游 `OceanEyeFF/vibecoding_autoworkflow`。

目标根安全策略只允许当前工作目录、显式 source root 与用户 home 下的 target repo root。共享临时目录 `/tmp` 与 `/var/tmp` 不再作为独立允许前缀；临时 smoke 仍应先进入隔离 target repo，再从该目录运行 installer。

因此，pre-release `.tgz` 试用路径的可信边界是：payload 来自 `.tgz`，写入目标是 operator 当前所在项目的 `.agents/skills`。这也是 root `.tgz` smoke 必须清空 `AW_HARNESS_REPO_ROOT` 并在临时 target repo 中执行的原因。

## 三、命令信任边界

| 命令 | Payload 来源 | Target 行为 | Trust boundary |
|---|---|---|---|
| `diagnose --backend <backend> --json` | 读取当前 source 与 target 状态 | 只读 | 可返回 0 并报告 issue；用于观察，不是安装成功证明 |
| `verify --backend <backend>` | 读取当前 source 与 target 状态 | 只读 | 严格复验；发现 source、target、payload、marker、drift 或 conflict 问题时失败 |
| `install --backend <backend>` | 复制当前 source 声明的 live payload | 写入 resolved target root | 必须先通过 source contract 与 target conflict 检查；不做远程 fetch |
| `update --backend <backend>` | 读取当前 source 声明的 live payload | 只输出 dry-run plan | 不写入；暴露将删除、将写入和 blocking issue 摘要 |
| `update --backend <backend> --yes` | 复制当前 source 声明的 live payload | 显式 destructive reinstall | 只包装 `prune --all -> check_paths_exist -> install -> verify`；不做远程 fetch、增量更新或自动回滚 |
| `update --backend agents --source github --github-repo OWNER/REPO --github-ref REF` | 下载并验证 GitHub source archive 后读取其中的 live payload | dry-run 或显式 destructive reinstall | 只允许 GitHub archive 成为本次 source root；仍执行同一 update plan、target checks 和 post-apply verify |
| `prune --all --backend <backend>` | 不读取新 payload | 删除当前 backend 可识别受管目录 | 只删除带可识别 `aw.marker` 且属于当前 backend 的目录 |
| `check_paths_exist --backend <backend>` | 读取当前 source 声明的目标路径 | 只读冲突扫描 | 失败时不得写业务文件 |

`aw.marker` 是 target runtime marker，只证明目录是当前 backend 的受管 live install。它不是 source truth、不是历史版本记录，也不是可信远程 provenance 证明。

## 四、当前禁止项

当前 `aw-installer` 不实现以下能力：

- 从 registry、GitHub release、任意 HTTP endpoint 或非 GitHub source archive 动态获取 deploy payload。
- 根据 dist-tag、release channel 或 latest 指针自动选择新 payload。
- 在 `update --yes` 内执行远程检查、下载、验签、升级自身 package 或替换 source root。
- 维护 archive/history、旧版本保活、增量 patch、自动回滚或 target-to-source 反向同步。
- 将 `.agents/`、`.claude/` 或 `.aw/` runtime state 当作 package payload 或 canonical source。

真实 npm 发布只改变 operator 获取 package 的方式，不改变本文定义的 payload/source/target 边界。

## 五、GitHub source archive 准入

`0.4.0-rc.3` 开始，`update` 可以显式选择 GitHub source archive：

```bash
aw-installer update --backend agents --source github --github-repo OceanEyeFF/vibecoding_autoworkflow --github-ref <ref-containing-current-payload> --json
aw-installer update --backend agents --source github --github-repo OceanEyeFF/vibecoding_autoworkflow --github-ref <ref-containing-current-payload> --yes
```

准入边界：

- `--source github` 只支持 `OWNER/REPO` + branch/ref archive，不支持任意 URL；fork 或重命名仓库应显式传 `--github-repo`，或设置 `AW_INSTALLER_GITHUB_REPO` / `GITHUB_REPOSITORY`。
- 下载后的 archive 必须通过 Harness payload source validation：至少包含 `product/harness/skills`、`product/harness/adapters/agents/skills` 与 `product/harness/adapters/claude/skills`。
- GitHub source root 是一次性临时目录；命令结束后不得作为长期 source truth 保留。
- target root 不得默认为 GitHub source root；默认仍是当前工作目录，或显式 `AW_HARNESS_TARGET_REPO_ROOT` / `--agents-root`。
- `update --json` 必须暴露 `source_kind=github` 和 `source_ref=OWNER/REPO@REF`。
- GitHub source 不改变 destructive reinstall 顺序、target conflict policy、marker policy 或 post-apply strict verify。
- 所选 GitHub ref 必须真实包含当前 Harness payload source；`master`/default branch 只有在已经包含这些 required source paths 时才是有效 ref。如果 GitHub archive 缺少 required source paths，update 必须失败，而不是回退到 package-local source。

## 六、未来远程更新准入条件

任何未来 channel-based update worktrack 必须先补齐以下合同与证据，不能直接扩展当前 `update --yes`：

- 明确 remote manifest schema、payload digest、签名或等价完整性验证机制。
- 明确 release channel 到 payload artifact 的解析规则，并与 release-channel contract 对齐。
- 明确失败恢复策略，包括下载失败、验签失败、写入失败、verify 失败和部分写入后的 operator 恢复路径。
- 明确 dry-run 输出中必须展示 remote artifact identity、digest、channel、source root、target root、将删除路径和将写入路径。
- 补充 package/tarball smoke、deploy regression、PR-baseline CodeReview 和 closeout gate 证据。

在这些条件满足前，`update` 只能表示“用 package-local source 或显式 GitHub source archive 重装当前 target root”。

## 七、验证要求

涉及本文边界的后续改动至少应验证：

- `npm pack --dry-run --json` 的 root packlist仍只包含显式 package payload。
- 根 `.tgz` smoke 不设置 `AW_HARNESS_REPO_ROOT`，并证明 package 内 source payload 与临时 target repo 分离。
- `diagnose`、`verify` 仍是只读命令。
- `update --backend agents --json` 在 package/local source dry-run 场景下由 Node-owned 路径输出 plan，并保留既有 JSON 字段。
- `update --backend agents --yes` 仍执行 destructive reinstall，并在写入后运行严格 `verify`。
- `update --backend agents --source github --github-ref <ref-containing-current-payload> --json` 在 GitHub source 有效时输出 `source_kind=github`，在 GitHub source 缺少 payload source paths 时失败。
- 文档同步 [Distribution Entrypoint Contract](./distribution-entrypoint-contract.md)、[Deploy Runbook](./deploy-runbook.md) 和本页。
