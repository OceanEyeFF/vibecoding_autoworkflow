---
title: "Knowledge Base 基线"
status: active
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Knowledge Base 基线

> 目的：定义 `Knowledge Base` 在 `Memory Side` 中的职责，只回答“项目长期真相如何在仓库中存在”。

## 一、组件

`Knowledge Base`

## 二、功能

- 保存仓库内的长期真相文档
- 承载项目总览、模块入口、决策记录、变更记录、参考资料和归档资料
- 为其他 Partition 提供稳定的文档入口

## 三、目标

- 让不同 AI 后端读取同一套项目真相
- 让项目真相属于仓库，而不属于某个对话或某个 Prompt
- 让后续的上下文整理和回写有明确落点

## 四、工作模式

### Bootstrap Mode

适用于仓库几乎没有文档体系的时候。

功能：

- 指导 LLM 建立最小文档骨架
- 先补总入口、模块入口、决策位、变更位
- 不追求一次写全所有文档

目标：

- 先让仓库拥有可维护的最小真相层

### Adopt Mode

适用于仓库已经有一定文档体系的时候。

功能：

- 指导 LLM 扫描现有文档
- 识别哪些文档是主线入口，哪些是参考，哪些已过期
- 补索引、补链接、补状态，而不是直接重写

目标：

- 接管并整理现有文档体系，而不是推倒重来

## 五、分层结构

`Knowledge Base` 不是单层知识堆，而是分层文档系统。

### 1. Core Truth

默认可作为执行基线的当前真相层。

典型内容：

- `overview`
- `modules`
- `apis` / `interfaces`
- `decisions`
- `rules`

作用：

- 说明项目当前有效结构和约束
- 为 AI 提供默认可信入口

### 2. Operational Truth

描述当前正在发生什么的运行真相层。

典型内容：

- `tasks/active`
- `tasks/completed`
- `changelog`
- `risks`
- `todo`

作用：

- 说明近期任务状态和变化
- 让 AI 知道当前项目正推进到哪里

### 3. Exploratory Records

保存想法、讨论和思考过程的探索记录层。

典型内容：

- `ideas`
- `discussion`
- `thinking`
- 方案比较
- 草稿分析

作用：

- 保留探索过程
- 提供候选理解和背景

限制：

- 默认不能直接当执行基线
- 需要经过确认后才能上升到 `Core Truth` 或 `Operational Truth`

### 4. Archive

保存历史资料的归档层。

典型内容：

- 旧方案
- 已废弃文档
- 历史设计记录
- 只保留参考价值的旧资料

作用：

- 保留上下文历史
- 避免删除后完全失去脉络

限制：

- 不参与默认主线判断
- 不应作为执行入口

## 六、默认读取级别

| 层级 | 默认读取策略 |
|---|---|
| `Core Truth` | 默认优先读取 |
| `Operational Truth` | 与当前任务强相关时优先读取 |
| `Exploratory Records` | 仅在需要背景、方案比较或历史思路时读取 |
| `Archive` | 默认不读，只有明确需要追溯历史时才读 |

## 七、当前最合适的实现形态

- 仓库内静态文档
- 文档状态字段和最小 frontmatter
- 文档入口和文档之间的稳定链接

建议的最小目录形态：

```text
docs/
  INDEX.md
  PROJECT_OVERVIEW.md
  overview/
  modules/
  apis/
  decisions/
  tasks/
    active/
    completed/
  changelog/
  archive/
```

## 八、不做什么

- 不把 Prompt 当成长期真相
- 不让某个后端维护自己的私有知识体系
- 不在现阶段把 `Knowledge Base` 做成外部数据库或检索系统
- 不把外部参考材料直接当作默认执行基线

## 九、判断标准

如果下面几句话成立，说明 `Knowledge Base` 的分层是清楚的：

- AI 能区分“当前真相”和“探索记录”
- AI 知道哪些文档默认可用作执行基线
- AI 知道哪些文档只可参考，不能直接下判断
- 旧资料不会和主线文档同时声称自己是真相源

## 十、后续演进

当前阶段先做静态文档体系。

后续如果文档规模上来，再考虑：

- `BM25`
- 轻量索引
- 程序化 retrieval 引导

前提是：

- 文档边界已经稳定
- 文档状态已经清晰
- 文档入口已经可导航

## 十一、配套文档

为了把 `Knowledge Base` 继续落成可执行载体，当前配套文档包括：

- [Memory Side Skill 与 Agent 模型](./skill-agent-model.md)
