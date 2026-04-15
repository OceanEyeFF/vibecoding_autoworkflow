---
title: "Deploy Runbook"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Deploy Runbook

> 目的：提供当前仓库的 deploy Quick Start，回答“支持哪些 backend、target 在哪里、首次安装怎么做、已有安装的最小更新路径是什么”。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)

本页只保留 Quick Start 和 target 总览；生命周期细节与维护诊断分别去：

- [skill-lifecycle.md](./skill-lifecycle.md)
- [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)

## 一、什么时候看这页

适合在下面场景先读：

- 你第一次给某个 backend 做 repo-local 挂载
- 你第一次做全局安装
- 你要先弄清 `agents / claude / opencode` 的 target 对照
- 你只想走一遍最小更新路径，再决定是否需要进入 maintenance

## 二、支持哪些 backend

当前统一入口：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py
```

当前 deploy backend：

- `agents`
  对应 `Codex / OpenAI`
- `claude`
  对应 `Claude`
- `opencode`
  对应 `OpenCode`

当前边界：

- 三个 backend 都支持 `local` / `global` deploy 与 `sync verify`
- `agents` 与 `claude` 还有 backend-specific smoke verify 口径
- `opencode` 当前只确认 deploy sync，不在这里写成稳定 runtime smoke backend

## 三、Repo-local / Global Target 对照

| backend | repo-local target | global target | backend page |
|---|---|---|---|
| `agents` | `.agents/skills/` | `$CODEX_HOME/skills` 或 `--agents-root` | [codex.md](../usage-help/codex.md) |
| `claude` | `.claude/skills/` | `~/.claude/skills` 或 `--claude-root` | [claude.md](../usage-help/claude.md) |
| `opencode` | `.opencode/skills/` | `$XDG_CONFIG_HOME/opencode/skills`、`~/.config/opencode/skills` 或 `--opencode-root` | [opencode.md](../usage-help/opencode.md) |

通用 source root 都在：

- `product/*/adapters/<backend>/skills/`

当前仓库不再保留 `product/memory-side/` 与 `product/task-interface/` 的 adapter source tree。
如果后续恢复可部署 source，应在新的 `product/harness/adapters/<backend>/skills/` 或其他已准入目录下落地，并同步更新本页。

## 五、首次安装最小步骤

### 1. 首次本地挂载

执行对应 backend 的 repo-local deploy：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend opencode
```

然后做最小结构复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend opencode
```

### 2. 首次全局安装

先选定 global target，再执行安装：

如果 `agents` backend 想走脚本默认解析，先确保当前 shell 已经设置：

```bash
export CODEX_HOME=/your/codex/home
```

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
```

安装后显式传 root 做复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```

## 六、已有安装更新最小步骤

如果你只是更新已有 mounts，而不是处理 rename / remove：

1. 先跑一次 `verify`
2. 执行对应的 `local` 或 `global` deploy
3. 再跑一次 `verify`

repo-local 示例：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

global 示例：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
```

如果你改的是 skill 名、删除了 skill，或怀疑 target 里有旧目录，不要停在本页；直接转去 [skill-lifecycle.md](./skill-lifecycle.md) 或 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)。

## 七、下一步去哪页

- 你要做 `add / update / rename / remove`：看 [skill-lifecycle.md](./skill-lifecycle.md)
- 你要处理 drift、坏链路、`--prune`、stale target：看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- 你只想看 backend 特有 global path、smoke verify 或限制：看 [Codex](../usage-help/codex.md)、[Claude](../usage-help/claude.md)、[OpenCode](../usage-help/opencode.md)
