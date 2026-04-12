---
title: "Context Routing 基线"
status: active
updated: 2026-04-13
owner: aw-kernel
last_verified: 2026-04-13
---
# Context Routing 基线

> 目的：定义 `Context Routing` 在 `Memory Side` 中的职责，只回答“任务开始前怎么为 AI 整理阅读入口”。

## 一、组件

`Context Routing`

## 二、功能

- 根据任务类型预整理应读的文档入口
- 指出相关代码入口和优先阅读顺序
- 明确禁读范围和暂不需要读取的历史资料

## 三、目标

- 让 AI 在进入任务前拿到足够但受限的阅读范围
- 避免全仓库盲读和上下文爆炸
- 让不同后端在同类任务下拿到相近的阅读入口

## 四、当前最合适的实现形态

- 文档预整理 Prompt
- `context-routing-skill`
- repo-local 任务入口模板或检查清单

说明：

- 当前阶段更适合先固化 Prompt、Skill 和模板，而不是先定义任务级 Agent
- Prompt 的职责是整理阅读入口，不是定义项目真相

## 五、输入与输出

输入：

- 任务类型
- 优先使用 `Task Contract` 中已定稿的目标和范围；若尚无 Contract，再使用当前目标
- `Knowledge Base` 中可用的入口文档

输出：

- 先读哪些文档
- 再读哪些代码入口
- 暂时不要读哪些资料

## 六、不做什么

- 不替代 `Knowledge Base`
- 不替代 `Task Contract`
- 不默认扫描整个仓库
- 不把所有历史文档都推给执行端

## 七、判断标准

如果下面三句话成立，说明 `Context Routing` 是清楚的：

- AI 知道先读什么
- AI 知道哪些内容先不要读
- 同类任务不会因为后端不同而读取完全不同的主线材料

## 八、配套文档

为了把 `Context Routing` 落成可执行产物，当前配套文档包括：

- [Context Routing 分流规则](./context-routing-rules.md)
- [Context Routing 输出格式](./formats/context-routing-output-format.md)
- [context-routing-skill/SKILL.md](../../../product/memory-side/skills/context-routing-skill/SKILL.md)
