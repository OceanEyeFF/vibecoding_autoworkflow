---
title: "Task Contract 模板"
status: active
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Task Contract 模板

> 目的：为当前仓库提供一份可复用的 `Task Contract` 正式模板，把讨论收束成唯一正式执行基线，而不把它误写成产品设计、运行时编排或客户端调用说明。

## 一、角色定位

`Task Contract` 属于 `Task Interface` 层。

它不是：

- `Memory Side` 组件
- 产品功能设计
- 后端服务模块
- 宿主运行时编排文档
- 客户端 `Skill / Agent` 的调用说明

当前仓库中，`Memory Side` 只包含：

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

`Task Contract` 的职责严格限定为：

- 从讨论中抽取已确认信息
- 压缩为唯一正式执行基线
- 明确目标、范围、非目标、验收、约束、依赖、风险、验证要求
- 对未确认内容显式标记为 `pending`

当前仓库还提供一个与模板并行的 skill 载体：

- `product/task-interface/skills/task-contract-skill/`

一句话定义：

> `Task Contract` 是 `discussion -> execution` 之间的唯一任务接口对象。

## 二、适用范围

适用于下面场景：

- 任务讨论已经基本收敛，但还没有进入执行
- 需要把目标、范围和验收边界压成稳定对象
- 需要为 `Context Routing`、执行层和 `Writeback & Cleanup` 提供统一上游输入

不适用于下面场景：

- 直接设计产品模块
- 直接写运行时编排方案
- 直接产出多步执行计划
- 直接作为客户端适配层规范

## 三、使用约束

- 只使用已确认讨论和主线文档事实
- 没有明确确认的内容，一律写为 `pending`
- 不把 `ideas / archive / 历史讨论` 直接提升为正式基线
- 不把 `Route Card` 或 `Writeback Card` 的字段混入 `Task Contract`
- 没有 `Task Contract` 时，不应直接进入执行

## 四、固定输出结构

每份 `Task Contract` 至少包含下面 5 个部分：

1. `Task Contract Role`
2. `Project Baseline`
3. `Current Task Contract`
4. `Open Decisions`
5. `Downstream Consumption`

其中 `Current Task Contract` 至少包含下面字段：

- `task`
- `goal`
- `non_goals`
- `in_scope`
- `out_of_scope`
- `acceptance_criteria`
- `constraints`
- `dependencies`
- `risks`
- `verification_requirements`

## 五、字段填写规则

### 1. `task`

- 用一句话说明当前任务要交付什么
- 只写本轮正式任务，不夹带背景叙事

### 2. `goal`

- 区分 `confirmed` 与 `pending`
- `confirmed` 只写已经拍板的目标
- `pending` 只写尚未最终确认、但会影响交付形态的点

### 3. `non_goals`

- 明确本轮不做什么
- 优先写最容易越界的内容

### 4. `in_scope` / `out_of_scope`

- 明确本轮允许进入和明确不进入的边界
- 如果仓库分层本身不是任务目标，不要把目录说明写成任务内容

### 5. `acceptance_criteria`

- 只写能判断“任务是否完成”的标准
- 不写实现步骤

### 6. `constraints`

- 写执行前就已经成立的硬限制
- 例如真相层、目录层级、禁止越界事项

### 7. `dependencies`

- 用 `confirmed` / `pending` 区分依赖状态
- 如果没有关键阻塞依赖，应明确写出

### 8. `risks`

- 只写真实存在的边界风险、消费风险和落地风险
- 不把泛泛而谈的担忧堆成风险列表

### 9. `verification_requirements`

- 明确如何判断内容与仓库主线一致
- 明确不能出现哪些越界行为

## 六、模板

```md
# Task Contract

## 1. Task Contract Role

[说明当前 Task Contract 的职责、边界和不属于什么。]

## 2. Project Baseline

[说明当前仓库事实基线、正式内容区和非真相层。]

## 3. Current Task Contract

### task

[一句话任务定义]

### goal

#### confirmed

- [...]

#### pending

- [...]

### non_goals

- [...]

### in_scope

- [...]

### out_of_scope

- [...]

### acceptance_criteria

- [...]

### constraints

- [...]

### dependencies

#### confirmed

- [...]

#### pending

- [...]

### risks

- [...]

### verification_requirements

- [...]

## 4. Open Decisions

### 已确定

- [...]

### 待最终拍板

1. [...]
2. [...]

## 5. Downstream Consumption

- Context Routing
  -> [Task Contract 如何作为 Route Card 的上游输入]

- 执行层
  -> [Task Contract 如何作为唯一正式执行基线]

- Writeback & Cleanup
  -> [Task Contract 如何作为收尾范围参照]

- Skills / Agents / 客户端
  -> [仅为消费层，不属于 Task Contract 本体]
```

