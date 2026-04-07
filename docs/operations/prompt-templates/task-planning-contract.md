---
title: "Task Planning Contract Prompt"
status: active
updated: 2026-04-07
owner: aw-kernel
last_verified: 2026-04-07
---
# Task Planning Contract Prompt

> 目的：把需求文档或问题列表转成可直接驱动执行的 Task Unit 合同集合。

## Prompt 模板

```text
我们需要基于该文档，制定一份“可执行的任务规划文档”，用于后续直接驱动多 Agent 执行。

【总体目标】
- 将文档中的问题或需求拆分为多个“可独立执行的任务单元”
- 每个任务必须具备明确边界、依赖关系、执行建议和完成标准
- 输出结果必须可以直接对接执行型 Prompt

【任务拆分原则】
- 优先拆分为最小可独立验证单元
- 避免跨模块模糊任务
- 将高风险或高复杂度任务单独拆出
- 区分代码任务与文档任务
- 明确哪些任务可以并行，哪些必须串行

【每个任务必须使用以下结构】

任务ID：T-{编号}
任务名称：{一句话总结目标}
任务类型：Explore / Implement / Refactor / Debug / Review / Document

1. 任务目标（Goal）
2. 非目标（Non-goals）
3. 任务边界（In-scope / Out-of-scope）
4. 输入上下文（必读 / 可选 / 不需要读取）
5. 执行策略（Execution Strategy）
6. 模型与推理建议（Execution Profile）
7. 依赖关系（Dependencies）
8. 风险与不确定性（Risks）
9. 验证计划（Validation Plan）
10. 完成标准（Exit Criteria）
11. 失败协议（Failure Handling）

【额外要求】
在所有任务之后，输出：
1. 任务依赖图
2. 推荐执行顺序（Batch 划分）
3. 可并行执行的任务组
4. 高风险任务列表
5. 推荐整体执行策略

【输出要求】
输出为结构化任务规划文档，确保：
- 每个任务可以独立交付给执行 Agent
- 不依赖隐含上下文
- 不存在模糊边界
```

## 相关文档

- [docs/knowledge/README.md](../../knowledge/README.md)
- [Execution Contract 模板](./execution-contract-template.md)
- [Task Contract 模板](../../knowledge/foundations/task-contract-template.md)
- [Task Contract 基线](../../knowledge/task-interface/task-contract.md)
- [task-contract-skill](../../../product/task-interface/skills/task-contract-skill/SKILL.md)
