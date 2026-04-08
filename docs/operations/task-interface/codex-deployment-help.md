---
title: "Codex Task Interface Repo-local Adapter 部署帮助"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Codex Task Interface Repo-local Adapter 部署帮助

> 目的：说明如何把 `product/` 下的 `Task Interface` Codex / OpenAI adapter 源码部署到本仓库 `.agents/`，或安装到全局 `CODEX_HOME`。本页属于仓库实现层，不是跨仓库通用合同。

本页属于 [Task Interface Usage Help](./README.md) 路径簇。

先建立通用边界，再读本页：

- [项目 Partition 模型](../../knowledge/foundations/partition-model.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Skill Deployment 维护流](../skill-deployment-maintenance.md)

本页默认采用两层验证：

- `sync verify`：通过 `adapter_deploy.py verify` 检查 `.agents/skills/` 的同步状态
- `smoke verify`：在 Codex / OpenAI 侧做最小 skill 可用性确认

说明：

- 当前部署脚本按 backend 汇总部署 `product/` 下的所有 adapter skill。
- 执行 `--backend agents` 时，`Memory Side` 与 `Task Interface` 两组 skill 会一起挂载到 `.agents/skills/`。
- 本页只约束其中 `Task Interface` 这一组 skill 的边界和检查项。

## 一、当前落点

```text
docs/knowledge/
  foundations/
    task-contract-template.md
  task-interface/
    task-contract.md
    skills/
      task-contract-skill.md

product/task-interface/
  skills/
    task-contract-skill/
  adapters/
    agents/
      skills/
        task-contract-skill/

.agents/
  skills/

toolchain/scripts/
  deploy/
    adapter_deploy.py
```

职责边界：

- `docs/knowledge/` 是真相层
- `product/task-interface/skills/` 是 canonical skill 源码
- `product/task-interface/adapters/agents/` 是 Codex / OpenAI adapter 源码
- `.agents/skills/` 是 repo-local deploy target
- `agents/openai.yaml` 只承载 interface metadata，不承载 `Task Contract` 规则正文

## 二、部署原则

- 不把 `Task Contract` 真相搬进 `.agents/skills/`
- 不直接手工维护 `.agents/skills/`
- 不把 `.agents/skills/` 当成第二真相层
- 业务源码始终改在 `product/`

## 三、本地挂载

默认把 adapter 源码以软链方式挂到本仓库 `.agents/skills/`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents
```

做 dry run：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents --dry-run
```

先做 repo-local 检查：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

如需清理陈旧 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend agents --prune
```

部署后复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend agents
```

最小 smoke verify：

- 在 Codex / OpenAI 侧显式调用 repo-local `task-contract-skill`
- 只确认两件事：
  - backend 能读取 `.agents/skills/task-contract-skill`
  - 返回结果仍符合固定 `Task Contract` 结构

## 四、全局安装

默认把 adapter 复制到 `$CODEX_HOME/skills/`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend agents --dry-run
```

如果没有设置 `CODEX_HOME`，可以显式传入目标根：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend agents \
  --agents-root ~/.codex/skills \
  --create-roots
```

如需检查全局目标：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --target global \
  --backend agents \
  --agents-root ~/.codex/skills
```

全局 smoke verify 仍沿同一口径：

- 先做 `sync verify`
- 再在 Codex / OpenAI 侧调用全局安装后的 `task-contract-skill`
- 不把 smoke verify 扩成研究评测

## 五、最小检查项

- `product/task-interface/adapters/agents/skills/task-contract-skill/SKILL.md` 先读 canonical skill，再读 canonical docs
- `product/task-interface/adapters/agents/skills/task-contract-skill/agents/openai.yaml` 只保留显示名、短说明和默认提示
- `.agents/skills/` 由部署脚本生成，而不是手工维护
- skill 输出仍然使用 `Task Contract` 的固定结构
- adapter 内没有复制 `Task Contract` 规则正文

## 六、相关文档

- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Task Contract Skill 骨架](../../knowledge/task-interface/skills/task-contract-skill.md)
- [Task Contract canonical skill](../../../product/task-interface/skills/task-contract-skill/SKILL.md)
