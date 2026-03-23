---
title: "Claude Task Interface Repo-local Adapter 适配帮助"
status: active
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Claude Task Interface Repo-local Adapter 适配帮助

> 目的：说明如何把 `product/` 下的 `Task Interface` Claude adapter 源码部署到本仓库 `.claude/`，并保持与 Codex 同一套能力边界。本页属于仓库实现层，不是跨仓库通用合同。

先建立通用边界，再读本页：

- [项目 Partition 模型](../../knowledge/foundations/partition-model.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)

说明：

- 当前部署脚本按 backend 汇总部署 `product/` 下的所有 adapter skill。
- 执行 `--backend claude` 时，`Memory Side` 与 `Task Interface` 两组 skill 会一起挂载到 `.claude/skills/`。
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
    claude/
      skills/
        task-contract-skill/

.claude/
  skills/

toolchain/scripts/
  deploy/
    adapter_deploy.py
```

职责边界：

- `docs/knowledge/` 是真相层
- `product/task-interface/skills/` 是 canonical skill 源码
- `product/task-interface/adapters/claude/` 是 Claude adapter 源码
- `.claude/skills/` 是 repo-local deploy target

## 二、为什么先做项目级 Skill

当前阶段优先采用项目级 skill，而不是先做复杂 subagents，原因很简单：

- `Task Interface` 当前只需要 1 个稳定能力，不需要大 catalog
- `Skill` 更适合承载固定结构和字段约束
- Claude 端先把 `Task Contract` 的输入输出稳定住，比先扩编排更重要

## 三、本地挂载

默认把 adapter 源码以软链方式挂到本仓库 `.claude/skills/`：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude
```

做 dry run：

```bash
python3 toolchain/scripts/deploy/adapter_deploy.py local --backend claude --dry-run
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

## 五、对齐要求

Claude 侧必须和 Codex 侧保持同一套边界：

- 同样的 `task-contract-skill`
- 同样的 canonical docs
- 同样的固定输出契约
- 同样不允许把规则正文塞进 adapter

允许的差异只有：

- frontmatter 格式
- 文档裁剪和读取节奏
- Claude CLI 的挂载和调用方式

## 六、最小检查项

- `product/task-interface/adapters/claude/skills/task-contract-skill/SKILL.md` 先读 canonical skill，再读 canonical docs
- `.claude/skills/` 由部署脚本生成，而不是手工维护
- skill 内容没有复制 `Task Contract` 规则正文
- Claude 侧默认先走项目级 skill，而不是直接起复杂 subagents
- 输出结构与 Codex 侧一致

## 七、相关文档

- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [Task Contract Skill 骨架](../../knowledge/task-interface/skills/task-contract-skill.md)
- [Codex Task Interface Repo-local Adapter 部署帮助](./codex-deployment-help.md)
- [Task Interface Repo-local Adapter 评测基线](../../analysis/task-interface/task-interface-eval-baseline.md)
