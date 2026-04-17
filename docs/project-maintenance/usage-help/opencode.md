---
title: "OpenCode Repo-local Usage Help"
status: active
updated: 2026-04-17
owner: aw-kernel
last_verified: 2026-04-17
---
# OpenCode Repo-local Usage Help

> 目的：只保留 `opencode` backend 的 runtime 侧差异，回答 “常见 skill root 在哪、当前支持到哪一层、和其他 backend 的区别是什么”。当前仓库的 `adapter_deploy.py` 不提供 `--backend opencode`。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与常见路径

- backend 名：`opencode`
- 常见 repo-local runtime root：`.opencode/skills/`
- 常见 user config runtime root：`$XDG_CONFIG_HOME/opencode/skills` 或 `~/.config/opencode/skills`

说明：

- 这里描述的是 OpenCode 侧常见 runtime 路径，不是当前仓库 `adapter_deploy.py` 的 CLI 合同
- 当前仓库的 deploy adapter 只实现 `--backend agents`；不要把旧的 `--opencode-root`、`verify --target global` 命令当成现行入口

## 二、当前支持边界

- 当前仓库不提供 `opencode` backend 的 deploy adapter CLI
- 本页只记录 OpenCode 的 runtime 路径约定与验证边界
- 当前不写成稳定 smoke verify backend

因此：

- 不把这里写成“当前仓库已经提供 OpenCode deploy/source 对齐检查”
- 不把 OpenCode 写成已经具备稳定 `Memory Side` 或 `Task Interface` runtime smoke 口径
- 如果你需要 runtime 可读性结论，当前文档不承诺它

## 三、和其他 backend 的区别

- `opencode` 没有稳定 smoke verify 口径，这一点和 `agents`、`claude` 不同
- `opencode` 的常见 user config 路径按 XDG 规则解析，这一点和 `claude`、`agents` 都不同
- 当前仓库不提供 `opencode` backend 的 deploy adapter CLI；如果未来恢复，必须以新的真实命令面更新文档

## 四、当前限制

- 不要在当前仓库使用 `adapter_deploy.py --backend opencode`
- 这页只承接 OpenCode 的 runtime 路径与支持边界，不承接 deploy 命令合同
