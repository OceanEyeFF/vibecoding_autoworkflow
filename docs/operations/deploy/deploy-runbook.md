---
title: "Deploy Runbook"
status: active
updated: 2026-04-11
owner: aw-kernel
last_verified: 2026-04-11
---
# Deploy Runbook

> 目的：给当前仓库提供一份统一的部署总览，说明 `Codex`、`Claude`、`OpenCode` 三个 backend 的 deploy target、入口命令和下钻阅读路径。

本页属于 [Deploy / Verify / Maintenance](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../../knowledge/foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [Skill Deployment 维护流](./skill-deployment-maintenance.md)

本页是 repo-local runbook，总结“怎么部署、部署到哪里、接着该读哪页”，不是 canonical truth。

## 一、什么时候看这页

适合在下面几种场景先读：

- 你需要判断当前仓库支持哪些 deploy backend
- 你需要快速找到某个 backend 的 local/global deploy 命令
- 你需要知道部署后应该继续看哪份细化 runbook

不适合把这页当成：

- backend-specific 详细维护手册
- canonical skill 规则正文
- research runner 使用说明

## 二、当前 deploy backend

本仓库当前统一通过：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py
```

部署 backend 有三个：

- `agents`
  对应 `Codex / OpenAI` 侧 adapter
- `claude`
  对应 `Claude` 侧 adapter
- `opencode`
  对应 `OpenCode` 侧 adapter

当前支持边界：

- 这三者都支持 deploy target 生成与 sync verify
- `OpenCode` 当前只在部署层成立
- `OpenCode` 不应在本仓库文档里被描述成 active research / eval backend

## 三、Deploy Target 对照

### 1. Repo-local target

| backend | repo-local target | source root |
|---|---|---|
| `agents` | `.agents/skills/` | `product/*/adapters/agents/skills/` |
| `claude` | `.claude/skills/` | `product/*/adapters/claude/skills/` |
| `opencode` | `.opencode/skills/` | `product/*/adapters/opencode/skills/` |

### 2. Global target

| backend | global target |
|---|---|
| `agents` | `$CODEX_HOME/skills` 或 `--agents-root` |
| `claude` | `~/.claude/skills` 或 `--claude-root` |
| `opencode` | `$XDG_CONFIG_HOME/opencode/skills`、`~/.config/opencode/skills` 或 `--opencode-root` |

## 四、最小入口命令

### 1. Repo-local deploy

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode
```

### 2. Global deploy

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root ~/.codex/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
```

### 3. 进入维护流

如果你不是只想“重新部署一次”，而是要检查 drift、清理 stale target、做复验，下一步看：

- [Skill Deployment 维护流](./skill-deployment-maintenance.md)

## 五、怎么继续下钻

### 1. 你关心 `Memory Side`

读对应 backend 页面：

- [Codex Memory Side Repo-local Adapter 部署帮助](../memory-side/codex-deployment-help.md)
- [Claude Memory Side Repo-local Adapter 适配帮助](../memory-side/claude-adaptation-help.md)
- [OpenCode Memory Side Repo-local Adapter 部署帮助](../memory-side/opencode-deployment-help.md)

### 2. 你关心 `Task Interface`

读对应 backend 页面：

- [Codex Task Interface Repo-local Adapter 部署帮助](../task-interface/codex-deployment-help.md)
- [Claude Task Interface Repo-local Adapter 适配帮助](../task-interface/claude-adaptation-help.md)
- [OpenCode Task Interface Repo-local Adapter 部署帮助](../task-interface/opencode-deployment-help.md)

## 六、判断标准

如果下面几句话成立，说明你已经用对了这页：

- 你知道当前 deploy backend 有哪些
- 你知道每个 backend 的 target 落在哪里
- 你知道下一步该去 maintenance flow 还是具体 backend 页
