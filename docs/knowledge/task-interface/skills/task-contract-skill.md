---
title: "Task Contract Skill 骨架"
status: draft
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Task Contract Skill 骨架

> 目的：定义 `task-contract-skill` 的最小职责、输入输出和边界，作为面向目标仓库的通用 `Task Interface` skill contract。

## 一、Skill 名称

`task-contract-skill`

## 二、职责

- 从已收敛讨论中提取已确认信息
- 产出固定结构的 `Task Contract`
- 明确 `confirmed / pending` 分界
- 在进入执行前收口任务边界

## 三、触发场景

- 任务讨论已经基本收敛
- 需要在执行前形成正式任务基线
- 需要让不同后端消费同一份任务对象

## 四、输入

- 当前任务讨论
- 当前仓库主线文档中的已确认事实
- 必要时读取最小 `Context Routing` 入口，但不替代 `Route Card`

## 五、输出

- 一份固定结构的 `Task Contract`

最小部分包括：

- `Task Contract Role`
- `Project Baseline`
- `Current Task Contract`
- `Open Decisions`
- `Downstream Consumption`

## 六、主要读取入口

- [根目录分层](../../foundations/root-directory-layering.md)
- [Task Contract 基线](../task-contract.md)
- [Task Contract 基线](../task-contract.md)

## 七、硬性约束

- 不推断未确认事实
- 不进入编码
- 不分配 agents
- 不输出多步执行计划
- 不把 repo 结构说明误写成任务本体
- 不把 `Task Contract` 并入 `Memory Side`

## 八、本文身份与本仓库中的落点

- 本文定义 `task-contract-skill` 的通用合同，不负责描述某个 repo-local wrapper。
- 当前仓库里的 canonical skill 实现在下面位置。

```text
product/task-interface/skills/task-contract-skill/
  SKILL.md
  references/
    entrypoints.md
```

当前实际入口：

- [task-contract-skill/SKILL.md](../../../../product/task-interface/skills/task-contract-skill/SKILL.md)
- [task-contract-skill/references/entrypoints.md](../../../../product/task-interface/skills/task-contract-skill/references/entrypoints.md)

## 九、建议接入方式

- 由用户在讨论收敛后显式调用
- 由宿主执行层在进入 `Context Routing` 前触发
- 如果宿主执行层需要统一 caller，可自行命名，但不在本文固定 agent 名

## 十、判断标准

- Skill 能稳定输出结构一致的 `Task Contract`
- Skill 能区分已确认与待确认内容
- Skill 产物可直接作为后续执行的正式输入
