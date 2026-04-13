---
title: "OpenCode Repo-local Usage Help"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# OpenCode Repo-local Usage Help

> 目的：只保留 `opencode` backend 的特有差异，回答 “global target 在哪、root 参数怎么传、目前支持到哪一层、和其他 backend 的区别是什么”。

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
- 如果你需要 runtime 可读性结论，当前文档不承诺它

## 三、和其他 backend 的区别

- `opencode` 和 `agents`、`claude` 一样支持 deploy 与 `sync verify`
- `opencode` 没有稳定 smoke verify 口径，这一点和 `agents`、`claude` 不同
- `opencode` 的全局路径按 XDG 规则解析，这一点和 `claude`、`agents` 都不同

## 四、命令差异

全局安装或复验时，`opencode` backend 的差异是使用 XDG 风格 target root：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend opencode --opencode-root ~/.config/opencode/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend opencode --opencode-root ~/.config/opencode/skills
```
