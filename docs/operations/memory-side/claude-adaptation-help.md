---
title: "Claude Memory Side Repo-local Adapter 适配帮助"
status: active
updated: 2026-03-26
owner: aw-kernel
last_verified: 2026-03-26
---
# Claude Memory Side Repo-local Adapter 适配帮助

> 目的：说明如何把 `product/` 下的 Claude adapter 源码部署到本仓库 `.claude/`，并保持与 Codex 同一套能力边界。本页属于仓库实现层，不是跨仓库通用合同。

先建立通用边界，再读本页：

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Skill Deployment 维护流](../skill-deployment-maintenance.md)

说明：

- 当前部署脚本按 backend 汇总部署 `product/` 下的所有 adapter skill。
- 如果仓库同时存在 `Task Interface` skill，它也会一起挂载到 `.claude/skills/`。
- 本页只约束其中 `Memory Side` 这一组 skill 的边界和检查项。

## 一、当前落点

```text
docs/knowledge/
  memory-side/
    ...

product/memory-side/
  skills/
  adapters/
    claude/
      skills/

.claude/
  skills/

toolchain/scripts/
  deploy/
    adapter_deploy.py
```

职责边界：

- `docs/knowledge/` 是真相层
- `product/memory-side/skills/` 是 canonical skill 源码
- `product/memory-side/adapters/claude/` 是 Claude adapter 源码
- `.claude/skills/` 是 repo-local deploy target

## 二、为什么先做项目级 Skill

当前阶段优先采用项目级 skill，而不是先做复杂 subagents，原因很简单：

- `Memory Side` 目前只需要 3 个稳定能力，不需要大 catalog
- `Skill` 更适合承载固定输入输出和限读边界
- `Claude` 端先把读取顺序和输出格式稳定住，比先扩编排更重要

## 三、本地挂载

默认把 adapter 源码以软链方式挂到本仓库 `.claude/skills/`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
```

做 dry run：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude --dry-run
```

先做 repo-local 检查：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
```

如需清理陈旧 target：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude --prune
```

部署后复验：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify --backend claude
```

## 四、全局安装

默认把 adapter 复制到 `~/.claude/skills/`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global --backend claude --dry-run
```

如果要自动创建根目录：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py global \
  --backend claude \
  --create-roots
```

如需检查全局目标：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py verify \
  --target global \
  --backend claude \
  --claude-root ~/.claude/skills
```

## 五、对齐要求

Claude 侧必须和 Codex 侧保持同一套边界：

- 同样的 3 个 skill
- 同样的 canonical docs
- 同样的固定输出契约
- 同样不允许把规则正文塞进 adapter

允许的差异只有：

- frontmatter 格式
- 文档裁剪和读取节奏
- Claude CLI 的挂载和调用方式

## 六、最小检查项

- `product/memory-side/adapters/claude/skills/*/SKILL.md` 先读 canonical skill，再读 canonical docs
- `.claude/skills/` 由部署脚本生成，而不是手工维护
- skill 内容没有复制 `Memory Side` 规则正文
- Claude 侧默认先走项目级 skill，而不是直接起复杂 subagents
- 三个 skill 的输出契约与 Codex 侧一致

## 七、相关文档

- [Memory Side 层级边界](../../knowledge/memory-side/layer-boundary.md)
- [Memory Side Skill 与 Agent 模型](../../knowledge/memory-side/skill-agent-model.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](./codex-deployment-help.md)
