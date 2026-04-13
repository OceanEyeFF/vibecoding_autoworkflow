---
title: "Deploy Runbook"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Deploy Runbook

> 目的：提供当前仓库的 deploy Quick Start，回答“支持哪些 backend、target 在哪里、首次安装怎么做、已有安装怎么更新”。

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
- 你只想快速更新已有 mounts，不想先读维护诊断
- 你需要先知道 backend / target 对照，再决定下一步去哪页

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

- 三个 backend 都支持 deploy 与 `sync verify`
- `agents` 与 `claude` 还有 backend-specific smoke verify
- `opencode` 当前只确认 deploy sync，不在这里写成稳定 runtime smoke backend

## 三、Repo-local / Global Target 对照

| backend | repo-local target | global target | source root |
|---|---|---|---|
| `agents` | `.agents/skills/` | `$CODEX_HOME/skills` 或 `--agents-root` | `product/*/adapters/agents/skills/` |
| `claude` | `.claude/skills/` | `~/.claude/skills` 或 `--claude-root` | `product/*/adapters/claude/skills/` |
| `opencode` | `.opencode/skills/` | `$XDG_CONFIG_HOME/opencode/skills`、`~/.config/opencode/skills` 或 `--opencode-root` | `product/*/adapters/opencode/skills/` |

## 四、首次安装最小步骤

### 0. 首次初始化 harness runtime

如果你要跑 `Harness Operations` 相关 workflow，先把 repo-local harness runtime 初始化出来：

```bash
python3 toolchain/scripts/deploy/init_harness_project.py
```

需要把 harness 配置写到自定义路径时，可显式传：

```bash
python3 toolchain/scripts/deploy/init_harness_project.py --harness-file custom-runtime/harness/config.yaml
```

### 0.5 需要时预构建 harness adapter source

`harness-operations` 现在由 canonical `prompt.md`、shared `harness-standard.md` 和 backend `header.yaml` 组装成最终 `SKILL.md`。

如果你要先检查组装产物、在不部署的情况下刷新 build cache，或准备运行只读 `verify`，可以先显式执行：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend claude
python3 toolchain/scripts/deploy/adapter_deploy.py build --backend opencode
```

说明：

- `local` / `global` 在部署 `harness-operations` 时也会自动组装当前 backend 的产物
- `verify` 保持只读，不会自动触发 build
- 如果 `verify` 报 `missing-build-source`，先跑一次 `build` 或重新执行对应 deploy

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

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root ~/.codex/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --claude-root ~/.claude/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
```

安装后显式传 root 做复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root ~/.codex/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend claude --claude-root ~/.claude/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```

## 五、已有安装更新最小步骤

如果你只是更新已有 mounts，而不是处理 rename / remove：

1. 先跑一次 `verify`
2. 如需只读复验 harness build output，先跑一次 `build`
3. 执行对应的 `local` 或 `global` deploy
4. 再跑一次 `verify`

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

## 六、下一步去哪页

- 你要做 `add / update / rename / remove`：看 [skill-lifecycle.md](./skill-lifecycle.md)
- 你要处理 drift、坏链路、`--prune`、stale target：看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- 你只想看 backend 特有 global path、smoke verify 或限制：看 [Codex](../usage-help/codex.md)、[Claude](../usage-help/claude.md)、[OpenCode](../usage-help/opencode.md)
