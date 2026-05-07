---
title: "Codex Usage Help"
status: active
updated: 2026-05-07
owner: aw-kernel
last_verified: 2026-05-07
---
# Codex Usage Help

> 目的：只保留 `agents` backend 的 target root 解析、参数传递、三步主流程注意事项与 Harness manual run 入口。先读通用 deploy 文档，再读本页。

## 一、快速试用路径

public/stable 主路径仍是 `agents`，推荐默认 `aw-installer` selector：

```bash
AW_INSTALLER_PACKAGE="aw-installer"
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer diagnose --backend agents --json
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer update --backend agents --yes
AW_HARNESS_REPO_ROOT="" AW_HARNESS_TARGET_REPO_ROOT="" npx --yes --package "$AW_INSTALLER_PACKAGE" -- aw-installer verify --backend agents
```

然后在目标仓库用 Codex `set-harness-goal-skill` 初始化 `.aw/`。

## 二、Backend 标识与 target root

backend 名 `agents`，默认 target root `.agents/skills/`，覆盖参数 `--agents-root`（只能指向受控 `.agents/skills` 或临时技能目录，不指向敏感路径）。外部试用优先从目标仓库根目录清空环境变量运行；有工作内容的目标仓库先 `diagnose`/dry-run 再 `update --yes`。

## 三、Deploy verify 与真实 Harness 观察

`agents` 的最小 deploy 验证是 destructive reinstall 主流程加只读 `verify`，证明 payload source、target root 与 live install 对齐，不证明 Harness runtime 行为。

当前 Node-owned package/local 路径：

```bash
aw-installer diagnose --backend agents --json
aw-installer update --backend agents --json
aw-installer update --backend agents --yes
aw-installer verify --backend agents
```

`update --yes` 按 `prune --all -> check_paths_exist -> install -> verify` 执行。`diagnose --json` 和 `update --json` 是只读路径；已有内容的 target 应先看这两步再 `update --yes`。

需观察真实 Harness 行为时使用 [Codex Post-Deploy Behavior Tests](../testing/codex-post-deploy-behavior-tests.md)，在临时 repo 隔离 `.agents/skills/`，用无交互 `codex exec` 调用 `harness-skill`。

判断边界：
- `aw-installer verify --backend agents` 是 package/local deploy target 对齐证明
- `codex-post-deploy-behavior-tests.md` 是 operator-facing 的 Harness runtime 观察入口
- skills mock/contract smoke 不再作为当前主线验证入口

## 四、和其他 backend 的区别

- `agents` 默认使用 repo-local `.agents/skills/`
- 如需改 root 显式传 `--agents-root`
- 使用和其他 backend 同一套 destructive reinstall 模型
- backend 名仍是 `agents`，本轮不并入 `agents -> codex` 命名迁移

## 五、命令差异

主要差异只有 target root 参数：

```bash
aw-installer diagnose --backend agents --json --agents-root "$PWD/.agents/skills"
aw-installer update --backend agents --json --agents-root "$PWD/.agents/skills"
aw-installer update --backend agents --yes --agents-root "$PWD/.agents/skills"
aw-installer verify --backend agents --agents-root "$PWD/.agents/skills"
```

`update --backend agents --yes` 构成 destructive reinstall 主流程；部署到默认 repo-local target 时可省略 `--agents-root`；不要把 `--agents-root` 指向敏感目录。外部试用反馈优先使用 [trial feedback issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-trial-feedback.yml) 或 [bug/blocker issue template](../../../.github/ISSUE_TEMPLATE/aw-installer-bug.yml)。本地 `diagnose`/`update`/`check_paths_exist`/`verify`/`install`/`prune` 已是 Node-owned 路径；selected GitHub-source update 与 selected Claude package/local lifecycle 也由 Node-owned `aw-installer` 路径承接。unsupported variants 在 Node 层失败，不 fallback 到 Python；Python deploy scripts 仅作 repo-local reference/parity/governance tooling。

## 六、Source 变更后的 operator 决策

- source of truth 始终在 `product/`，不改 `.agents/skills/` 已安装结果
- 重新对齐 source 回 [Deploy Runbook](../deploy/deploy-runbook.md) 走三步主流程
- source 出现重复 `target_dir`、改名、移除或 target naming 变化时先修 source contract 再重装
