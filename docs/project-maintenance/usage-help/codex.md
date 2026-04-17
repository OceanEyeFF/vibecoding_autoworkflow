---
title: "Codex Usage Help"
status: active
updated: 2026-04-17
owner: aw-kernel
last_verified: 2026-04-17
---
# Codex Usage Help

> 目的：只保留 `agents` backend 的特有差异，回答 “Codex target root 怎么解析、root 参数怎么传、按新三步主流程时有什么 backend 特有注意事项、最小 smoke verify 怎么做”。

先读通用 deploy 文档，再读本页：

- [Deploy Runbook](../deploy/deploy-runbook.md)
- [Skill Deployment 维护流](../deploy/skill-deployment-maintenance.md)
- [Skill 生命周期维护](../deploy/skill-lifecycle.md)

## 一、Backend 标识与 target root

- backend 名：`agents`
- 默认 target root：`.agents/skills/`
- 显式覆盖参数：`--agents-root`

说明：

- 如果没有 `--agents-root`，当前命令默认落到 repo-local `.agents/skills/`
- 如果你要把 target root 指到别处，再显式传 `--agents-root /your/custom/skills`
- deploy 主流程统一写在 [Deploy Runbook](../deploy/deploy-runbook.md)；本页只补 backend-specific 差异

## 二、最小 smoke verify 口径

`agents` 是当前有稳定 smoke verify 口径的 backend 之一。前提是先完成主流程，再跑一次只读 `verify`，然后做最小 skill entry 可读性确认。

推荐顺序：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

建议做法：

- 显式调用当前 target root 下的一个已安装 skill entry
- 选一个你当前在用、且输出结构稳定的 skill 做最小读取确认
- 只确认 “skill entry 能被 Codex 读取，输出结构仍符合对应 skill 的固定契约”

判断标准：

- Codex 能读取对应 skill entry
- 输出仍符合固定结构
- 这一步是 backend runtime 可读性确认，不替代 `adapter_deploy.py verify`

## 三、和其他 backend 的区别

- `agents` 默认使用 repo-local `.agents/skills/`
- 如需改 root，再显式传 `--agents-root`
- `agents` 继续使用和其他 backend 同一套 destructive reinstall 模型，不需要额外的 `agents` 专属 build 步骤
- backend 名仍是 `agents`；本轮不并入 `agents -> codex` 命名迁移

## 四、命令差异

`agents` backend 的主要差异只有 target root 参数：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py prune --all --backend agents --agents-root /your/custom/skills
python3 toolchain/scripts/deploy/adapter_deploy.py check_paths_exist --backend agents --agents-root /your/custom/skills
python3 toolchain/scripts/deploy/adapter_deploy.py install --backend agents --agents-root /your/custom/skills
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents --agents-root /your/custom/skills
```

当前语义：

- 前三条构成主流程
- 最后一条是只读复验
- 如果你就在当前仓库下部署到默认 repo-local target，可以省略 `--agents-root`
