---
title: "Memory Side 总览"
status: superseded
updated: 2026-04-14
owner: aw-kernel
last_verified: 2026-04-14
---
# Memory Side 总览

> 本页已降级为 legacy 副本。canonical 文档已迁到 [../../harness/adjacent-systems/memory-side/overview.md](../../harness/adjacent-systems/memory-side/overview.md)。

> 目的：作为 `Memory Side` 的总文档，统一说明三个 Partition 的角色、关系和共用原则，避免设计继续发散。

## 一、范围

`Memory Side` 只包含 3 个组件：

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

它只负责两件事：

- 维护仓库内的项目长期记忆
- 为单次任务提供可读取、可回写的上下文边界

## 二、层级边界

当前仓库里的 `Memory Side` 资产，在阅读判断上可先分为两类：

- 通用合同层：定义能力模型、输入输出和边界，面向“目标仓库”描述
- 仓库实现层：说明这些合同如何落到本仓库当前的 adapter、runner 和评测资产上

在当前仓库的实际落点上，它进一步展开为“三层主体 + 一层挂载”，边界说明见：

- [Memory Side 层级边界](./layer-boundary.md)

## 三、组件总览

| 组件 | 功能 | 目标 |
|---|---|---|
| `Knowledge Base` | 保存仓库内的长期真相文档，包括总览、模块入口、决策、变更、参考和归档 | 让不同 AI 后端读取同一套项目真相，而不是各自维护记忆 |
| `Context Routing` | 根据任务类型预整理应读的文档入口、代码入口和禁读范围 | 让 AI 在进入任务前拿到足够但受限的阅读范围，避免盲读和上下文爆炸 |
| `Writeback & Cleanup` | 按固定更新规则把已验证结果写回静态文档，并清理失效 Prompt、旧假设和过期入口 | 让项目真相持续刷新，避免一次任务结束后留下脏上下文 |

对应分区文档：

- [Knowledge Base](./knowledge-base.md)
- [Context Routing](./context-routing.md)
- [Writeback & Cleanup](./writeback-cleanup.md)

## 四、共用原则

- 仓库内静态文档是真相本体。
- Agent Prompt 是维护层，不是真相层。
- 后端差异只能影响“怎么读写文档”，不能影响“项目真相是什么”。
- Memory Side 优先做文档与能力合同，不优先做交互模块。

## 五、组件关系

```text
Knowledge Base
    ↓
Context Routing
    ↓
AI 执行端
    ↓
Writeback & Cleanup
    ↓
Knowledge Base
```

含义：

- `Knowledge Base` 提供长期记忆原料
- `Context Routing` 把原料整理成当前任务的阅读入口
- AI 执行端按阅读入口完成任务
- `Writeback & Cleanup` 把结果写回并清理噪声

## 六、对 AI 后端的统一约束

所有后端都遵守同一条原则：

**Prompt 是适配层，不是真相层。**

因此：

- `Claude`、`Codex`、`OpenCode`、`OpenClaw` 都只能读取仓库内同一套静态文档
- 不允许某个后端在自己的 Skill / Agent / Prompt 中私自维护项目主线真相
- 后端差异只应体现在“怎么读取和维护文档”，不应体现在“真相是什么”

## 七、阅读顺序建议

1. 先读本页，建立 `Memory Side` 的总边界。
2. 再读 [Memory Side 层级边界](./layer-boundary.md)，确认“通用合同层”和“仓库实现层”不要混读。
3. 再读 `Knowledge Base`，确认长期真相如何存在仓库里。
4. 再读 `Context Routing`，确认任务开始前怎么整理阅读入口。
5. 最后读 `Writeback & Cleanup`，确认任务结束后怎么回写和清理。

## 八、当前阶段只回答的问题

- 项目长期记忆放在哪里
- 任务开始前上下文怎么裁剪
- 任务结束后哪些信息必须写回

## 九、当前阶段不回答的问题

- 具体用哪家 CLI 做主执行端
- Prompt 如何为每个后端分别优化
- 是否引入 RAG、索引或数据库
- Runtime 状态机如何编码实现

## 十、判断标准

如果下面三句话能成立，说明 `Memory Side` 的基础定义是清楚的：

- 不同 AI 后端读到的是同一套项目真相
- 同一类任务进入执行前会拿到相近的阅读入口
- 任务完成后，项目真相会被统一回写，而不是留在某个对话里

## 十一、Skill、Task Interface 与可选调用层

当前 `Memory Side` 已经有稳定的合同正文，但后续真实落地不能停在 docs 层说明。

建议的载体分层是：

- 合同正文：定义语义规范
- canonical skill：封装单一能力
- `Task Contract`：在讨论和执行之间提供正式任务基线
- Agent / Workflow Shell：由宿主执行层决定如何调用 Skill，不属于当前仓库知识主线

当前仓库中与 `Task Contract` 对应的实际落点包括：

- [Task Contract 基线](../task-interface/task-contract.md)
- [task-contract-skill/SKILL.md](../../../product/task-interface/skills/task-contract-skill/SKILL.md)

如果你要理解通用能力模型，先读：

- [Memory Side Skill 与 Agent 模型](./skill-agent-model.md)
- [根目录分层](../../project-maintenance/foundations/root-directory-layering.md)

如果你要看本仓库当前怎么部署和 repo-local 使用，再读：

- [Usage Help 总入口](../../project-maintenance/usage-help/README.md)
- [Codex Repo-local Usage Help](../../project-maintenance/usage-help/codex.md)
- [Claude Repo-local Usage Help](../../project-maintenance/usage-help/claude.md)
