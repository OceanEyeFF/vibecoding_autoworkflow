---
title: "项目 Partition 模型"
status: active
updated: 2026-03-19
owner: aw-kernel
last_verified: 2026-03-19
---
# 项目 Partition 模型

> 目标：先定义 Orchestrator 项目的职责分区，再反推目录、模板和运行时实现。

## 一、设计原则

- 先分职责边界，再分目录结构。
- 先定义谁持有真相，再定义谁消费真相。
- 长期记忆和单次任务闭环必须分层。
- 没有明确 owner 的信息，不应进入主线文档。

## 二、总览

| Partition | Side | 核心职责 | 持有的真相 |
|---|---|---|---|
| `Control Plane` | Flow Side | 持有阶段状态、推进流程、做裁决 | 当前 phase、任务状态、收尾判定 |
| `Knowledge Base` | Memory Side | 维护项目长期记忆 | 项目总览、模块入口、决策、变更、归档 |
| `Context Routing` | Memory Side | 决定任务开始前应读取哪些上下文 | 入口文档、代码入口、禁读范围 |
| `Task Contract` | Flow Side | 把讨论收束成正式执行基线 | 目标、范围、验收标准、约束、风险 |
| `Execution Runtime` | Flow Side | 执行具体任务和工具调用 | 本轮执行状态、工具结果、局部产物 |
| `Verification` | Flow Side | 审核证据与验收结果 | 白盒结果、黑盒结果、Gate 结论 |
| `Writeback & Cleanup` | Memory Side | 回写项目真相并清理失效上下文 | 变更摘要、风险、待办、清场记录 |

## 三、Side 划分

### Memory Side

- `Knowledge Base`
- `Context Routing`
- `Writeback & Cleanup`

职责：

- 维护长期真相
- 控制 AI 进入任务时读取什么
- 保证任务结束后真相被刷新

### Flow Side

- `Control Plane`
- `Task Contract`
- `Execution Runtime`
- `Verification`

职责：

- 管理单次任务闭环
- 约束执行过程
- 基于证据决定是否完成

## 四、各 Partition 边界

### 1. Control Plane

**职责**

- 定义当前任务所处阶段
- 决定何时进入执行、验证、收尾
- 接收验证反馈并裁决
- 维护任务级 shared state

**输入**

- 用户目标
- 当前任务状态
- Contract、Verification、Writeback 的反馈

**输出**

- 当前 phase
- 状态更新
- 下一步动作
- Done / Blocked / Continue 判定

**不拥有**

- 项目长期知识内容
- 执行细节实现
- 具体验证脚本逻辑

**禁止越界**

- 不能跳过 `Task Contract` 直接进入执行
- 不能用“对话印象”替代正式状态
- 不能把临时讨论直接写入长期记忆

### 2. Knowledge Base

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

### 3. Context Routing

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

### 4. Task Contract

**职责**

- 把模糊讨论压成唯一正式执行基线
- 定义目标、范围、验收标准和边界
- 记录风险、限制、依赖和验证要求

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
- 最终验收裁决

**禁止越界**

- 没有 Contract 不得进入执行
- Contract 不能只写目标，不写边界和验收
- Contract 不能把讨论碎片直接原样堆进去

### 5. Execution Runtime

**职责**

- 按 Contract 执行编码、分析、工具调用
- 管理 worker、CLI、模型和局部运行状态
- 产出代码、配置、局部说明等交付物

**输入**

- Task Contract
- Context Routing 指定的入口
- Control Plane 的阶段指令

**输出**

- 代码变更
- 工具调用结果
- 局部自测结果
- 执行说明

**不拥有**

- 项目长期真相
- 最终完成判定
- 独立的黑盒验收结论

**禁止越界**

- 不能自行修改 Contract 目标
- 不能拿旧记忆代替本轮证据
- 不能把“实现成功”直接当“任务完成”

### 6. Verification

**职责**

- 做白盒检查和黑盒验收
- 审查证据链
- 给出 Gate 结论和风险判断

**输入**

- Execution Runtime 产物
- Task Contract 验收标准
- 可执行测试和检查命令

**输出**

- 白盒结果
- 黑盒结果
- Gate 结论
- 风险和未覆盖项

**不拥有**

- 项目总览
- 最终文档回写
- 下一轮任务规划

**禁止越界**

- 不能只验证“实现者想验证的东西”
- 不能无证据宣告通过
- 不能跳过未覆盖项说明

### 7. Writeback & Cleanup

**职责**

- 把已验证结果写回长期记忆
- 更新变更日志、决策记录、待办和风险
- 清理失效 prompt、旧策略和伪事实

**输入**

- Verification 结果
- Execution Runtime 交付摘要
- 当前 Knowledge Base 入口

**输出**

- writeback 日志
- 更新后的主线文档
- 待办与风险记录
- 清场记录

**不拥有**

- 执行阶段控制权
- 验证判定权
- 需求讨论本体

**禁止越界**

- 未经验证结果不得回写为项目真相
- 不得保留已失效的 prompt 作为主线规则
- 不得只提交代码而跳过回写

## 五、Partition 之间的关系

主流程：

`Control Plane -> Task Contract -> Execution Runtime -> Verification -> Writeback & Cleanup`

辅助关系：

- `Knowledge Base -> Context Routing`：提供长期记忆和稳定入口
- `Context Routing -> Task Contract`：提供任务限读范围和入口
- `Writeback & Cleanup -> Knowledge Base`：刷新长期真相
- `Verification -> Control Plane`：提供是否可收尾的依据

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

- 再设计 `Control Plane` 的 shared state
- 再接 `Execution Runtime` 和 `Verification`

## 八、当前阶段不做什么

- 不先设计复杂 RAG
- 不先绑定某个单一后端或运行时框架
- 不先展开大而全的 Agent catalog
- 不把旧仓库结构直接继承成新架构

## 九、判断标准

当以下条件满足时，说明 Partition 规划成立：

- 能明确说出每类信息该写到哪里
- 能明确说出一个任务开始前该读什么
- 能明确说出没有哪些产物就不能进入执行
- 能明确说出代码完成后还缺哪些回写动作
- 旧文档和主线文档不会同时声称自己是真相源
