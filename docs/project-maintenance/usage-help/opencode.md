---
title: "OpenCode Repo-local Usage Help"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# OpenCode Repo-local Usage Help

> 目的：只保留 `opencode` backend 的特有差异，回答 “global target 在哪、目前支持到哪一层、命令差异是什么”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与目标路径

- backend 名：`opencode`
- repo-local target：`.opencode/skills/`
- global target：`$XDG_CONFIG_HOME/opencode/skills` 或 `~/.config/opencode/skills`
- 显式覆盖参数：`--opencode-root`

说明：

- 没有显式传 `--opencode-root` 时，脚本会优先读 `XDG_CONFIG_HOME`
- `verify --target global` 时，优先显式传 `--opencode-root`

## 二、当前支持边界

- 支持 deploy
- 支持 `sync verify`
- 当前不写成稳定 smoke verify backend

因此：

- 这里只确认 target 与 source 同步
- 不把 OpenCode 写成已经具备稳定 `Memory Side` 或 `Task Interface` runtime smoke 口径

## 三、Backend 限制

- 本页不重复通用 local / global deploy 流程
- `.opencode/skills/` 是 repo-local deploy target，不是 source of truth
- 变更仍应先改 `product/`，再通过 deploy 同步到 target

## 四、命令差异

全局安装或复验时，`opencode` backend 的差异是使用 XDG 风格 target root：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```
