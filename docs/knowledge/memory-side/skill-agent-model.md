---
title: "Memory Side Skill 与 Agent 模型"
status: active
updated: 2026-03-21
owner: aw-kernel
last_verified: 2026-03-21
---
# Memory Side Skill 与 Agent 模型

> 目的：定义 `Memory Side` 中 `Prompt`、`Skill`、`Agent` 的关系，回答“这些文档规范如何真正变成可挂载到不同 AI CLI 的执行载体”。

## 一、为什么现在不能停在 Prompt

当前三个 Prompt 已经能定义行为边界，但还不够成为稳定产物。

原因：

- Prompt 解决“怎么说”，不解决“怎么触发”
- Prompt 解决“语义约束”，不解决“能力封装”
- Prompt 解决“共识规范”，不解决“多步编排”

因此，`Memory Side` 的可落地形态不能只有 Prompt。

## 二、三层载体

### 1. Prompt

职责：

- 定义跨后端共享的行为语义
- 约束每个能力的输入、输出和边界

特点：

- 后端无关
- 语义稳定
- 不持有项目真相

### 2. Skill

职责：

- 把单一能力封装成可复用的执行单元
- 指定何时触发、读取哪些文档、输出什么结构

特点：

- 能力单一
- 可被多个 Agent 复用
- 是 Prompt 的实际挂载位

### 3. Agent

职责：

- 决定在什么阶段调用哪个 Skill
- 串联任务前、中、后的上下文维护动作

特点：

- 负责编排，不负责编写真相
- 不应为每个后端各自维护一套项目知识

## 三、统一原则

- 仓库内静态文档是真相本体
- Prompt 是语义规范层
- Skill 是能力封装层
- Agent 是调用编排层
- 后端差异只能影响适配方式，不能改变真相和主线规则

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

默认调用顺序：

1. 必要时调用 `knowledge-base-skill`
2. 调用 `context-routing-skill`

### 2. `task-closeout-agent`

职责：

- 在任务结束后整理回写与清理动作
- 产出当前任务的 `Writeback Card`

默认调用顺序：

1. 读取验证结果和变更结果
2. 调用 `writeback-cleanup-skill`

说明：

- `memory-side-agent` 可以作为后续阶段的总控角色
- 当前阶段不必先单独实现

## 六、当前落点

当前 `Memory Side` 已经落成两层静态资产；任务级 `Agent` 仍停留在模型定义层，尚未在仓库里物化：

### 1. Canonical Skill 资产（已存在）

```text
toolchain/
  skills/
    aw-kernel/
      memory-side/
        knowledge-base-skill/
        context-routing-skill/
        writeback-cleanup-skill/
```

当前已存在的 canonical Skill 入口：

- [knowledge-base-skill/SKILL.md](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/knowledge-base-skill/SKILL.md)
- [context-routing-skill/SKILL.md](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/context-routing-skill/SKILL.md)
- [writeback-cleanup-skill/SKILL.md](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/toolchain/skills/aw-kernel/memory-side/writeback-cleanup-skill/SKILL.md)

建议中的最小 `Agent` 形态仍然是：

- `task-entry-agent`
- `task-closeout-agent`

但当前仓库还没有把它们落到 `toolchain/agents/`；这一轮只先把 skill 的 backend adapter 接好。

### 2. Repo-local backend adapter（已存在）

```text
.agents/
  skills/
    knowledge-base-skill/
    context-routing-skill/
    writeback-cleanup-skill/

.claude/
  skills/
    knowledge-base-skill/
    context-routing-skill/
    writeback-cleanup-skill/
```

说明：

- `toolchain/skills/...` 继续保存 canonical skill 定义
- `.agents/skills/...` 是 `Codex` / `OpenAI` 侧的项目级 wrapper
- `.claude/skills/...` 是 `Claude` 侧的项目级 wrapper
- wrapper 只能回指 canonical doc / canonical skill，不能复制项目真相
- `agents/openai.yaml` 只承载 interface metadata，不承载 Memory Side 规则正文
- 任务级 `Agent` catalog 仍未展开，这一轮只补 skill 的 backend adapter

## 七、与不同后端的关系

无论是 `OpenCode`、`OpenClaw`、`Codex` 还是 `Claude`，都应共享同一套：

- Prompt 规范
- Skill 输入输出约束
- Agent 调用顺序

后端差异只应体现在：

- Skill 如何被注册
- Agent 如何被声明
- Prompt 如何被注入

不应体现在：

- 项目真相是什么
- 默认读哪些主线文档
- 回写规则和清理规则是什么

## 八、当前阶段不做什么

- 不直接为每个后端分别写一整套独立 Skill
- 不直接为每个 Partition 都做一个 Agent
- 不让 Agent 私自持有仓库主线真相
- 不把 Skill 做成隐藏规则黑箱
- 不先把 `Codex` / `Claude` 扩成复杂 subagents catalog

## 九、配套文档

- [Knowledge Base Skill 骨架](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skills/knowledge-base-skill.md)
- [Context Routing Skill 骨架](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skills/context-routing-skill.md)
- [Writeback & Cleanup Skill 骨架](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/memory-side/skills/writeback-cleanup-skill.md)
- [Memory Side Auto Research Loop](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/analysis/memory-side-auto-research-loop.md)
- [Codex Memory Side 部署帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/codex-deployment-help.md)
- [Claude Memory Side 适配帮助](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/guides/claude-adaptation-help.md)
- [Memory Side Adapter 评测基线](/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/docs/knowledge/analysis/memory-side-eval-baseline.md)

## 十、判断标准

如果下面几句话成立，说明这个模型是清楚的：

- Prompt、Skill、Agent 三层各自职责明确
- 同一项 Memory Side 能力可以被不同后端复用
- 当前阶段不会过早膨胀成大而全的 Agent catalog
