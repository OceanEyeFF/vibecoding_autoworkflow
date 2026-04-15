---
title: "Deploy Runbook"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Deploy Runbook

> 目的：提供当前仓库的部署快速上手指南，回答四个核心问题：当前支持哪些运行端点、目标根目录在哪里、首次激活怎么操作、已有根目录的最小更新路径是什么。

本页属于 [Deploy Runbooks](./README.md) 系列文档。

阅读本页前，建议先了解以下背景：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)
- [Deploy Mapping Spec](./deploy-mapping-spec.md) —— 部署映射规范

本页只保留快速入门和目标根目录总览。维护诊断请查看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)，业务生命周期边界请查看 [skill-lifecycle.md](./skill-lifecycle.md)。

## 一、什么时候看这页

以下场景建议先读本文：

- 首次激活当前仓库的本地（repo-local）目标根目录
- 首次激活全局目标根目录
- 想先了解当前实现了哪些后端（backend）
- 只想走一遍最小更新路径，再决定是否进入维护流程

## 二、当前实现状态

统一入口脚本：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py
```

当前已实现的后端：

- `agents` —— 对应 `Codex / OpenAI`

暂不实现：

- `claude`
- `opencode`

当前边界说明：

- 仅支持 `agents` 的 `local` / `global` 端点，以及 `verify`（校验）
- 当前部署脚本只负责管理目标根目录（创建/校验目录结构），不复制 skill 内容
- 原始来源（canonical source）、后端部署包（backend payload source）、清单（manifest）、目标入口（target entry）之间的正式映射规则，见 [Deploy Mapping Spec](./deploy-mapping-spec.md)
- 未来若恢复其他后端，应先重新定义目标端契约（target contract），再扩展本文档

## 三、本地 / 全局目标对照

| backend | 本地目标路径 | 全局目标路径 |
|---|---|---|
| `agents` | `.agents/skills/` | `$CODEX_HOME/skills` 或通过 `--agents-root` 显式指定 |

当前执行接口只保证目标根目录可被激活和复验。原始来源到目标入口的正式映射、部署包文件规则与校验口径，见 [Deploy Mapping Spec](./deploy-mapping-spec.md)。

## 四、首次激活最小步骤

### 1. 首次本地激活

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

### 2. 首次全局激活

如果 `agents` 后端想走脚本默认解析，先确保当前 shell 已设置环境变量：

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

## 五、已有根目录的最小更新路径

如果只是确认已有根目录仍可用：

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

- 根目录不一致（drift）、损坏链路、root 类型错误：查看 [skill-deployment-maintenance.md](./skill-deployment-maintenance.md)
- skills / `.aw_template` 的增删改查：查看 [skill-lifecycle.md](./skill-lifecycle.md)
- 原始来源、后端部署包、清单、目标入口的正式规则：查看 [Deploy Mapping Spec](./deploy-mapping-spec.md)
- `claude` / `opencode` 当前暂不在部署接口中实现；恢复前不要将它们写成稳定的运维操作流程