## 七、当前仓库实例示例

下面示例对应一个 `docs-side contract task`，用于说明模板如何落地；它是实例，不替代模板本体。

```md
# Task Contract（示例）

## 1. Task Contract Role

`Task Contract` 属于 `Task Interface` 层的任务接口对象，不属于产品功能、运行时编排器、后端服务，也不属于 `Memory Side` 三组件本体。

## 2. Project Baseline

当前仓库是 AI coding 的 repo-side contract layer。
正式内容区只有：

- `product/`
- `docs/`
- `toolchain/`

`.agents/`、`.claude/`、`.opencode/`、`.autoworkflow/`、`.spec-workflow/`、`.serena/` 不属于正式内容区。

## 3. Current Task Contract

### task

为当前仓库在 `docs/` 真相层内补齐一份正式的 `Task Contract` 基线模板文档。

### goal

#### confirmed

- 形成仓库内可复用的 `Task Contract` 正式模板
- 明确 `Task Contract` 是 `discussion -> execution` 的任务接口对象
- 为 `Context Routing`、执行层和 `Writeback & Cleanup` 提供统一消费基线

#### pending

- 是否同步补齐其他成组模板

### non_goals

- 不进入 `product/` 业务实现
- 不进行运行时编排设计
- 不定义客户端调用方式

### in_scope

- 固化 `Task Contract` 的结构和字段
- 明确 `confirmed / pending` 的边界
- 说明与下游层的接口关系

### out_of_scope

- 运行时代码
- 客户端适配逻辑
- 基于猜测补全缺失事实

### acceptance_criteria

- 模板结构固定
- 字段集合完整
- 与主线文档一致
- 可被下游稳定消费

### constraints

- 只使用主线文档事实
- 未确认信息不得推断补全
- 不混入 `Route Card / Writeback Card`

### dependencies

#### confirmed

- `partition-model.md`
- `root-directory-layering.md`
- `path-governance-ai-routing.md`
- `memory-side/overview.md`

#### pending

- 无关键阻塞依赖

### risks

- 若误写成 runtime / service / agent，会破坏边界
- 若只做实例不做模板，会失去复用性

### verification_requirements

- 与 `docs/knowledge` 主线一致
- 明确区分 `confirmed / pending`
- 不出现编码、规划或 agent 分配内容

## 4. Open Decisions

### 已确定

- 任务类型是 `docs-side contract task`
- 交付物是 `Task Contract` 模板文档

### 待最终拍板

1. 是否同步补齐其他模板
2. 是否需要更多 repo-local 示例

## 5. Downstream Consumption

- Context Routing
  -> 基于 `Task Contract` 中已定稿目标和范围生成 `Route Card`

- 执行层
  -> 以 `Task Contract` 为唯一正式执行基线

- Writeback & Cleanup
  -> 以 `Task Contract` 作为收尾范围参照

- Skills / Agents / 客户端
  -> 只是消费层，不属于 `Task Contract` 本体
```

## 八、与下游层的关系

- `Context Routing` 使用 `Task Contract` 中已定稿的目标和范围来生成 `Route Card`
- 执行层使用 `Task Contract` 作为唯一正式执行基线
- `Writeback & Cleanup` 使用同一份 `Task Contract` 作为任务收尾时的范围参照
- 不同客户端的 `Skills / Agents` 只是消费 `Task Contract` 的调用层，不是 `Task Contract` 本体
- 不要把“哪个客户端如何调用”写成 `Task Contract` 的核心定义

## 九、相关文档

- [项目 Partition 模型](./partition-model.md)
- [Task Contract 基线](../task-interface/task-contract.md)
- [Task Contract Skill 骨架](../task-interface/skills/task-contract-skill.md)
- [根目录分层](./root-directory-layering.md)
- [路径治理与 AI 告知](./path-governance-ai-routing.md)
- [Memory Side 总览](../memory-side/overview.md)
- [Memory Side Skill 与 Agent 模型](../memory-side/skill-agent-model.md)
