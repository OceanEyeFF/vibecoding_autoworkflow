---
title: "Skill Deployment 维护流"
status: active
updated: 2026-04-15
owner: aw-kernel
last_verified: 2026-04-15
---
# Skill Deployment 维护流

> 目的：为当前仓库的 repo-local / global runtime target root 提供统一的维护与诊断入口，回答“怎么复验、怎么处理 root drift、local/global verify 到底各看什么、故障信号分别表示什么”。

本页属于 [Deploy Runbooks](./README.md) 路径簇。

先建立通用边界，再读本页：

- [根目录分层](../foundations/root-directory-layering.md)
- [Toolchain 分层](../../../toolchain/toolchain-layering.md)

本页只负责 root 维护与诊断；首次激活看 [deploy-runbook.md](./deploy-runbook.md)，业务生命周期边界看 [skill-lifecycle.md](./skill-lifecycle.md)。

## 一、什么时候看这页

适合在下面场景先读：

- 你已经有 target root，想做日常复验
- 你怀疑 root 状态不对
- 你在处理坏链路或 root 类型错误
- 你看到 `wrong-target-root-type`、`missing-target-root` 之类的错误码

## 二、推荐维护循环

默认顺序固定为：

1. `verify`
2. `local` 或 `global` endpoint
3. 再跑一次 `verify`

这个顺序的目的：

- 先看清 root drift 是什么
- 再决定只是重新激活 endpoint，还是要手工修 root
- 最后确认 endpoint 执行后问题是否真的消失

## 三、`verify` 在看什么

### 1. 通用 `verify`

用途：

- 检查 deploy target root 是否存在、是否是目录、是否是坏链路
- 发现缺失 root、错误类型和坏链路

执行入口：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

global target 复验时，优先显式传 `--agents-root`

### 2. local 与 global 的差异

`verify` 在两个 target scope 下都只关注 root 状态：

- `local`
  检查 `.agents/skills/` root 是否存在、是否是目录。
- `global`
  检查全局 target root 是否存在、是否是目录。

这里的 operator-facing 目标形态是固定的：

- `local` 预期是目录 root
- `global` 预期是目录 root

如果手工改过 target root，导致它不是目录，`verify` 会把它报成 `wrong-target-root-type`。

## 四、Repo-local 维护

检查 repo-local target root：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

重新激活 repo-local target root：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
```

## 五、全局安装维护

检查全局 target root：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
```

如果你不想显式传 `--agents-root`，先在 shell 里 `export CODEX_HOME=/your/codex/home`；脚本只会在未传 `--agents-root` 时读取 `CODEX_HOME`，不会替你把空变量补成合法路径。

重新激活全局 target root：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots
```

## 六、故障信号怎么路由

| 信号 | 常见含义 | 优先处理方式 |
|---|---|---|
| `missing-target-root` | target root 还没激活，或已存在 root 被删了 | 首次激活回 [deploy-runbook.md](./deploy-runbook.md)；非首次场景按本页维护循环重建 |
| `wrong-target-root-type` | target root 存在，但不是目录 | 修正 root 后重跑 endpoint |
| `broken-target-root-symlink` | target root 是坏链路 | 删除坏链路后重跑 endpoint |

## 七、额外判断

如果看到：

- `missing-target-root`

先判断这是“还没激活”还是“已激活 root 丢失”。首次激活场景应回到 [deploy-runbook.md](./deploy-runbook.md)；已有 root 意外缺失时，再按本页维护循环处理。
