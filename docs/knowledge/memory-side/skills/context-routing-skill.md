---
title: "Context Routing Skill 骨架"
status: draft
updated: 2026-03-23
owner: aw-kernel
last_verified: 2026-03-23
---
# Context Routing Skill 骨架

> 目的：定义 `context-routing-skill` 的最小职责和输入输出，作为面向目标仓库的通用 skill contract。

## 一、Skill 名称

`context-routing-skill`

## 二、职责

- 根据任务类型生成最小 `Route Card`
- 指定文档入口、代码入口和禁读范围
- 控制任务开始前的阅读边界

## 三、触发场景

- 新任务进入执行前
- 用户目标较宽，需要先缩小阅读范围
- 需要为不同后端提供统一的任务入口

## 四、输入

- 优先使用 `Task Contract` 中已定稿的目标和范围；若尚无 Contract，再使用当前任务目标和范围
- 当前任务类型
- `Knowledge Base` 中可用的主线入口

## 五、输出

- 一张固定格式的 `Route Card`

最小字段包括：

- `task_type`
- `goal`
- `read_first`
- `read_next`
- `code_entry`
- `do_not_read_yet`
- `stop_reading_when`

## 六、主要读取入口

- [Memory Side 层级边界](../layer-boundary.md)
- [Context Routing 基线](../context-routing.md)
- [Context Routing 分流规则](../context-routing-rules.md)
- [Context Routing 输出格式](../formats/context-routing-output-format.md)
- [Context Routing 适配 Prompt 草案](../prompts/context-routing-adapter-prompt.md)

## 七、硬性约束

- 不默认全仓扫描
- 不把历史讨论全部塞入上下文
- 不把 `Archive` 当执行入口
- 不把 `Route Card` 写成执行计划

## 八、本文身份与本仓库中的落点

- 本文定义 `context-routing-skill` 的通用合同，不负责描述某个 repo-local wrapper。
- 当前仓库里的 canonical skill 实现在下面位置。

```text
product/memory-side/skills/context-routing-skill/
  SKILL.md
  references/
    entrypoints.md
```

当前实际入口：

- [context-routing-skill/SKILL.md](../../../../product/memory-side/skills/context-routing-skill/SKILL.md)
- [context-routing-skill/references/entrypoints.md](../../../../product/memory-side/skills/context-routing-skill/references/entrypoints.md)

## 九、建议接入方式

- 由 repo-local 任务入口模板或检查清单触发
- 由人工任务进入前的上下文整理动作触发
- 如果宿主执行层需要统一 caller，可自行命名，但不在本文固定 agent 名

## 十、判断标准

- Skill 能稳定输出结构一致的 `Route Card`
- Skill 能压缩上下文，而不是扩大上下文
- Skill 产物能直接支撑执行端开始工作
