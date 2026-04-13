---
title: "Codex Repo-local Usage Help"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Codex Repo-local Usage Help

> 目的：只保留 `agents` backend 的特有差异，回答 “global target 在哪、root 参数怎么传、最小 smoke verify 怎么做、和其他 backend 的区别是什么”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与目标路径

- backend 名：`agents`
- repo-local target：`.agents/skills/`
- global target：`$CODEX_HOME/skills`
- 显式覆盖参数：`--agents-root`

说明：

- 如果没有 `--agents-root`，全局安装依赖 `CODEX_HOME`
- `verify --target global` 时，优先显式传 `--agents-root`
- 如果你要依赖脚本默认解析，先 `export CODEX_HOME=/your/codex/home`；不要把未设置的 `"$CODEX_HOME/skills"` 直接当命令参数传进去

## 二、最小 smoke verify 口径

`agents` 是当前有稳定 smoke verify 口径的 backend 之一。前提是先让 `sync verify` 通过，再做最小 skill entry 可读性确认。

建议做法：

- 显式调用 `.agents/skills/` 下的一个 repo-local skill entry
- 选一个你当前在用、且输出结构稳定的 skill 做最小读取确认
- 只确认 “skill entry 能被 Codex 读取，输出结构仍符合对应 skill 的固定契约”

判断标准：

- Codex 能读取对应 skill entry
- 输出仍符合固定结构
- 这一步是 backend runtime 可读性确认，不替代 `adapter_deploy.py verify`

## 三、和其他 backend 的区别

- `agents` 和 `claude` 都有稳定 smoke verify 口径
- `agents` 的全局目标路径取决于 `CODEX_HOME`，这一点和 `claude`、`opencode` 不同
- harness 的 build/deploy/verify 模型与其他 backend 相同，不需要额外的 `agents` 专属 build 步骤

## 四、命令差异

全局安装或复验时，`agents` backend 的差异只有 target root 参数：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --agents-root /your/codex/home/skills --create-roots
python3 toolchain/scripts/deploy/adapter_deploy.py verify --target global --backend agents --agents-root /your/codex/home/skills
```
