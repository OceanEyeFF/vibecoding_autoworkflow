---
title: "Memory Side Skill 与 Agent 模型"
status: active
updated: 2026-03-22
owner: aw-kernel
last_verified: 2026-03-22
---
# Memory Side Skill 与 Agent 模型

> 目的：定义 `Memory Side` 中 `Prompt`、`Skill`、`Agent` 的关系，并明确它们在当前仓库中分别落到知识层、业务源码层、部署层和工具层的哪里。

## 一、为什么不能停在 Prompt

当前三个 Prompt 已经能定义行为边界，但还不够成为稳定产物。

原因：

- Prompt 解决“怎么说”，不解决“怎么触发”
- Prompt 解决“语义约束”，不解决“能力封装”
- Prompt 解决“共识规范”，不解决“多后端部署”

因此，`Memory Side` 的可落地形态不能只有 Prompt。

## 二、三层载体

### 1. Prompt

职责：

- 定义跨后端共享的行为语义
- 约束每个能力的输入、输出和边界

### 2. Skill

职责：

- 把单一能力封装成可复用的执行单元
- 指定何时触发、读取哪些文档、输出什么结构

### 3. Agent

职责：

- 决定在什么阶段调用哪个 Skill
- 串联任务前、中、后的上下文维护动作

## 三、当前仓库里的四层落点

### 1. 知识合同层

包括：

- `docs/knowledge/memory-side/` 下的基线、规则、格式、Prompt 和 skill skeleton

### 2. 业务源码层

包括：

- `product/memory-side/skills/` 下的 canonical skill 源码
- `product/memory-side/adapters/agents/` 下的 Codex / OpenAI adapter 源码
- `product/memory-side/adapters/claude/` 下的 Claude adapter 源码

### 3. 部署结果层

包括：

- `.agents/skills/`
- `.claude/skills/`

说明：

- 这里是 repo-local deploy target
- 它们从 `product/` 同步出来
- 它们不是 source of truth

### 4. 工具层

包括：

- `toolchain/scripts/`
- `toolchain/evals/`

说明：

- 工具层负责部署、评测、实验
- 工具层不再保存 canonical skill 源码

边界说明见：

- [Memory Side 层级边界](./layer-boundary.md)

## 四、Memory Side 的最小 Skill 集

当前阶段只建议 3 个 Skill：

- `knowledge-base-skill`
- `context-routing-skill`
- `writeback-cleanup-skill`

对应关系：

| Skill | 对应 Partition | 核心产物 |
|---|---|---|
| `knowledge-base-skill` | `Knowledge Base` | 文档体系判断、主线入口修正、分层归类 |
| `context-routing-skill` | `Context Routing` | `Route Card` |
| `writeback-cleanup-skill` | `Writeback & Cleanup` | `Writeback Card` |

## 五、Memory Side 的最小 Agent 集

当前阶段不建议先展开大而全的 Agent catalog。

只建议先定义 2 个任务级 Agent：

### 1. `task-entry-agent`

职责：

- 在任务开始前整理主线入口
- 按需调用 `knowledge-base-skill`
- 产出当前任务的 `Route Card`

### 2. `task-closeout-agent`

职责：

- 在任务结束后整理回写与清理动作
- 产出当前任务的 `Writeback Card`

## 六、当前仓库中的落点

### 1. Canonical skill 源码

```text
product/
  memory-side/
    skills/
      knowledge-base-skill/
      context-routing-skill/
      writeback-cleanup-skill/
```

当前入口：

- [knowledge-base-skill/SKILL.md](../../../../product/memory-side/skills/knowledge-base-skill/SKILL.md)
- [context-routing-skill/SKILL.md](../../../../product/memory-side/skills/context-routing-skill/SKILL.md)
- [writeback-cleanup-skill/SKILL.md](../../../../product/memory-side/skills/writeback-cleanup-skill/SKILL.md)

### 2. Backend adapter 源码

```text
product/
  memory-side/
    adapters/
      agents/
        skills/
      claude/
        skills/
```

说明：

- adapter 源码也在 `product/`
- 这样本地测试、全局安装、后续市场分发都可以共用一套 source

### 3. Repo-local deploy target

```text
.agents/
  skills/

.claude/
  skills/
```

说明：

- 这些目录只保留部署结果
- 它们通过 `toolchain/scripts/deploy/adapter_deploy.py` 从 `product/` 同步
- 不应再手工维护源码

### 4. Toolchain

```text
toolchain/
  scripts/
  evals/
```

说明：

- `deploy/adapter_deploy.py` 负责本地挂载与全局安装
- `research/memory_side_autoresearch.py` 和 `research/memory_side_autoresearch_score.py` 负责评测和实验闭环

## 七、与不同后端的关系

无论是 `Codex` 还是 `Claude`，都应共享同一套：

- Prompt 规范
- Skill 输入输出约束
- Agent 调用顺序
- canonical skill 源码

后端差异只应体现在：

- adapter frontmatter 或 interface metadata
- 本地挂载路径
- 各 CLI 的安装与调用方式

## 八、当前阶段不做什么

- 不直接为每个后端分别写一整套独立知识文档
- 不把 deploy target 当成 source of truth
- 不把 Skill 做成隐藏规则黑箱
- 不先把 `Codex` / `Claude` 扩成复杂 subagents catalog

## 九、配套文档

- [Memory Side 层级边界](./layer-boundary.md)
- [Knowledge Base Skill 骨架](./skills/knowledge-base-skill.md)
- [Context Routing Skill 骨架](./skills/context-routing-skill.md)
- [Writeback & Cleanup Skill 骨架](./skills/writeback-cleanup-skill.md)
- [Memory Side Repo-local Auto Research Loop](../../analysis/memory-side/memory-side-auto-research-loop.md)
- [Codex Memory Side Repo-local Adapter 部署帮助](../../operations/memory-side/codex-deployment-help.md)
- [Claude Memory Side Repo-local Adapter 适配帮助](../../operations/memory-side/claude-adaptation-help.md)
- [Memory Side Repo-local Adapter 评测基线](../../analysis/memory-side/memory-side-eval-baseline.md)
