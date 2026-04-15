---
title: "Deploy Runbook"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Deploy Runbook

> 目的：提供当前仓库的 deploy Quick Start，回答“当前 runtime endpoint 支持什么、target root 在哪里、首次激活怎么做、已有 root 的最小更新路径是什么”。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)

本页只保留 Quick Start 和 target root 总览；维护诊断去 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)，业务生命周期边界去 [skill-lifecycle.md](./skill-lifecycle.md)。

## 一、什么时候看这页

适合在下面场景先读：

- 你第一次给当前 repo-local target root 做激活
- 你第一次做全局 root 激活
- 你要先弄清当前实现了哪些 backend
- 你只想走一遍最小更新路径，再决定是否需要进入 maintenance

## 二、当前实现状态

当前统一入口：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py
```

当前已实现 backend：

- `agents`
  对应 `Codex / OpenAI`

暂不实现：

- `claude`
- `opencode`

当前边界：

- 只支持 `agents` 的 `local` / `global` endpoint 与 `verify`
- 当前 deploy 只管理 target root，不复制 skill 内容
- 未来如果恢复其他 backend，应先重定义 target contract，再扩这页

## 三、Repo-local / Global Target 对照

| backend | repo-local target | global target |
|---|---|---|
| `agents` | `.agents/skills/` | `$CODEX_HOME/skills` 或 `--agents-root` |

当前执行接口只保证 target root 可被激活和复验。
它不在这一步定义 canonical source、skill payload、`.aw_template/` 映射或未来 backend overlay 结构。

## 四、首次激活最小步骤

### 1. 首次本地激活

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

### 2. 首次全局激活

如果 `agents` backend 想走脚本默认解析，先确保当前 shell 已经设置：

```bash
export CODEX_HOME=/your/codex/home
```

默认解析示例：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --create-roots
```

显式传 root 示例：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
```

## 五、已有 root 的最小更新路径

如果你只是确认已有 root 仍可用：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

global 示例：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
```

## 六、下一步去哪页

- 你要处理 root drift、坏链路、root 类型错误：看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- 你要处理 skills / `.aw_template` 的 add / update / rename / remove：看 [skill-lifecycle.md](./skill-lifecycle.md)
- `claude` / `opencode` 当前暂不在 deploy 接口中实现；恢复前先不要把它们写成稳定 operator 流程
