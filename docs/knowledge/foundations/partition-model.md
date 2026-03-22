---
title: "项目 Partition 模型"
status: active
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# 项目 Partition 模型

> 目标：先定义当前仓库这个 repo-side contract layer 需要持有的主线分区和任务接口对象，再反推目录、模板和后续实现落点。

相关目录投影见：

- [根目录分层](./root-directory-layering.md)

## 一、设计原则

- 先分职责边界，再分目录结构。
- 先定义谁持有真相，再定义谁消费真相。
- 长期记忆、任务入口和任务收尾必须分层。
- `foundations` 只固化当前仓库需要持有的合同层，不提前展开宿主运行时。
- 没有明确 owner 的信息，不应进入主线文档。

## 二、总览

| Partition | 类型 | 核心职责 | 持有的真相 |
|---|---|---|---|
| `Knowledge Base` | Memory Side | 维护项目长期记忆 | 项目总览、模块入口、决策、变更、归档 |
| `Context Routing` | Memory Side | 决定任务开始前应读取哪些上下文 | 入口文档、代码入口、禁读范围 |
| `Task Contract` | Task Interface | 把讨论收束成正式执行基线 | 目标、范围、验收标准、约束、风险 |
| `Writeback & Cleanup` | Memory Side | 回写项目真相并清理失效上下文 | 变更摘要、风险、待办、清场记录 |

## 三、主线分区与接口对象

### Memory Side

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

职责：

- 维护长期真相
- 控制 AI 进入任务时读取什么
- 保证任务结束后真相被刷新

### Task Interface

- `Task Contract`

职责：

- 在讨论和执行之间建立唯一正式基线
- 把目标、范围、验收和限制压成可消费对象
- 约束执行层在进入任务前先拿到同一份边界

## 四、各 Partition 边界

### 1. Knowledge Base

**职责**

- 维护项目长期记忆
- 提供稳定文档入口
- 存放决策记录、变更记录、参考资料和归档

**输入**

- 已验证的项目事实
- 已完成任务的 writeback
- 经确认的设计决策

**输出**

- 项目总览
- 模块入口
- 任务入口
- 决策记录
- 变更日志
- 参考资料与归档资料

**不拥有**

- 单次任务的运行状态
- 执行过程中的临时推理
- 未经验证的猜测

**禁止越界**

- `reference` 文档不能承载当前真相
- `archived` 文档不能作为执行入口
- 临时草稿不能直接覆盖主线入口

### 2. Context Routing

**职责**

- 为不同任务类型指定阅读入口
- 决定先读哪些文档、代码、目录
- 明确哪些内容与当前任务无关

**输入**

- 任务类型
- Task Contract 中的目标和范围
- Knowledge Base 中的入口文档

**输出**

- `context entry`
- 推荐阅读顺序
- 相关代码入口
- 禁读范围和裁剪建议

**不拥有**

- 项目主线知识本体
- 任务验收标准
- 执行结果

**禁止越界**

- 不能替代 `Task Contract`
- 不能把全仓库扫描当默认行为
- 不能把历史文档全部推给执行层

### 3. Task Contract

**职责**

- 把模糊讨论压成唯一正式执行基线
- 定义目标、范围、验收标准和边界
- 记录风险、限制、依赖和验证要求
- 可由 skill、agent 或 repo-local 模板承载

**输入**

- 用户讨论结果
- Context Routing 提供的上下文入口
- 当前项目约束

**输出**

- `task contract`
- 验收标准
- 范围边界
- 验证要求

**不拥有**

- 项目总览
- 实际执行步骤日志
- 宿主运行时的调度状态

**禁止越界**

- 没有 Contract 不得进入执行
- Contract 不能只写目标，不写边界和验收
- Contract 不能把讨论碎片直接原样堆进去

### 4. Writeback & Cleanup

**职责**

- 把已验证结果写回长期记忆
- 更新变更日志、决策记录、待办和风险
- 清理失效 prompt、旧策略和伪事实

**输入**

- 已验证的任务结果
- 交付摘要
- 当前 Knowledge Base 入口

**输出**

- writeback 日志
- 更新后的主线文档
- 待办与风险记录
- 清场记录

**不拥有**

- 需求讨论本体
- 宿主运行时的调度权
- 未验证的结论

**禁止越界**

- 未经验证结果不得回写为项目真相
- 不得保留已失效的 prompt 作为主线规则
- 不得只提交代码而跳过回写

## 五、Partition 之间的关系

- `Knowledge Base -> Context Routing`：提供长期记忆和稳定入口
- `Context Routing -> Task Contract`：提供任务限读范围和入口
- `Task Contract -> 执行层`：提供唯一正式基线
- `已验证结果 -> Writeback & Cleanup`：提供可回写事实
- `Writeback & Cleanup -> Knowledge Base`：刷新长期真相

说明：

- 当前 foundations 只定义主线分区和接口对象
- `Control Plane`、`Execution Runtime`、`Verification` 属于后续宿主运行时或仓库实现层议题，不在本页展开

## 六、建议的最小文档产物

按当前规划，至少需要这些主线文档：

- `project_overview.md`
- `partition-model.md`
- `task-contract-template.md`
- `context-entry-template.md`
- `writeback-log-template.md`
- `decision-record-template.md`
- `module-entry-template.md`

## 七、当前实现顺序建议

### P0

- 先固化 Partition 边界
- 明确每类文档的唯一职责
- 明确哪些信息算长期真相

### P1

- 给 `Knowledge Base`、`Task Contract`、`Context Routing`、`Writeback & Cleanup` 建模板
- 补齐最小入口文档

### P2

- 如后续确实需要宿主运行时编排，再在仓库实现层单独设计：
- 执行阶段状态与 shared state
- 执行运行时与工具调用面
- 验证流程与验收 gate

## 八、当前阶段不做什么

- 不先设计复杂 RAG
- 不先绑定某个单一后端或运行时框架
- 不先展开大而全的 Agent catalog
- 不在 foundations 主线中展开 `Control Plane / Execution Runtime / Verification`
- 不把旧仓库结构直接继承成新架构

## 九、判断标准

当以下条件满足时，说明 Partition 规划成立：

- 能明确说出每类信息该写到哪里
- 能明确说出一个任务开始前该读什么
- 能明确说出没有 `Task Contract` 就不能进入执行
- 能明确说出代码完成后还缺哪些回写动作
- 旧文档和主线文档不会同时声称自己是真相源
