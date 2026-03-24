---
title: "Codex Memory Side Repo-local Adapter 部署帮助"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# Codex Memory Side Repo-local Adapter 部署帮助

> 目的：说明如何把 `product/` 下的 Codex / OpenAI adapter 源码部署到本仓库 `.agents/`，或安装到全局 `CODEX_HOME`。本页属于仓库实现层，不是跨仓库通用合同。

先建立通用边界，再读本页：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)

说明：

- 当前部署脚本按 backend 汇总部署 `product/` 下的所有 adapter skill。
- 如果仓库同时存在 `Task Interface` skill，它也会一起挂载到 `.agents/skills/`。
- 本页只约束其中 `Memory Side` 这一组 skill 的边界和检查项。

## 一、当前落点

```text
docs/knowledge/
  memory-side/
    ...

product/memory-side/
  skills/
  adapters/
    agents/
      skills/

.agents/
  skills/

toolchain/scripts/
  deploy/
    adapter_deploy.py
```

职责边界：

- `docs/knowledge/` 是真相层
- `product/memory-side/skills/` 是 canonical skill 源码
- `product/memory-side/adapters/agents/` 是 Codex / OpenAI adapter 源码
- `.agents/skills/` 是 repo-local deploy target
- `agents/openai.yaml` 只承载 interface metadata，不承载 `Memory Side` 规则正文

## 二、部署原则

- 不把项目真相搬进 `.agents/skills/`
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

## 五、最小检查项

- `product/memory-side/adapters/agents/skills/*/SKILL.md` 先读 canonical skill，再读 canonical docs
- `product/memory-side/adapters/agents/skills/*/agents/openai.yaml` 只保留显示名、短说明和默认提示
- `.agents/skills/` 由部署脚本生成，而不是手工维护
- skill 输出仍然使用 canonical docs 中定义的固定格式
- adapter 内没有复制 `Memory Side` 规则正文

## 六、相关文档

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
- [Knowledge Base canonical skill](../../../product/memory-side/skills/knowledge-base-skill/SKILL.md)
- [Context Routing canonical skill](../../../product/memory-side/skills/context-routing-skill/SKILL.md)
- [Writeback & Cleanup canonical skill](../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md)
